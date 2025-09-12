# Day 30: Export Time-Series Data for PSSE / PowerFactory
# Runs with only NumPy and CSV — easy for online execution

import numpy as np
import csv

# --- Simulation Setup ---
sim_time = 60       # seconds
dt = 1              # 1-second resolution for export
steps = int(sim_time / dt)
t = np.arange(0, sim_time + dt, dt)

# Synthetic wind profile (pu)
Pwind = 0.6 + 0.2 * np.sin(0.1 * t)   # oscillating wind
Pwind[t > 30] += 0.1                  # step increase after 30s

# Synthetic load profile (pu)
Pload = 0.8 + 0.1 * np.cos(0.05 * t)

# Frequency response (Hz) – mimic converter support
f0 = 50.0
freq = f0 - 0.02 * np.sin(0.05 * t)   # small oscillations

# --- Export to CSV ---
filename = "day30_timeseries_export.csv"

with open(filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    
    # Header in PSSE/PowerFactory style
    writer.writerow(["Time(s)", "Wind_Power(pu)", "Load(pu)", "Frequency(Hz)"])
    
    # Rows
    for i in range(len(t)):
        writer.writerow([round(t[i], 2), round(Pwind[i], 4), round(Pload[i], 4), round(freq[i], 4)])

print(f"✅ Time-series data exported to {filename}")
