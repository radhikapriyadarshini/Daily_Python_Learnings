import numpy as np

def dc_pf(n_buses, slack, lines, Pinj):
    B = np.zeros((n_buses, n_buses), dtype=float)
    for f,t,X,_ in lines:
        b = -1.0/X
        B[f,f] -= b; B[t,t] -= b
        B[f,t] += b; B[t,f] += b
    idx = [i for i in range(n_buses) if i != slack]
    Bred = B[np.ix_(idx, idx)]
    Pred = np.array([Pinj[i] for i in idx], dtype=float)
    theta = np.zeros(n_buses); theta[idx] = np.linalg.solve(Bred, Pred)
    flows=[]
    for f,t,X,rate in lines:
        F=(theta[f]-theta[t])/X
        flows.append((f,t,F,rate))
    return theta, flows

def n_1_screen(n_buses, slack, lines, Pinj, overload_pct=100.0):
    base_theta, base_flows = dc_pf(n_buses,slack,lines,Pinj)
    results=[]
    for k in range(len(lines)):
        out = lines[:k]+lines[k+1:]
        try:
            _, flows = dc_pf(n_buses,slack,out,Pinj)
        except np.linalg.LinAlgError:
            results.append({"outage":k,"islanded":True,"overloads":[]})
            continue
        ov=[]
        for (f,t,F,rate) in flows:
            pct = 100*abs(F)/rate if rate>0 else np.inf
            if pct>overload_pct: ov.append({"from":f,"to":t,"MW":F,"rate":rate,"pct":pct})
        results.append({"outage":k,"islanded":False,"overloads":ov})
    return base_flows, results

# Demo reuse Day 11 data
lines = [(0,1,0.2,200),(1,2,0.25,150),(2,3,0.2,200),(0,3,0.4,100),(1,3,0.3,120)]
Pinj = [150,-50,-60,-40]
base_flows, res = n_1_screen(4,0,lines,Pinj,overload_pct=100)
print("Base line flows MW:", [round(f[2],2) for f in base_flows])
for r in res:
    if r["islanded"] or r["overloads"]:
        print("Outage line index", r["outage"], "ISLAND" if r["islanded"] else "Overloads:", r["overloads"])
