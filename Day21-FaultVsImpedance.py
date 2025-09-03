import numpy as np
import matplotlib.pyplot as plt

# --- Sequence Impedances (pu) ---
Z1 = 0.2 + 0.4j   # Positive sequence
Z2 = 0.2 + 0.4j   # Negative sequence
Z0 = 0.1 + 0.3j   # Zero sequence
V_pre = 1.0       # Prefault voltage (pu)

# --- Fault types to analyze ---
fault_types = ["3PH", "SLG", "LL", "LLG"]

def fault_current(fault_type, V, Z0, Z1, Z2, Zf):
    if fault_type == "3PH":
        return abs(V / (Z1 + Zf))

    elif fault_type == "SLG":
        return abs(3*V / (Z0 + Z1 + Z2 + 3*Zf))

    elif fault_type == "LL":
        return abs(np.sqrt(3) * V / (Z1 + Z2 + Zf))

    elif fault_type == "LLG":
        Z012 = (Z1*Z2 + Z2*Z0 + Z0*Z1) + Zf*(Z0+Z1+Z2)
        I1 = V*(Z2+Z0+Zf)/Z012
        I2 = V*(Z0+Z1+Zf)/Z012
        I0 = V*(Z1+Z2+Zf)/Z012
        return abs(I0+I1+I2)

    return 0

# --- Sweep faul
