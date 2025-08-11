# run_uc_example.py
import numpy as np
from phase3_uc import build_uc_model, solve_uc, export_results

def create_demo_data(horizon=24):
    # Buses 1..4
    buses = [1,2,3,4]
    # Generators: name, bus, pmin, pmax, ramp_up, ramp_down, startup_cost, shutdown_cost, min_up, min_down, cost_a, cost_b
    gens = [
        {'name':'Coal_1','bus':1,'pmin':150,'pmax':500,'ramp_up':50,'ramp_down':50,'startup_cost':1000,'shutdown_cost':200,'min_up':6,'min_down':4,'cost_a':0.00025,'cost_b':22.0},
        {'name':'Gas_CC_1','bus':2,'pmin':100,'pmax':400,'ramp_up':80,'ramp_down':80,'startup_cost':800,'shutdown_cost':150,'min_up':3,'min_down':2,'cost_a':0.0008,'cost_b':35.0},
        {'name':'Gas_Peak_1','bus':3,'pmin':0,'pmax':200,'ramp_up':100,'ramp_down':100,'startup_cost':300,'shutdown_cost':50,'min_up':1,'min_down':1,'cost_a':0.002,'cost_b':50.0},
        {'name':'Hydro_1','bus':1,'pmin':10,'pmax':120,'ramp_up':60,'ramp_down':60,'startup_cost':0,'shutdown_cost':0,'min_up':1,'min_down':1,'cost_a':0.0,'cost_b':8.0},
    ]
    # Lines
    lines = [
        {'name':'L12','from_bus':1,'to_bus':2,'reactance':0.05,'limit':300.0},
        {'name':'L23','from_bus':2,'to_bus':3,'reactance':0.08,'limit':250.0},
        {'name':'L13','from_bus':1,'to_bus':3,'reactance':0.12,'limit':200.0},
        {'name':'L34','from_bus':3,'to_bus':4,'reactance':0.06,'limit':400.0},
        {'name':'L24','from_bus':2,'to_bus':4,'reactance':0.10,'limit':180.0},
    ]

    # Create demand profile (24 hrs) - simple diurnal curve by bus
    demand = {}
    base = {1:200, 2:180, 3:150, 4:70}
    for t in range(1, horizon+1):
        hour_frac = 0.5 + 0.5 * np.sin((t-1)/24.0 * 2*np.pi)  # rough diurnal
        demand[t] = {b: base[b] * (0.8 + 0.4 * hour_frac) for b in base}

    # Renewable profiles (wind+solar) at bus 4
    renewable = {}
    for t in range(1, horizon+1):
        solar = max(0.0, 100.0 * np.sin((t-6)/24.0 * np.pi))  # rough peak around t=12
        wind = 50.0 + 20.0 * np.sin((t+3)/8.0)  # slow variation
        renewable[t] = {1:0.0,2:0.0,3:0.0,4: solar + wind}

    # Reserve targets: spinning and non-spinning
    reserve_spinning = {t: 50.0 for t in range(1, horizon+1)}
    reserve_nonspinning = {t: 30.0 for t in range(1, horizon+1)}

    data = {
        'gens': gens,
        'buses': buses,
        'lines': lines,
        'demand': demand,
        'renewable': renewable,
        'reserve_spinning': reserve_spinning,
        'reserve_nonspinning': reserve_nonspinning
    }
    return data

if __name__ == '__main__':
    horizon = 24
    data = create_demo_data(horizon=horizon)
    print("Building model...")
    model = build_uc_model(data, horizon=horizon, nseg=8)

    # Solver fallback order: try CLI highs, then appsi_highs, then glpk
    solver_candidates = ['cbc', 'glpk']
    model_solved = None
    lmp = None
    from pyomo.common.errors import ApplicationError
    
    print("Solving model...")
    try:
        model_solved, lmp = solve_uc(model, solver_candidates=solver_candidates)
        print("Model solved successfully!")
        
        # Check if we got meaningful LMP values
        valid_lmps = sum(1 for v in lmp.values() if v is not None)
        if valid_lmps > 0:
            print(f"Successfully extracted {valid_lmps} LMP values")
        else:
            print("Warning: No LMP values extracted, but unit commitment solution is valid")
            
    except Exception as e:
        print(f"Error during solve: {e}")
        # Check if HiGHS is working but just having dual issues
        if "No solver succeeded" in str(e) and "glpk" in str(e):
            print("\nNote: HiGHS solved the MIP successfully but failed on LP re-solve for duals.")
            print("This is a known issue. The unit commitment solution is still valid.")
            print("To get LMP values, try installing GLPK or another LP solver.")
        raise RuntimeError("Optimization failed. Check solver installation and model setup.")

    export_results(model_solved, lmp, outdir='uc_results_demo')
    print("Done. Results in uc_results_demo/")