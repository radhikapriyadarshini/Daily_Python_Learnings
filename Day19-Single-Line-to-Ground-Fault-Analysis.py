import numpy as np

# System parameters
base_mva = 100       # MVA
base_kv = 132        # kV
z1 = 0.2 + 0.4j      # Positive sequence impedance (p.u.)
z2 = 0.2 + 0.4j      # Negative sequence impedance (p.u.)
z0 = 0.05 + 0.3j     # Zero sequence impedance (p.u.)
fault_impedance = 0  # Fault impedance (p.u.)
prefault_voltage = 1 # p.u.

# Fault calculation (SLG)
z_total = z1 + z2 + z0 + 3 * fault_impedance
i_f_pu = (3 * prefault_voltage) / z_total  # Fault current in p.u.

# Convert to Amps
i_base = base_mva * 1e6 / (np.sqrt(3) * base_kv * 1e3)
i_f_amps = abs(i_f_pu) * i_base

print(f"Fault Current (p.u.): {abs(i_f_pu):.3f}")
print(f"Fault Current (Amps): {i_f_amps:.2f} A")
