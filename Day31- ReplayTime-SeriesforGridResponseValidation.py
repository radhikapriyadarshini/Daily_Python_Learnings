# Day 31: Replay Exported Time-Series for Grid Response
# Reads the Day 30 CSV and simulates SMIB frequency dynamics

import csv
import numpy as np

# --- Parameters ---
H = 5.0        # inertia constant
f0 = 50.0      # nominal frequency
D = 0.02       # damping
dt = 1.0       # time step (s)

# --- Read Time-Series from CSV ---
filename = "day30_timeseries_export.csv"
time, Pwind, Pload = [], [], []

with open(filename, mode="r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        time.append(float(row["Time(s)"]))
        Pwind.append(float(row["Wind_Power(pu)"]))
        Pload.append(float(row["Load(pu)"]))

time = np.array(time)
Pwind = np.array(Pwind)
Pload = np.array(Pload)

# --- Simulation ---
freq = np.zeros(len(time))
freq[0] = f0
Pconv = Pwind.copy()   # assume converter tracks wind power

for k in range(1, len(time)):
    dfd = (f0 / (2 * H)) * (Pconv[k] - Pload[k] - D * (freq[k-1] - f0))
    freq[k] = freq[k-1] + dfd * dt

# --- Print outputs ---
print("Time(s)\tWind(pu)\tLoad(pu)\tFreq(Hz)")
for i in range(0, len(time), 5):  # print every 5 seconds
    print(f"{time[i]:.0f}\t{Pwind[i]:.3f}\t\t{Pload[i]:.3f}\t\t{freq[i]:.3f}")

print("\n✅ Simulation complete. Final Frequency:", round(freq[-1], 3), "Hz")
