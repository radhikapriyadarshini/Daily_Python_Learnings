import numpy as np

def dc_load_flow(n_buses, slack, lines, Pinj):
    """
    lines: list of (from, to, X_pu, rate_MW)
    Pinj: bus net injections (gen - load) in MW on system base (assumed = 1.0 per simplicity)
    """
    B = np.zeros((n_buses, n_buses), dtype=float)
    for f,t,X,_ in lines:
        b = -1.0/X
        B[f,f] -= b
        B[t,t] -= b
        B[f,t] += b
        B[t,f] += b
    # Reduce system by removing slack bus
    idx = [i for i in range(n_buses) if i != slack]
    Bred = B[np.ix_(idx, idx)]
    Pred = np.array([Pinj[i] for i in idx], dtype=float)
    theta = np.zeros(n_buses)
    theta[idx] = np.linalg.solve(Bred, Pred)
    # Line flows F = (θf - θt)/X
    flows = []
    for f,t,X,rate in lines:
        F = (theta[f]-theta[t])/X  # pu on system base -> MW if base=1 pu = system MVA
        flows.append({"from":f,"to":t,"MW":F,"rate":rate,"pct":100*abs(F)/rate if rate>0 else np.nan})
    return theta, flows

# Demo 4-bus
lines = [
    (0,1,0.2, 200), (1,2,0.25, 150), (2,3,0.2, 200), (0,3,0.4, 100), (1,3,0.3, 120)
]
Pinj = [150, -50, -60, -40]  # MW, sum≈0
theta, flows = dc_load_flow(4, slack=0, lines=lines, Pinj=Pinj)
print("Bus angles (rad):", np.round(theta,4))
for f in flows: print(f)
