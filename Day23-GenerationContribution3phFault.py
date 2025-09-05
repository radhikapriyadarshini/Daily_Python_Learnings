import numpy as np

# Zbus matrix (example, per-unit)
Zbus = np.array([
    [0.20+0j, 0.05+0j, 0.02+0j],
    [0.05+0j, 0.25+0j, 0.08+0j],
    [0.02+0j, 0.08+0j, 0.30+0j]
])

V_prefault = np.array([1+0j, 1+0j, 1+0j])  # Assume 1∠0 pu prefault voltages
fault_bus = 2   # Bus-3 (Python index starts from 0)

# Fault impedance (Zf=0 means solid fault)
Zf = 0+0j

# Fault current at bus k
Vk_prefault = V_prefault[fault_bus]
Zkk = Zbus[fault_bus, fault_bus]
If = Vk_prefault / (Zkk + Zf)

print("Fault current at Bus-3 (pu):", If)

# Post-fault bus voltages
V_post = V_prefault - Zbus[:, fault_bus] * If
print("Post-fault bus voltages (pu):", V_post)

# Generator currents (assuming gen at bus 1 & 2)
# Current injection = (Vprefault - Vpost) / Zbus element
I_gen1 = (V_prefault[0] - V_post[0]) / Zbus[0,0]
I_gen2 = (V_prefault[1] - V_post[1]) / Zbus[1,1]

print("Generator-1 fault contribution (pu):", I_gen1)
print("Generator-2 fault contribution (pu):", I_gen2)