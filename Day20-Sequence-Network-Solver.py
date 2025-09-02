import numpy as np

# --- System Data ---
Z1 = 0.2 + 0.4j  # Positive sequence impedance
Z2 = 0.2 + 0.4j  # Negative sequence impedance
Z0 = 0.1 + 0.3j  # Zero sequence impedance
V_pre = 1.0       # Pre-fault voltage (pu)
fault_type = 'SLG'  # Options: SLG, LL, LLG, 3PH

# --- Fault Impedance ---
Zf = 0 + 0j  # Assume solid fault (can modify for impedance fault)

# --- Sequence Currents ---
def calc_fault_currents(fault_type, V_pre, Z0, Z1, Z2, Zf):
    if fault_type == '3PH':
        I1 = V_pre / (Z1 + Zf)
        I2 = 0
        I0 = 0

    elif fault_type == 'SLG':  # Single-Line-to-Ground
        I0 = I1 = I2 = V_pre / (Z0 + Z1 + Z2 + 3*Zf)

    elif fault_type == 'LL':  # Line-to-Line
        I1 = V_pre / (Z1 + Z2 + Zf)
        I2 = -I1
        I0 = 0

    elif fault_type == 'LLG':  # Double-Line-to-Ground
        Z012 = (Z1 * Z2 + Z2 * Z0 + Z0 * Z1) + Zf * (Z0 + Z1 + Z2)
        I1 = V_pre * (Z2 + Z0 + Zf) / Z012
        I2 = V_pre * (Z0 + Z1 + Zf) / Z012
        I0 = V_pre * (Z1 + Z2 + Zf) / Z012

    else:
        raise ValueError("Unknown fault type. Use SLG, LL, LLG, 3PH.")

    return I0, I1, I2

I0, I1, I2 = calc_fault_currents(fault_type, V_pre, Z0, Z1, Z2, Zf)

print(f"Fault Type: {fault_type}")
print(f"I0 = {I0:.4f} pu")
print(f"I1 = {I1:.4f} pu")
print(f"I2 = {I2:.4f} pu")

# --- Phase Currents (Optional) ---
a = np.exp(1j * 2 * np.pi / 3)
A = np.array([[1,1,1],[1,a**2,a],[1,a,a**2]])
I_phase = A @ np.array([I0, I1, I2])

print(f"\nPhase Currents:")
print(f"Ia = {I_phase[0]:.4f} pu")
print(f"Ib = {I_phase[1]:.4f} pu")
print(f"Ic = {I_phase[2]:.4f} pu")
