"""
Day 25: Wind Turbine Pitch Control + Dynamic Response
"""

import numpy as np
import matplotlib.pyplot as plt


class PitchControlledTurbine:
    def __init__(
        self,
        rated_power_w=3e6,
        rotor_diameter_m=120.0,
        air_density=1.225,
        cut_in=3.0,
        rated_wind=11.5,
        cut_out=25.0,
        inertia=5e6,  # kg·m² (rotor + drivetrain)
        gearbox_eff=0.97,
        generator_eff=0.95,
        dt=0.1,  # simulation timestep (s)
    ):
        self.rated_power = rated_power_w
        self.D = rotor_diameter_m
        self.area = np.pi * (self.D / 2) ** 2
        self.rho = air_density
        self.cut_in = cut_in
        self.rated_wind = rated_wind
        self.cut_out = cut_out
        self.inertia = inertia
        self.gearbox_eff = gearbox_eff
        self.generator_eff = generator_eff
        self.dt = dt

        # dynamic states
        self.omega = 1.0  # rad/s (rotor speed)
        self.pitch = 0.0  # deg (blade angle)

        # controller params
        self.Kp = 0.01
        self.Ki = 0.001
        self.integral_error = 0.0

    def aero_power(self, wind, pitch_deg):
        """Simplified Cp curve: drops with pitch angle."""
        if wind < self.cut_in or wind >= self.cut_out:
            return 0.0
        Cp_max = 0.45
        # Cp decreases with pitch (very crude)
        Cp = Cp_max * np.exp(-0.1 * pitch_deg)
        P_wind = 0.5 * self.rho * self.area * wind**3
        return Cp * P_wind

    def step(self, wind):
        """One timestep update (dt)."""
        # aerodynamic mechanical power
        P_aero = self.aero_power(wind, self.pitch)

        # electrical power
        P_elec = P_aero * self.gearbox_eff * self.generator_eff

        # pitch controller (if above rated wind)
        error = self.rated_power - P_elec
        if wind >= self.rated_wind:
            self.integral_error += error * self.dt
            pitch_rate = self.Kp * error + self.Ki * self.integral_error
            self.pitch += pitch_rate * self.dt
            self.pitch = max(0.0, min(30.0, self.pitch))  # physical limits

        # inertia update (rotor speed dynamics simplified)
        torque_aero = P_aero / max(self.omega, 0.1)
        torque_gen = P_elec / max(self.omega, 0.1)
        domega = (torque_aero - torque_gen) / self.inertia
        self.omega += domega * self.dt

        return P_elec, self.pitch, self.omega


# --- demo simulation ---
if __name__ == "__main__":
    wt = PitchControlledTurbine()

    T = 300  # seconds
    steps = int(T / wt.dt)
    wind = np.ones(steps) * 8.0  # base 8 m/s
    wind[100:200] = 15.0  # gust
    wind[200:] = 20.0  # strong wind

    P_hist, pitch_hist, omega_hist = [], [], []
    for v in wind:
        P, pitch, omega = wt.step(v)
        P_hist.append(P)
        pitch_hist.append(pitch)
        omega_hist.append(omega)

    t = np.arange(steps) * wt.dt

    plt.figure(figsize=(10, 6))
    plt.subplot(3, 1, 1)
    plt.plot(t, wind, label="Wind (m/s)")
    plt.ylabel("Wind")
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(t, np.array(P_hist) / 1e6, label="Power (MW)")
    plt.axhline(wt.rated_power / 1e6, color="r", linestyle="--", label="Rated")
    plt.ylabel("Power (MW)")
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(t, pitch_hist, label="Pitch (deg)")
    plt.plot(t, omega_hist, label="Rotor speed (rad/s)")
    plt.ylabel("Pitch / Speed")
    plt.legend()

    plt.tight_layout()
    plt.show()
