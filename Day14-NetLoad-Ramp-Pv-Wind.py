import numpy as np, pandas as pd

np.random.seed(7)
t = pd.date_range("2025-01-01", periods=96, freq="15min")
load = 800 + 150*np.sin(2*np.pi*(t.hour*60+t.minute)/1440 - 1.0) + 20*np.random.randn(len(t))
pv = np.maximum(0, 250*np.sin(np.pi*(t.hour*60+t.minute)/720 - np.pi/2))  # 0 at night, peak ~midday
wind = 120 + 40*np.sin(2*np.pi*(t.hour*60+t.minute)/1440 + 0.7) + 30*np.random.randn(len(t))

df = pd.DataFrame({"Load_MW":load, "PV_MW":pv, "Wind_MW":wind}, index=t)
df["NetLoad_MW"] = df["Load_MW"] - df["PV_MW"] - df["Wind_MW"]
df["Ramp_MW_per_15min"] = df["NetLoad_MW"].diff()
reserve_req_pct = 0.03  # 3% of peak load as a simple policy
df["ReserveReq_MW"] = reserve_req_pct*df["Load_MW"].rolling(96, min_periods=1).max()

# Key stats
print("Peak Load MW:", round(df["Load_MW"].max(),1))
print("Min Net Load MW:", round(df["NetLoad_MW"].min(),1))
print("Max 15-min Ramp Up MW:", round(df["Ramp_MW_per_15min"].max(),1))
print("Max 15-min Ramp Down MW:", round(df["Ramp_MW_per_15min"].min(),1))
print(df.head(8))
