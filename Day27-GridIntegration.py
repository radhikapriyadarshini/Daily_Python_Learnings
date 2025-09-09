"""
day27_grid_integration.py
Day 27: Connect pitch-controlled wind turbine (mechanical source) to a
Synchronous Machine (SMIB) using the swing equation.

Requirements:
    pip install numpy scipy matplotlib

What it does:
- Uses a simplified pitch-controlled turbine to produce mechanical power Pm(t) [W].
- Converts Pm to per-unit on base power (Sb = turbine rated power).
- Synchronous machine modeled by swing equation:
    d(delta)/dt = 2*pi * (f - f0)
    d(f)/dt = (f0 / (2*H)) * (Pm_pu - Pe_pu - D * (f - f0))
  where Pe_pu = (E*V/X) * sin(delta)
- Simulates a wind gust and plots results (Pm, Pe, delta, freq).
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ------- Simple Pitch-Controlled Turbine (reduced from Day 25) -------
class PitchTurbineSimple:
    def __init__(
        self,
        rated_power_w=3e6,
        rotor_diameter_m=120.0,
        rho=1.225,
        cut_in=3.5,
        rated_wind=11.5,
        cut_out=25.0,
        gearbox_eff=0.97,
        gen_eff=0.95,
        dt=0.1,
    ):
        self.rated_power = rated_power_w
        self.D = rotor_diameter_m
        self.area = np.pi * (self.D/2.0)**2
        self.rho = rho
        self.cut_in = cut_in
        self.rated_wind = rated_wind
        self.cut_out = cut_out
        self.gearbox_eff = gearbox_eff
        self.gen_eff = gen_eff
        self.dt = dt

        # dynamic states
        self.pitch = 0.0       # degrees
        self.omega = 1.0       # rotor speed (arbitrary units for torque calc)

        # PI controller params (tune to taste)
        self.Kp = 5e-7     # chosen small because error in Watts
        self.Ki = 1e-7
        self.integral_error = 0.0

    def aero_power(self, v, pitch_deg):
        if v < self.cut_in or v >= self.cut_out:
            return 0.0
        Cp_max = 0.45
        Cp = Cp_max * np.exp(-0.1 * pitch_deg)   # crude pitch effect
        P_wind = 0.5 * self.rho * self.area * v**3
        P_mech = Cp * P_wind
        return min(P_mech, self.rated_power)

    def step(self, wind_speed):
        # compute mechanical power from aerodynamics
        P_mech = self.aero_power(wind_speed, self.pitch)

        # apply drivetrain & generator eff to get electrical
        P_elec = P_mech * self.gearbox_eff * self.gen_eff

        # pitch PI to track rated power if wind >= rated_wind
        error = self.rated_power - P_elec
        if wind_speed >= self.rated_wind:
            self.integral_error += error * self.dt
            dpitch_dt = self.Kp * error + self.Ki * self.integral_error
            self.pitch += dpitch_dt * self.dt
            # saturate pitch (0..30 deg)
            self.pitch = max(0.0, min(30.0, self.pitch))

        # small inertia effect on omega (very simplified)
        torque_aero = P_mech / max(self.omega, 0.1)
        torque_gen = P_elec / max(self.omega, 0.1)
        domega = (torque_aero - torque_gen) * 1e-6   # scale to keep omega stable
        self.omega += domega * self.dt

        return P_mech, P_elec, self.pitch, self.omega

# ------- Synchronous machine (reduced-order swing) -------
class SMIB:
    def __init__(self, base_power_w, H=5.0, D=0.02, E=1.05, V=1.0, X=0.8, f0=50.0):
        """
        base_power_w : base (S_base) in Watts (use turbine rated power)
        H : inertia constant (s)
        D : damping (pu/Hz)
        E : internal emf (pu)
        V : infinite bus voltage (pu)
        X : reactance between machine and infinite bus (pu)
        f0: nominal frequency (Hz)
        """
        self.Sb = base_power_w
        self.H = H
        self.D = D
        self.E = E
        self.V = V
        self.X = X
        self.f0 = f0

    def electrical_power_pu(self, delta):
        # Pe (pu) = (E*V/X) * sin(delta)
        return (self.E * self.V / self.X) * np.sin(delta)

    def swing_ode(self, t, y, Pm_pu_func):
        """
        y = [delta (rad), f (Hz)]
        Pm_pu_func: function Pm_pu(t) mechanical power in pu
        """
        delta, f = y
        Pm_pu = Pm_pu_func(t)
        Pe_pu = self.electrical_power_pu(delta)
        # df/dt = (f0/(2H)) * (Pm - Pe - D*(f - f0))
        dfdt = (self.f0 / (2.0 * self.H)) * (Pm_pu - Pe_pu - self.D * (f - self.f0))
        # ddelta/dt = 2*pi*(f - f0)
        ddt_delta = 2.0 * np.pi * (f - self.f0)
        return [ddt_delta, dfdt]

# ------- Simulation routine -------
def run_simulation(sim_time_s=200.0, dt=0.05):
    # instantiate turbine and SMIB
    rated_power_w = 3e6
    turbine = PitchTurbineSimple(rated_power_w=rated_power_w)
    smib = SMIB(base_power_w=rated_power_w, H=5.0, D=0.02, E=1.05, V=1.0, X=0.8, f0=50.0)

    # construct a wind profile: base 8 m/s, gust to 16 m/s between 30-100s, then stepdown
    t_eval = np.arange(0.0, sim_time_s + dt, dt)
    wind_ts = np.ones_like(t_eval) * 8.0
    gust_inds = (t_eval >= 30.0) & (t_eval <= 100.0)
    wind_ts[gust_inds] = 16.0
    wind_ts[t_eval > 140.0] = 10.0

    # precompute Pm(t) by stepping turbine at dt (turbine uses same dt)
    Pm_mech_W = np.zeros_like(t_eval)
    P_elec_W = np.zeros_like(t_eval)
    pitch_ts = np.zeros_like(t_eval)
    omega_ts = np.zeros_like(t_eval)

    for i, t in enumerate(t_eval):
        v = wind_ts[i]
        Pm, Pelec, pitch, omega = turbine.step(v)
        Pm_mech_W[i] = Pm
        P_elec_W[i] = Pelec
        pitch_ts[i] = pitch
        omega_ts[i] = omega

    # convert mechanical power to per-unit on base (pu)
    Pm_pu_ts = Pm_mech_W / rated_power_w  # because base = rated_power

    # create interpolation function for Pm_pu(t) to feed ODE
    from scipy.interpolate import interp1d
    Pm_pu_func = interp1d(t_eval, Pm_pu_ts, kind="previous", fill_value=(Pm_pu_ts[0], Pm_pu_ts[-1]), bounds_error=False)

    # initial conditions: delta small (rad), frequency = f0
    y0 = [0.0, smib.f0]

    # integrate swing equation
    sol = solve_ivp(lambda t, y: smib.swing_ode(t, y, Pm_pu_func),
                    [t_eval[0], t_eval[-1]], y0, t_eval=t_eval, method="RK45", rtol=1e-6)

    delta = sol.y[0, :]
    freq = sol.y[1, :]
    Pe_pu = (smib.E * smib.V / smib.X) * np.sin(delta)
    Pe_W = Pe_pu * rated_power_w

    # Plots
    plt.figure(figsize=(10, 9))

    plt.subplot(4, 1, 1)
    plt.plot(t_eval, wind_ts, label="Wind speed (m/s)")
    plt.ylabel("Wind (m/s)")
    plt.legend()

    plt.subplot(4, 1, 2)
    plt.plot(t_eval, Pm_mech_W/1e6, label="P_mech (MW)")
    plt.plot(t_eval, P_elec_W/1e6, label="Turbine electrical (MW)", alpha=0.7)
    plt.plot(t_eval, Pe_W/1e6, label="Generator electrical Pe (MW, delivered to grid)", linestyle="--")
    plt.ylabel("Power (MW)")
    plt.legend()

    plt.subplot(4, 1, 3)
    plt.plot(t_eval, pitch_ts, label="Pitch (deg)")
    plt.ylabel("Pitch (deg)")
    plt.legend()

    plt.subplot(4, 1, 4)
    plt.plot(t_eval, freq, label="System frequency (Hz)")
    plt.axhline(smib.f0, color="k", linestyle="--", alpha=0.6)
    plt.ylabel("Frequency (Hz)")
    plt.xlabel("Time (s)")
    plt.legend()

    plt.tight_layout()
    plt.show()

    # return time series for further analysis
    return {
        "t": t_eval,
        "wind": wind_ts,
        "Pm_mech_W": Pm_mech_W,
        "P_turbine_W": P_elec_W,
        "P_grid_W": Pe_W,
        "pitch": pitch_ts,
        "freq": freq,
        "delta": delta,
    }

# run demo if executed
if __name__ == "__main__":
    results = run_simulation(sim_time_s=220.0, dt=0.05)