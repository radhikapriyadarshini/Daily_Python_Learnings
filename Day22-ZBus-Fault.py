import numpy as np

def zbus_fault_analysis(Zbus, faulted_bus, V_prefault=1.0, Zf=0.0):
    """
    Perform fault analysis using Zbus method.
    
    Parameters:
    -----------
    Zbus : numpy.ndarray
        Bus impedance matrix (in pu).
    faulted_bus : int
        Bus number where fault occurs (0-based index).
    V_prefault : float
        Pre-fault bus voltage (default = 1.0 pu).
    Zf : float
        Fault impedance (default = 0 for bolted fault).
        
    Returns:
    --------
    If : float
        Fault current in pu.
    Vf : float
        Post-fault voltage at the faulted bus.
    """
    Zkk = Zbus[faulted_bus, faulted_bus]
    If = V_prefault / (Zkk + Zf)
    Vf = V_prefault - If * Zkk
    return If, Vf


# ---------------- Example ----------------
# Example 3-bus Zbus (dummy values in pu)
Zbus = np.array([
    [0.20, 0.05, 0.02],
    [0.05, 0.25, 0.06],
    [0.02, 0.06, 0.30]
])

faulted_bus = 1  # Fault at Bus 2 (0-based index)

If, Vf = zbus_fault_analysis(Zbus, faulted_bus)

print(f"Fault at Bus {faulted_bus+1}")
print(f"Fault Current = {abs(If):.4f} pu")
print(f"Post-Fault Voltage at Bus {faulted_bus+1} = {Vf:.4f} pu")
