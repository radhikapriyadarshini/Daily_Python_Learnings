#  Power System Unit Commitment (UC) — DevOps-ready

## Overview

This repository contains a Python-based implementation of **Unit Commitment (UC)** for power system operations, with an emphasis on reproducible engineering workflows and DevOps best practices for deployment, testing, and CI/CD.

Unit Commitment decides which generation units to turn ON/OFF and how much they should produce over a time horizon (typically 24 hours, sometimes longer) to meet demand at minimum cost while satisfying electrical and operational constraints. This README explains UC theory, how the Python implementation is structured, and how to operate and deploy the project in an engineering team setting.

---

# 1. Unit Commitment — Power system explanation (detailed)

## 1.1 Purpose

UC schedules generating units to:

* meet demand (load) and reserve requirements,
* minimize total system cost (fuel + startup/shutdown + no-load costs),
* respect unit technical limits and system constraints,
* optionally provide security / reserve and ramping services.

## 1.2 Typical time horizon and granularity

* Horizon: 24 hours (commonly) or 48+ hours for planning.
* Granularity: hourly is standard; sub-hourly (15/5 min) for higher-fidelity studies.

## 1.3 Decision variables

* Binary ON/OFF: $u_{g,t} \in \{0,1\}$ — whether unit $g$ is committed at time $t$.
* Startup $s_{g,t} \in \{0,1\}$: indicates a start-up event.
* Shutdown $z_{g,t} \in \{0,1\}$: indicates a shutdown event.
* Dispatch (continuous) $p_{g,t} \ge 0$: power output of unit $g$ at time $t$.
* Sometimes reserves $r_{g,t}$, ramp-use variables.

## 1.4 Objective function (typical)

Minimize:

$$
\sum_{t}\sum_{g}\Big(C^{\text{fuel}}_{g}(p_{g,t}) + C^{\text{no-load}}_g u_{g,t} + C^{\text{startup}}_g s_{g,t} + C^{\text{shutdown}}_g z_{g,t}\Big)
$$

Fuel cost often approximated piecewise-linear or quadratic (linearized in MILP).

## 1.5 Key constraints

* **Power balance** (per time step): $\sum_g p_{g,t} = D_t + Losses_t$ (plus exports/imports)
* **Capacity bounds**: $u_{g,t} \cdot P_{g}^{\min} \le p_{g,t} \le u_{g,t} \cdot P_g^{\max}$
* **Ramp up / down**: $p_{g,t} - p_{g,t-1} \le RU_g$ etc.
* **Minimum up / down time**: handled via linking constraints over multiple periods.
* **Reserve requirement**: $\sum_g r_{g,t} \ge R_t$
* **Network constraints (optional)**: DC power flow or AC approximations for security-constrained UC.
* **Start/shutdown linking**: $s_{g,t} - z_{g,t} = u_{g,t} - u_{g,t-1}$

## 1.6 Outputs

* Commitment schedule $u_{g,t}$
* Dispatch schedule $p_{g,t}$
* Marginal prices (LMPs) if you solve LP re-solve (dual variables on power-balance)
* Commitment costs, startup/shutdown counts, reserve provision
* Feasibility / infeasibility diagnostics

---

# 2. Python implementation guidance (Pyomo + solver notes)

This project uses Python and Pyomo for modeling (but the structure below is framework-agnostic).

## 2.1 Structure (recommended)

```
/ (repo root)
├─ README.md
├─ pyproject.toml or requirements.txt
├─ src/
│  ├─ uc/
│  │  ├─ __init__.py
│  │  ├─ model.py           # UC Pyomo model builder
│  │  ├─ solve_uc.py        # solver orchestration (solve + LP-re-solve for duals)
│  │  ├─ data.py            # input parsers (csv, json)
│  │  └─ utils.py
├─ examples/
│  ├─ run_uc_example.py
│  └─ sample_input.csv
├─ tests/
│  ├─ test_model_build.py
│  └─ test_solve.py
├─ docker/
│  ├─ Dockerfile
│  └─ docker-compose.yml
└─ ci/
   └─ github-actions.yml
```

## 2.2 Solver recommendations

* **CBC**: robust open-source MILP solver — good for MIP and LP. (We favor `cbc` CLI for MILP.)
* **GLPK**: fallback open-source solver (`glpsol`) — okay for LP/MIP but slower.
* **HiGHS**: fast, but historically Pyomo + HiGHS may return invalid duals for some LP re-solves — if you need LMPs, verify duals carefully.
* Commercial alternatives: Gurobi, CPLEX (recommended for production speed & reliability).

### Installing solvers (Windows / Linux)

* Prefer conda packages if available: `conda install -c conda-forge coincbc glpk` (if you use conda).
* Or download official binaries and add to PATH.
* Ensure the solver CLI is on PATH so `pyomo.environ.SolverFactory('cbc')` finds it.

## 2.3 Example: build (minimal) UC in Pyomo

```python
from pyomo.environ import ConcreteModel, Var, NonNegativeReals, Binary, Objective, Constraint, SolverFactory, RangeSet, summation

def build_uc_model(units, horizon, demand):
    model = ConcreteModel()
    model.T = RangeSet(0, horizon-1)
    model.G = RangeSet(0, len(units)-1)

    # Parameters arrays here: Pmin[g], Pmax[g], cost[g] etc.
    Pmin = {i: units[i]['Pmin'] for i in model.G}
    Pmax = {i: units[i]['Pmax'] for i in model.G}
    cost = {i: units[i]['a'] for i in model.G}  # linear cost coefficient

    model.u = Var(model.G, model.T, domain=Binary)               # ON/OFF
    model.p = Var(model.G, model.T, domain=NonNegativeReals)    # dispatch (MW)

    # capacity
    def cap_lower(m,g,t): return m.p[g,t] >= Pmin[g]*m.u[g,t]
    def cap_upper(m,g,t): return m.p[g,t] <= Pmax[g]*m.u[g,t]
    model.cap_min = Constraint(model.G, model.T, rule=cap_lower)
    model.cap_max = Constraint(model.G, model.T, rule=cap_upper)

    # demand balance
    def power_balance(m,t):
        return sum(m.p[g,t] for g in m.G) == demand[t]
    model.balance = Constraint(model.T, rule=power_balance)

    # objective: linear fuel cost + no-load (example)
    def obj_rule(m):
        fuel = sum(cost[g]*m.p[g,t] for g in m.G for t in m.T)
        no_load = 0.0
        return fuel + no_load
    model.obj = Objective(rule=obj_rule, sense=1)  # minimize
    return model

# solve
model = build_uc_model(units, horizon=24, demand=[...])
solver = SolverFactory('cbc')
results = solver.solve(model, tee=True)
```

## 2.4 LP re-solve to obtain duals (LMPs)

1. Fix commitment binaries to the solved integer values.
2. Solve the resulting **LP** (continuous) model — get valid duals on power balance constraints.
3. Extract `.dual[model.balance[t]]` for each t (requires a solver that returns duals).

Example sketch:

```python
from pyomo.environ import value

# after MILP solve, extract commitments
u_sol = {(g,t): round(value(model.u[g,t])) for g in model.G for t in model.T}

# fix binaries
for (g,t), val in u_sol.items():
    model.u[g,t].fix(val)

# solve LP
lp_solver = SolverFactory('cbc')   # or glpk; must support duals. (cbc returns duals for LP)
lp_results = lp_solver.solve(model, tee=True)
# access duals (Pyomo needs the 'suffix' to be loaded; solver should return duals)
from pyomo.environ import Suffix
model.dual = Suffix(direction=Suffix.IMPORT)
# then after solve, model.dual[model.balance[t]] holds LMP at time t
```

> Note: Pyomo duals require the solver to return dual information and Pyomo to import it via `Suffix`. Some solver/pyomo combinations need extra setup — test locally.

---

# 3. DevOps & Reproducibility

## 3.1 Environment and dependencies

* Use `pyproject.toml` or `requirements.txt` and pin versions for reproducibility.
* Provide `environment.yml` for conda users.
* Provide a `venv` friendly `setup.sh` for Linux/macOS and `setup.ps1` for Windows to bootstrap virtualenv and pip install.

Example `requirements.txt`:

```
pyomo==6.5.0
pandas==2.1.0
numpy==1.26.0
pytest==7.3.1
```

## 3.2 Docker (recommended for reproducible solver environment)

Dockerfile (minimal):

```dockerfile
FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y wget unzip && \
    apt-get clean

# Install Python deps
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install CBC (example via coinor)
RUN wget -q https://github.com/coin-or/Cbc/releases/download/version/Cbc-2.10.12-Linux.tar.gz \
    && tar -xzf Cbc-2.10.12-Linux.tar.gz -C /opt && ln -s /opt/Cbc/bin/cbc /usr/local/bin/cbc

WORKDIR /app
COPY src /app/src
COPY examples /app/examples

CMD ["python", "examples/run_uc_example.py"]
```

(Adjust URLs and versions as required; some platforms require custom installation.)

## 3.3 CI/CD (example GitHub Actions)

* Run unit tests
* Run model building static checks (lint)
* Run small/fast instance solves (sanity tests) with a free solver (GLPK or a mocked solver)
* On release, build Docker image and push to registry

Example `ci.yml` workflow steps:

1. Set up Python
2. Install requirements
3. Run `pytest -q`
4. Run `python examples/run_uc_example.py --smoke-test`

## 3.4 Testing strategy

* **Unit tests**: model building, constraint counts, parameter parsing
* **Integration tests**: small UC cases (2–3 units) with expected outputs
* **Performance tests**: timed solves (not in CI, but nightly)
* **Regression tests**: compare costs & schedules for benchmark cases (store golden outputs)

## 3.5 Logging & observability

* Use structured logging (Python `logging` with JSON formatter for pipeline).
* Log solver name, solver output summary, objective value, termination condition, runtime, nodes explored.
* Save solver log to artifacts in CI runs for debugging.

## 3.6 Secrets & configuration

* Keep secrets (API keys, credentials) out of repo — use GitHub Secrets or vault.
* Use `config/*.yaml` to manage scenario configurations (demand file paths, solver choices).

---

# 4. How to run locally (quick start)

1. Create venv and install:

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Ensure `cbc` is on PATH (or your chosen solver). Test:

```bash
cbc --version
glpsol --version
```

3. Run example:

```bash
python examples/run_uc_example.py
# or to force solver: python examples/run_uc_example.py --solver cbc
```

4. If you want LMPs (dual values):

* Make sure you have an LP-capable solver that returns duals.
* Use the `--get-lmps` flag (if implemented) to do the MILP->fix binaries->LP re-solve flow.

---

# 5. Troubleshooting & common pitfalls

* **No solver found**: check PATH and test `cbc --version`. Check that `pyomo` finds solver via `SolverFactory('cbc')`.
* **Solver runs MIP but LP re-solve returns invalid duals**: try a different solver (CBC or GLPK) for the LP re-solve. HiGHS has been reported to give invalid duals in some setups.
* **Infeasible model**: check constraint bounds, initial conditions, min up/down times, reserve requirement. Add `Constraint.Skip` debug prints or relax constraints for debugging.
* **Slow solves**: reduce horizon or relax discrete choices for testing; profile; consider commercial solvers for production.
* **No duals imported**: ensure you created `model.dual = Suffix(direction=Suffix.IMPORT)` before solve, and solver supports exporting duals.

---

# 6. Best practices for production UC pipelines

* **Benchmarking**: maintain a set of benchmark cases and record solver times & objective values.
* **Model versioning**: tag model changes (e.g., changes to cost curves, ramp limits) and store test results for each version.
* **Reproducibility**: use Docker images in CI, pin solver versions.
* **Monitoring**: if scheduling in real-time, build alerting for when solves exceed expected timelines or when infeasible.
* **Data validation**: add schema checks for inputs (demand, unit params) and automated sanity checks in CI.
* **Human-in-the-loop**: provide explainability artifacts — startup counts, marginal units, shadow prices — for operators.

