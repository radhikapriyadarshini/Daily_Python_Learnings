import numpy as np

def economic_dispatch(a, b, c, Pmin, Pmax, PD, tol=1e-5, maxit=100):
    """
    Quadratic costs: Ci = ai*Pi^2 + bi*Pi + ci
    """
    a,b,c = map(np.array, (a,b,c))
    Pmin,Pmax = np.array(Pmin), np.array(Pmax)

    lam_low, lam_high = 0.0, 1e4
    P = np.zeros_like(a, dtype=float)

    for _ in range(maxit):
        lam = 0.5*(lam_low+lam_high)
        # Unconstrained Pi = (lam - bi)/(2ai)
        P = (lam - b)/(2*a)
        P = np.clip(P, Pmin, Pmax)
        mismatch = P.sum() - PD
        if abs(mismatch) < tol: break
        if mismatch > 0: lam_high = lam
        else: lam_low = lam

    cost = (a*P*P + b*P + c).sum()
    return P, lam, cost

# Demo
a = [0.002, 0.0035, 0.001]  # Rs/MW^2
b = [10, 8, 12]             # Rs/MW
c = [100, 120, 150]         # Rs
Pmin = [10, 20, 15]
Pmax = [100, 80, 120]
PD = 180
P, lam, cost = economic_dispatch(a,b,c,Pmin,Pmax,PD)
print("Dispatch MW:", np.round(P,2), " λ≈", round(lam,3), " Cost≈", round(cost,2))
