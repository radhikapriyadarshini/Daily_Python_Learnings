import matplotlib.pyplot as plt
import pandas as pd

# Example bus voltage data (replace with real power flow results)
bus_data = {
    "Bus": [1, 2, 3, 4, 5],
    "Voltage (p.u.)": [1.02, 0.98, 1.01, 0.97, 1.00]
}

df = pd.DataFrame(bus_data)

# Plot voltage profile
plt.figure(figsize=(8, 5))
plt.plot(df["Bus"], df["Voltage (p.u.)"], marker='o', linestyle='-', linewidth=2)
plt.title("Bus Voltage Profile")
plt.xlabel("Bus Number")
plt.ylabel("Voltage (p.u.)")
plt.grid(True)
plt.ylim(0.9, 1.1)
plt.show()
