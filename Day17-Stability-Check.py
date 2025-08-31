import numpy as np
import matplotlib.pyplot as plt

# System parameters
H = 3.5     # Inertia constant (MW-s/MVA)
D = 0.0     # Damping coefficient
Pm = 0.8    # Mechanical power (p.u.)
Pe0 = 0.7   # Initial electrical power (p.u.)
delta0 = 0  # Initial rotor angle (rad)
w0 = 0      # Initial speed deviation (rad/s)

# Time settings
t_end = 5
dt = 0.01
time = np.arange(0, t_end, dt)

# Initialize arrays
delta = np.zeros(len(time))
w = np.zeros(len(time))

# Initial conditions
delta[0] = delta0
w[0] = w0

# Numerical integration (Euler's method)
for i in range(1, len(time)):
    Pe = Pe0 * np.sin(delta[i-1])
    w[i] = w[i-1] + dt * (Pm - Pe - D * w[i-1]) / (2 * H)
    delta[i] = delta[i-1] + dt * w[i]

# Plot results
plt.figure(figsize=(8, 5))
plt.plot(time, delta, label="Rotor Angle (rad)")
plt.plot(time, w, label="Speed Deviation (rad/s)")
plt.xlabel("Time (s)")
plt.ylabel("Response")
plt.title("Swing Equation Response")
plt.legend()
plt.grid(True)
plt.show()
