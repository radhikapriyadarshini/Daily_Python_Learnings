# phase3_uc.py
"""
HiGHS-safe optimized Phase 3 Unit Commitment Pyomo model.

Features:
- Piecewise-linear costs (midpoint linearization of provided quadratic)
- DC power flow (theta / flow)
- Spinning and non-spinning reserves
- Min-up / min-down, ramp limits, startup/shutdown indicators
- Two-stage solve: MILP -> fix binaries -> LP to extract LMPs
- Solver fallback: appsi_highs -> highs -> glpk
"""

from pyomo.environ import (
    ConcreteModel, Set, Param, Var, Binary, NonNegativeReals, Reals,
    Constraint, Objective, SolverFactory, minimize, Suffix, value
)
import numpy as np
import pandas as pd
import os
from pyomo.common.errors import ApplicationError

# -----------------------
# Helpers
# -----------------------
def piecewise_segments(pmin, pmax, nseg=6):
    if pmax <= pmin:
        return [(pmin, pmax)]
    pts = np.linspace(pmin, pmax, nseg + 1)
    return [(float(pts[i]), float(pts[i+1])) for i in range(len(pts)-1)]

# -----------------------
# Model builder
# -----------------------
def build_uc_model(data, horizon=24, nseg=6):
    T = list(range(1, horizon+1))
    model = ConcreteModel()
    model.T = Set(initialize=T)

    # Sets
    G = [g['name'] for g in data['gens']]
    model.G = Set(initialize=G)
    buses = sorted(data.get('buses', []))
    model.B = Set(initialize=buses)
    L = [l['name'] for l in data.get('lines', [])]
    model.L = Set(initialize=L)

    # Scalar params
    pmin = {g['name']: g.get('pmin', 0.0) for g in data['gens']}
    pmax = {g['name']: g.get('pmax', 0.0) for g in data['gens']}
    ramp_up = {g['name']: g.get('ramp_up', pmax[g['name']]) for g in data['gens']}
    ramp_down = {g['name']: g.get('ramp_down', pmax[g['name']]) for g in data['gens']}
    startup = {g['name']: g.get('startup_cost', 0.0) for g in data['gens']}
    shutdown = {g['name']: g.get('shutdown_cost', 0.0) for g in data['gens']}
    min_up = {g['name']: int(g.get('min_up', 1)) for g in data['gens']}
    min_down = {g['name']: int(g.get('min_down', 1)) for g in data['gens']}
    gen_bus = {g['name']: g['bus'] for g in data['gens']}

    # Piecewise segments
    seg_bounds = {}
    seg_cost = {}
    for g in data['gens']:
        name = g['name']
        a = g.get('cost_a', None)
        b = g.get('cost_b', None)
        segs = piecewise_segments(pmin[name], pmax[name], nseg)
        seg_bounds[name] = segs
        mcosts = []
        for lo, hi in segs:
            mid = 0.5*(lo+hi)
            if a is not None and b is not None:
                mc = 2.0*a*mid + b
            elif b is not None:
                mc = b
            else:
                mc = 0.0
            mcosts.append(float(mc))
        seg_cost[name] = mcosts

    # Time-series inputs (demand, renewables, reserves)
    demand_ts = data['demand']
    ren_ts = data.get('renewable', {t: {b: 0.0 for b in buses} for t in T})
    rs = data.get('reserve_spinning', {t: 0.0 for t in T})
    rns = data.get('reserve_nonspinning', {t: 0.0 for t in T})

    # Line params
    line_from = {l['name']: l['from_bus'] for l in data.get('lines', [])}
    line_to = {l['name']: l['to_bus'] for l in data.get('lines', [])}
    line_x = {l['name']: l['reactance'] for l in data.get('lines', [])}
    line_limit = {l['name']: l['limit'] for l in data.get('lines', [])}

    # Attach scalar params
    model.pmin = Param(model.G, initialize=pmin)
    model.pmax = Param(model.G, initialize=pmax)
    model.ramp_up = Param(model.G, initialize=ramp_up)
    model.ramp_down = Param(model.G, initialize=ramp_down)
    model.startup = Param(model.G, initialize=startup)
    model.shutdown = Param(model.G, initialize=shutdown)
    model.min_up = Param(model.G, initialize=min_up)
    model.min_down = Param(model.G, initialize=min_down)
    model.gen_bus = Param(model.G, initialize=gen_bus, within=model.B)

    model.line_from = Param(model.L, initialize=line_from)
    model.line_to = Param(model.L, initialize=line_to)
    model.line_x = Param(model.L, initialize=line_x)
    model.line_limit = Param(model.L, initialize=line_limit)

    # Indexed segment sets and flattened indices for Pyomo
    model.S = Set(model.G, initialize=lambda m, g: list(range(len(seg_bounds[g]))))
    seg_index = [(g, s) for g in G for s in range(len(seg_bounds[g]))]
    model.GS = Set(dimen=2, initialize=seg_index)
    gst_index = [(g, s, t) for g, s in seg_index for t in T]
    model.GST = Set(dimen=3, initialize=gst_index)

    seg_lo = {(g, s): seg_bounds[g][s][0] for g, s in seg_index}
    seg_hi = {(g, s): seg_bounds[g][s][1] for g, s in seg_index}
    seg_mc = {(g, s): seg_cost[g][s] for g, s in seg_index}
    model.seg_lo = Param(model.GS, initialize=seg_lo)
    model.seg_hi = Param(model.GS, initialize=seg_hi)
    model.seg_mc = Param(model.GS, initialize=seg_mc)

    # Variables
    model.u = Var(model.G, model.T, domain=Binary)
    model.v = Var(model.G, model.T, domain=Binary)
    model.w = Var(model.G, model.T, domain=Binary)
    model.p = Var(model.G, model.T, domain=NonNegativeReals)
    model.p_seg = Var(model.GST, domain=NonNegativeReals)
    model.theta = Var(model.B, model.T, domain=Reals)
    model.flow = Var(model.L, model.T, domain=Reals)
    model.r_sp = Var(model.G, model.T, domain=NonNegativeReals)
    model.r_ns = Var(model.G, model.T, domain=NonNegativeReals)

    # Constraints:
    # p equals sum of segments
    def seg_sum_rule(m, g, t):
        return m.p[g, t] == sum(m.p_seg[g, s, t] for s in m.S[g])
    model.seg_sum = Constraint(model.G, model.T, rule=seg_sum_rule)

    # segment width bounds (constants on RHS)
    def seg_bounds_rule(m, g, s, t):
        return m.p_seg[g, s, t] <= (m.seg_hi[g, s] - m.seg_lo[g, s])
    model.seg_bounds_cons = Constraint(model.GST, rule=seg_bounds_rule)

    # generator lower/upper bounds (split)
    model.gen_lb = Constraint(model.G, model.T, rule=lambda m, g, t: m.p[g, t] - m.pmin[g]*m.u[g, t] >= 0.0)
    model.gen_ub = Constraint(model.G, model.T, rule=lambda m, g, t: m.p[g, t] - m.pmax[g]*m.u[g, t] <= 0.0)

    # segment commit
    model.seg_commit = Constraint(model.G, model.T, rule=lambda m, g, t: sum(m.p_seg[g, s, t] for s in m.S[g]) - m.pmax[g]*m.u[g, t] <= 0.0)

    # Ramp constraints: move all variable terms to LHS, constants RHS
    # Apply only for t >= 2
    T_after1 = [t for t in T if t >= 2]
    model.T_after1 = Set(initialize=T_after1)
    model.ramp_up_cons = Constraint(model.G, model.T_after1, rule=lambda m, g, t: m.p[g, t] - m.p[g, t-1] - m.ramp_up[g] <= 0.0)
    model.ramp_down_cons = Constraint(model.G, model.T_after1, rule=lambda m, g, t: m.p[g, t-1] - m.p[g, t] - m.ramp_down[g] <= 0.0)

    # startup/shutdown linking (variables on both sides but bounds are inequality form acceptable)
    model.start_link = Constraint(model.G, model.T,
                                 rule=lambda m, g, t: m.v[g, t] - m.u[g, t] + (0 if t==1 else m.u[g, t-1]) >= 0.0)
    model.shut_link = Constraint(model.G, model.T,
                                 rule=lambda m, g, t: m.w[g, t] - (0 if t==1 else m.u[g, t-1]) + m.u[g, t] >= 0.0)

    # min-up/min-down: precompute valid indices to avoid Skip
    min_up_idx = []
    min_down_idx = []
    for g in G:
        mu = int(min_up[g])
        md = int(min_down[g])
        if mu > 1:
            for t in range(1, horizon - mu + 2):
                min_up_idx.append((g, t))
        if md > 1:
            for t in range(1, horizon - md + 2):
                min_down_idx.append((g, t))
    model.MINUP = Set(dimen=2, initialize=min_up_idx)
    model.MINDOWN = Set(dimen=2, initialize=min_down_idx)
    def min_up_rule(m, g, t):
        mu = int(m.min_up[g])
        return sum(m.v[g, k] for k in range(t, t+mu)) - m.u[g, t+mu-1] <= 0.0
    model.min_up_cons = Constraint(model.MINUP, rule=min_up_rule)
    def min_down_rule(m, g, t):
        md = int(m.min_down[g])
        return sum(m.w[g, k] for k in range(t, t+md)) + m.u[g, t+md-1] <= 1.0
    model.min_down_cons = Constraint(model.MINDOWN, rule=min_down_rule)

    # Nodal balance: move all variables to LHS and constant RHS
    def nodal_balance(m, b, t):
        gen_inj = sum(m.p[g, t] for g in m.G if int(m.gen_bus[g]) == int(b))
        inflow = sum(m.flow[l, t] for l in m.L if int(m.line_to[l]) == int(b))
        outflow = sum(m.flow[l, t] for l in m.L if int(m.line_from[l]) == int(b))
        rhs = demand_ts.get(t, {}).get(b, 0.0) - ren_ts.get(t, {}).get(b, 0.0)
        # gen + inflow - outflow - rhs == 0 -> gen + inflow - outflow - rhs = 0
        return gen_inj + inflow - outflow - rhs == 0.0
    model.balance = Constraint(model.B, model.T, rule=nodal_balance)

    # DC flow (lhs variable, rhs expression with only params and theta)
    def dc_flow(m, l, t):
        x = float(m.line_x[l])
        if x > 0:
            return m.flow[l, t] - (m.theta[m.line_from[l], t] - m.theta[m.line_to[l], t]) / x == 0.0
        else:
            return m.flow[l, t] == 0.0
    model.dc_flow = Constraint(model.L, model.T, rule=dc_flow)

    # reference bus angle
    if buses:
        ref_bus = buses[0]
        model.ref = Constraint(model.T, rule=lambda m, t: m.theta[ref_bus, t] == 0.0)

    # line limits split into two inequalities (constant RHS)
    model.line_pos = Constraint(model.L, model.T, rule=lambda m, l, t: m.flow[l, t] - m.line_limit[l] <= 0.0)
    model.line_neg = Constraint(model.L, model.T, rule=lambda m, l, t: -m.flow[l, t] - m.line_limit[l] <= 0.0)

    # Reserve constraints: move everything to LHS with constant RHS
    # spinning reserve availability: sum(Pmax*u - p) >= req -> sum(Pmax*u - p) - req >=0
    model.spin_avail = Constraint(model.T, rule=lambda m, t: sum(m.pmax[g]*m.u[g, t] - m.p[g, t] for g in m.G) - rs.get(t, 0.0) >= 0.0)
    # explicit spinning req via r_sp variables: sum(r_sp) - req >= 0
    model.spin_req = Constraint(model.T, rule=lambda m, t: sum(m.r_sp[g, t] for g in m.G) - rs.get(t, 0.0) >= 0.0)
    # non-spinning requirement
    model.ns_req = Constraint(model.T, rule=lambda m, t: sum(m.r_ns[g, t] for g in m.G) - rns.get(t, 0.0) >= 0.0)

    # reserve per-gen bounds (all variable terms kept LHS)
    model.r_sp_bound = Constraint(model.G, model.T, rule=lambda m, g, t: m.r_sp[g, t] - (m.pmax[g] - m.p[g, t]) <= 0.0)
    model.r_ns_bound = Constraint(model.G, model.T, rule=lambda m, g, t: m.r_ns[g, t] - (m.pmax[g]*(1 - m.u[g, t]) + (m.pmax[g] - m.p[g, t])) <= 0.0)

    # Objective: piecewise linear segments + start/shut costs
    def obj_rule(m):
        fuel = sum(m.seg_mc[g, s] * m.p_seg[g, s, t] for g, s, t in m.GST)
        start = sum(m.startup[g] * m.v[g, t] for g in m.G for t in m.T)
        shut = sum(m.shutdown[g] * m.w[g, t] for g in m.G for t in m.T)
        return fuel + start + shut
    model.obj = Objective(rule=obj_rule, sense=minimize)

    return model

# -----------------------
# Solver wrapper
# -----------------------
def solve_uc(model, solver_candidates=None, solver_name=None, time_limit=None):
    """
    Try solver candidates in order (default tries appsi_highs, highs CLI, glpk).
    After MILP, fix binary variables and re-solve LP to get duals (LMPs).
    """
    if solver_name is not None:
        # If specific solver requested, use it
        solver_candidates = [solver_name]
    elif solver_candidates is None:
        solver_candidates = ['cbc', 'glpk']

    # attach dual suffix (import) for LP duals later
    model.dual = Suffix(direction=Suffix.IMPORT)

    last_exc = None
    for solver_name in solver_candidates:
        try:
            opt = SolverFactory(solver_name)
            if time_limit is not None:
                try:
                    opt.options['time_limit'] = time_limit
                except Exception:
                    pass
            print("Attempting solver:", solver_name)
            res = opt.solve(model, tee=True)
            print("Solver returned:", solver_name, res.solver.status, res.solver.termination_condition)
            used_solver = solver_name
            break
        except ApplicationError as ex:
            print(f"Solver {solver_name} not available or failed: {ex}")
            last_exc = ex
        except Exception as ex:
            print(f"Solver {solver_name} error: {ex}")
            last_exc = ex
    else:
        raise RuntimeError("No solver succeeded. Last error: {}".format(last_exc))

    # fix binary decisions
    for g in model.G:
        for t in model.T:
            val_u = int(round(value(model.u[g, t])))
            model.u[g, t].fix(val_u)
            # fix indicators too
            model.v[g, t].fix(int(round(value(model.v[g, t]))))
            model.w[g, t].fix(int(round(value(model.w[g, t]))))

    # re-solve LP (same solver should handle continuous solve)
    try:
        opt = SolverFactory(used_solver)
        print("Re-solving LP with solver:", used_solver)
        res2 = opt.solve(model, tee=True)
    except Exception as ex:
        print("LP re-solve failed with solver {}: {}".format(used_solver, ex))
        # try fallback to glpk if not tried yet
        if used_solver != 'glpk':
            try:
                opt = SolverFactory('glpk')
                print("Attempting LP re-solve with glpk")
                res2 = opt.solve(model, tee=True)
                used_solver = 'glpk'
            except Exception as ex2:
                raise RuntimeError("LP re-solve failed on both {} and glpk: {}, {}".format(used_solver, ex, ex2))
        else:
            raise

    # extract LMPs from duals of balance constraints
    lmp = {}
    for b in model.B:
        for t in model.T:
            con = model.balance[b, t]
            dualval = model.dual.get(con, None)
            lmp[(b, t)] = float(dualval) if dualval is not None else None

    return model, lmp

# -----------------------
# Export helper
# -----------------------
def export_results(model, lmp, outdir='uc_results'):
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for g in model.G:
        for t in model.T:
            rows.append({
                'gen': g, 'time': t, 'u': int(value(model.u[g, t])),
                'p': float(value(model.p[g, t])),
                'v': int(value(model.v[g, t])), 'w': int(value(model.w[g, t]))
            })
    pd.DataFrame(rows).to_csv(os.path.join(outdir, 'unit_schedules.csv'), index=False)

    lmp_rows = [{'bus': b, 'time': t, 'lmp': lmp.get((b, t), None)} for b in model.B for t in model.T]
    pd.DataFrame(lmp_rows).to_csv(os.path.join(outdir, 'lmps.csv'), index=False)
    print(f"Exported results to {outdir}")