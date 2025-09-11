# Day 29: Simplified Converter-Based Wind Turbine
import numpy as np

# --- Parameters ---
sim_time = 60      # seconds
dt = 0.05          # step size
steps = int(sim_time / dt)
t = np.arange(0, sim_time, dt)

f0 = 50.0          # nominal frequency (Hz)
H = 5.0            # inertia constant (s)
D = 0.02           # damping (pu/Hz)

# Converter settings
K_ie = 0.8         # inertial emulation gain (pu / (Hz/s))
R = 0.05           # droop (pu/Hz)
T_conv = 0.2       # converter response time constant

# --- Profiles ---
Pwind = np.ones(steps) * 0.6
Pwind[(t >= 10) & (t < 30)] = 1.0   # gust
Pwind[(t >= 30)] = 0.7

Pload = np.ones(steps) * 0.6
Pload[(t >= 20)] = 0.9   # load increase

# --- Storage ---
freq = np.zeros(steps)
Pconv = np.zeros(steps)
Pmech = np.zeros(steps)

# Initial values
freq[0] = f0
Pconv[0] = 0.6   # start at balance

# --- Simulation loop ---
for k in range(1, steps):
    Pmech[k] = Pwind[k]

    # frequency derivative estimate
    dfdt = (freq[k-1] - freq[k-2])/dt if k > 1 else 0.0

    # converter target power: mech + inertia + droop
    Pinertia = K_ie * (-dfdt)
    Pdroop = -(1/R) * (freq[k-1] - f0)
    Ptarget = Pmech[k] + Pinertia + Pdroop

    # first-order tracking
    Pconv[k] = Pconv[k-1] + (dt/T_conv)*(Ptarget - Pconv[k-1])

    # swing equation
    dfd = (f0/(2*H)) * (Pconv[k] - Pload[k] - D*(freq[k-1]-f0))
    freq[k] = freq[k-1] + dfd*dt

# --- Print key outputs every 5 seconds ---
print("Time(s)\tFreq(Hz)\tPconv(pu)\tLoad(pu)\tWind(pu)")
for i in range(0, steps, int(5/dt)):
    print(f"{t[i]:.1f}\t{freq[i]:.3f}\t\t{Pconv[i]:.3f}\t\t{Pload[i]:.2f}\t\t{Pwind[i]:.2f}")

print("\nFinal Frequency:", round(freq[-1], 3), "Hz")
