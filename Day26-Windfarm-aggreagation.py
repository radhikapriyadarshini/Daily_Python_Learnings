"""
Day 26: Wind Farm Aggregation with Wake Losses (Jensen Model)

Requirements:
    pip install numpy matplotlib

Extends Day 24–25:
- Multiple turbines arranged in layout
- Jensen wake model for wind speed deficit
- Aggregate power output of farm
"""

import numpy as np
import matplotlib.pyplot as plt

from day24_wind_turbine import WindTurbine  # reuse Day 24 class


class WindFarm:
    def __init__(self, n_rows, n_cols, spacing=5.0, rotor_diameter=120.0,
                 rated_power=3e6, wake_decay=0.075):
        """
        n_rows, n_cols : layout (rows × cols)
        spacing        : spacing between turbines in rotor diameters
        rotor_diameter : turbine rotor diameter [m]
        wake_decay     : Jensen model decay constant (typical 0.05–0.1)
        """
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.spacing = spacing
        self.rotor_diameter = rotor_diameter
        self.rated_power = rated_power
        self.wake_decay = wake_decay

        # Create turbines
        self.turbines = [
            WindTurbine(rated_power_w=rated_power, rotor_diameter_m=rotor_diameter)
            for _ in range(n_rows * n_cols)
        ]

    def jensen_wake(self, wind_speed, x_dist, r0):
        """
        Jensen wake model:
        V = V0 * (1 - (1 - sqrt(1 - Ct)) * (r0 / (r0 + kx))^2)
        """
        Ct = 0.8  # thrust coefficient, approx
        k = self.wake_decay
        r = r0 + k * x_dist
        deficit = (1 - np.sqrt(1 - Ct)) * (r0 / r) ** 2
        return wind_speed * (1 - deficit)

    def farm_power(self, wind_speed, direction="x"):
        """
        Compute farm power for uniform inflow wind_speed.
        direction = 'x' means wind flows along rows (rows behind rows).
        """
        powers = []
        r0 = self.rotor_diameter / 2.0

        for row in range(self.n_rows):
            for col in range(self.n_cols):
                idx = row * self.n_cols + col
                wt = self.turbines[idx]

                if direction == "x":
                    # x spacing: rows are downstream
                    x_dist = row * self.spacing * self.rotor_diameter
                    if row == 0:
                        v_eff = wind_speed  # first row sees free wind
                    else:
                        v_eff = self.jensen_wake(wind_speed, x_dist, r0)
                else:
                    # no wake considered in y-direction for simplicity
                    v_eff = wind_speed

                P = wt.power_from_wind(v_eff)
                powers.append(P)

        return np.sum(powers), powers


# --- demo ---
if __name__ == "__main__":
    farm = WindFarm(n_rows=3, n_cols=4, spacing=6.0, rotor_diameter=120.0)

    wind_speeds = np.linspace(4, 20, 30)
    farm_power = []
    no_wake_power = []

    for v in wind_speeds:
        P_with_wake, _ = farm.farm_power(v)
        P_no_wake = farm.n_rows * farm.n_cols * farm.turbines[0].power_from_wind(v)
        farm_power.append(P_with_wake / 1e6)   # MW
        no_wake_power.append(P_no_wake / 1e6) # MW

    plt.figure(figsize=(8, 5))
    plt.plot(wind_speeds, no_wake_power, "k--", label="No wake (ideal sum)")
    plt.plot(wind_speeds, farm_power, "b-", label="With wake losses")
    plt.xlabel("Wind speed (m/s)")
    plt.ylabel("Farm power (MW)")
    plt.title("Wind Farm Output with Jensen Wake Model")
    plt.legend()
    plt.grid(True)
    plt.show()