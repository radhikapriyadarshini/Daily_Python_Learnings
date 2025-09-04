import numpy as np
import matplotlib.pyplot as plt

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
    Vf_all : numpy.ndarray
        Post-fault voltages at all buses (in pu).
    """
    Zkk = Zbus[faulted_bus, faulted_bus]
    If = V_prefault / (Zkk + Zf)

    # Post-fault voltages using Thevenin equivalent
    n_buses = Zbus.shape[0]
    Vf_all = np.ones(n_buses) * V_prefault  # initialize with prefault = 1 pu
    for i in range(n_buses):
        Vf_all[i] -= If * Zbus[i, faulted_bus]

    return If, Vf_all


# ---------------- Example ----------------
# Example 3-bus Zbus (dummy values in pu)
Zbus = np.array([
    [0.20, 0.05, 0.02],
    [0.05, 0.25, 0.06],
    [0.02, 0.06, 0.30]
])

faulted_bus = 1  # Fault at Bus 2 (0-based index)

If, Vf_all = zbus_fault_analysis(Zbus, faulted_bus)

print(f"Fault at Bus {faulted_bus+1}")
print(f"Fault Current = {abs(If):.4f} pu")
print("Post-Fault Voltages (pu):", Vf_all)


# -------- Visualization --------
n_buses = Zbus.shape[0]
pre_fault = np.ones(n_buses)  # all buses at 1 pu pre-fault
bus_indices = np.arange(1, n_buses+1)

plt.figure(figsize=(7,5))
plt.plot(bus_indices, pre_fault, 'go--', label="Pre-Fault Voltage (1 pu)")
plt.plot(bus_indices, Vf_all, 'ro-', label="Post-Fault Voltage")
plt.axhline(1.0, color='gray', linestyle='--', linewidth=0.8)

plt.title(f"Day 22 - Zbus Fault Analysis (Fault at Bus {faulted_bus+1})")
plt.xlabel("Bus Number")
plt.ylabel("Voltage (pu)")
plt.xticks(bus_indices)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
