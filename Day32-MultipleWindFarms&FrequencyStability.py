# Day 32: Multiple Wind Farms & Frequency Stability
# Simple Euler-based swing equation with two wind farm profiles

import numpy as np

# --- Parameters ---
H = 6.0       # inertia constant (s)
f0 = 50.0     # nominal frequency (Hz)
D = 0.02      # damping (pu/Hz)
dt = 1.0      # 1s step
T = 120       # total sim time (s)

steps = int(T/dt)
time = np.arange(0, T+dt, dt)

# --- Wind farm profiles (per-unit on base power) ---
farm1 = 0.6 + 0.2*np.sin(0.05*time)        # farm1 sinusoidal variation
farm2 = 0.7 + 0.1*np.cos(0.07*time+1.0)    # farm2 shifted cosine
# Aggregated power
Pwind_total = (farm1 + farm2) / 2.0        # avg of 2 farms

# --- Load profile ---
Pload = np.ones_like(time) * 0.8
Pload[60:] = 1.0   # step load increase at 60s

# --- Simulation ---
freq = np.zeros_like(time)
freq[0] = f0

for k in range(1, len(time)):
    # swing equation
    dfd = (f0/(2*H)) * (Pwind_total[k] - Pload[k] - D*(freq[k-1]-f0))
    freq[k] = freq[k-1] + dfd*dt

# --- Print summary ---
print("Time(s)\tFarm1(pu)\tFarm2(pu)\tTotal(pu)\tLoad(pu)\tFreq(Hz)")
for i in range(0, len(time), 10):  # every 10s
    print(f"{time[i]:.0f}\t{farm1[i]:.3f}\t\t{farm2[i]:.3f}\t\t{Pwind_total[i]:.3f}\t\t{Pload[i]:.2f}\t\t{freq[i]:.3f}")

print("\n✅ Simulation complete. Final Frequency:", round(freq[-1], 3), "Hz")
