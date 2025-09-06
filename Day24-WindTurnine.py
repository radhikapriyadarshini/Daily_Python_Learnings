What it does:
- Defines a WindTurbine class with:
  - rated_power (W)
  - rotor_diameter (m)
  - air_density (kg/m3)
  - cut_in, rated, cut_out speeds (m/s)
  - simple power curve (piecewise linear or using Cp approximation)
- Simulate output over a wind-speed timeseries
- Compute energy, capacity factor, and farm aggregation
"""

from __future__ import annotations
import numpy as np

# Optional plotting if you want to visualize results
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

class WindTurbine:
    def __init__(
        self,
        rated_power_w: float,
        rotor_diameter_m: float,
        cut_in: float = 3.0,
        rated_wind: float = 12.0,
        cut_out: float = 25.0,
        air_density: float = 1.225,
        gearbox_eff: float = 0.97,
        generator_eff: float = 0.95,
        power_curve_type: str = "piecewise"  # or "betz_cp"
    ):
        self.rated_power_w = float(rated_power_w)
        self.rotor_diameter_m = float(rotor_diameter_m)
        self.rotor_area = np.pi * (self.rotor_diameter_m / 2.0) ** 2
        self.cut_in = float(cut_in)
        self.rated_wind = float(rated_wind)
        self.cut_out = float(cut_out)
        self.rho = float(air_density)
        self.gearbox_eff = float(gearbox_eff)
        self.generator_eff = float(generator_eff)
        self.power_curve_type = power_curve_type

    def power_from_wind(self, wind_speed_m_s: float) -> float:
        """Return electrical power output (W) for a given wind speed (m/s)."""
        v = wind_speed_m_s
        # Outside operating range
        if v < self.cut_in or v >= self.cut_out:
            return 0.0

        if self.power_curve_type == "piecewise":
            # simple piecewise:
            # - between cut_in and rated: cubic scaling up to rated_power
            # - between rated and cut_out: constant rated_power
            if v < self.rated_wind:
                # P = P_rated * ( (v - vci) / (vr - vci) )^3  (smooth cubic ramp)
                frac = (v - self.cut_in) / max((self.rated_wind - self.cut_in), 1e-9)
                mech_power = self.rated_power_w * (frac ** 3)
            else:
                mech_power = self.rated_power_w
        elif self.power_curve_type == "betz_cp":
            # Use Betz-like Cp approximation: Cp(lambda) simplified -> depends on TSR (not modeled here)
            # We do a simple model: Cp_max * (1 - exp(-k*(v/v_rated)))
            Cp_max = 0.45  # realistic peak Cp < 0.59 (Betz)
            k = 3.0
            cp = Cp_max * (1 - np.exp(-k * (v / self.rated_wind)))
            p_wind = 0.5 * self.rho * self.rotor_area * v ** 3
            mech_power = cp * p_wind
            # limit to rated
            mech_power = min(mech_power, self.rated_power_w)
        else:
            raise ValueError("Unknown power_curve_type")

        # apply drivetrain & generator efficiencies to get electrical power
        elec_power = mech_power * self.gearbox_eff * self.generator_eff
        # Ensure not above rated (small numerical errors)
        return min(elec_power, self.rated_power_w)

    def simulate_series(self, wind_speeds: np.ndarray, dt_seconds: float = 3600.0) -> np.ndarray:
        """
        Simulate electrical power time series given wind_speeds array (m/s).
        dt_seconds is time-step duration; default = 3600s (hourly).
        Returns array of power in Watts for each sample.
        """
        winds = np.asarray(wind_speeds, dtype=float)
        powers = np.array([self.power_from_wind(v) for v in winds])
        return powers

    def energy_and_capacity_factor(self, power_ts_w: np.ndarray, dt_seconds: float = 3600.0):
        """
        Compute total energy (Wh or MWh) and capacity factor.
        Returns energy_MWh, capacity_factor
        """
        dt_hours = dt_seconds / 3600.0
        energy_Wh = np.sum(power_ts_w) * dt_hours  # Wh
        energy_MWh = energy_Wh / 1e6
        max_possible_MWh = (self.rated_power_w / 1e6) * (len(power_ts_w) * dt_hours)
        capacity_factor = energy_MWh / max_possible_MWh if max_possible_MWh > 0 else 0.0
        return energy_MWh, capacity_factor

# --- Quick demo / test ---
if __name__ == "__main__":
    # Example turbine: 3.0 MW, 120 m rotor diameter
    wt = WindTurbine(rated_power_w=3e6, rotor_diameter_m=120.0,
                     cut_in=3.5, rated_wind=11.5, cut_out=25.0,
                     power_curve_type="piecewise")

    # create an hourly synthetic wind time series for 1 week
    rng = np.random.default_rng(42)
    hours = 24 * 7
    # base wind speed with diurnal sinusoid + random gusts
    t = np.arange(hours)
    base = 8.0 + 2.5 * np.sin(2 * np.pi * t / 24.0)  # daily cycle
    noise = rng.normal(0, 1.2, size=hours)
    wind_series = np.clip(base + noise, 0.0, 30.0)

    power_ts = wt.simulate_series(wind_series, dt_seconds=3600.0)
    energy_MWh, cf = wt.energy_and_capacity_factor(power_ts, dt_seconds=3600.0)

    print(f"Simulated {hours} hours. Energy = {energy_MWh:.3f} MWh, Capacity factor = {cf:.3f}")

    if plt:
        plt.figure(figsize=(9,4))
        plt.plot(t, wind_series, label="Wind speed (m/s)")
        plt.ylabel("Wind speed (m/s)")
        plt.twinx().plot(t, power_ts/1e6, "r-", label="Power (MW)")
        plt.title("Wind speed and power (synthetic week)")
        plt.legend()
        plt.show()