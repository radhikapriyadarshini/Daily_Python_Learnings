import pandas as pd

def fault_current(bus_data, Vbase=230):
    """Compute fault current for each bus"""
    bus_data["I_fault"] = Vbase / bus_data["Zeq"]
    return bus_data

# Example bus data
data = {
    "Bus": ["Bus1", "Bus2", "Bus3"],
    "Zeq": [0.5, 0.8, 0.2]  # pu or Ohms
}
df = pd.DataFrame(data)
df = fault_current(df, Vbase=230)
print(df)

# Export to CSV
df.to_csv("fault_currents.csv", index=False)
