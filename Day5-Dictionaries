import math

def calculate_pf(load):
    """Calculate apparent power and power factor from dict load = {'P': , 'Q': }"""
    P, Q = load["P"], load["Q"]
    S = math.sqrt(P**2 + Q**2)
    pf = P / S if S != 0 else 0
    return {"P": P, "Q": Q, "S": round(S, 2), "PF": round(pf, 3)}

# Example with multiple loads
loads = [
    {"P": 100, "Q": 80},
    {"P": 200, "Q": 150},
    {"P": 50, "Q": 40}
]

results = [calculate_pf(load) for load in loads]
for i, r in enumerate(results, 1):
    print(f"Load {i}: {r}")
