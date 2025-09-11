"""
Day 28: Governor (primary frequency) + AVR (exciter) added to SMIB + pitch turbine
Brief:
- Uses PitchTurbineSimple from Day 27 (embedded here as a reduced turbine model).
- SMIB has: swing equation, governor, exciter.
- Governor: droop R (pu/Hz), time constant Tg (s). Produces Pm_gov (pu).
- AVR/exciter: first-order model dE/dt = (K_A*(V_ref - V_t) - E) / T_A
- Simulate wind gust and a small load step; observe frequency response and AVR effect.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# ---------------------------
# Reduced pitch-controlled turbine (small, self-contained)
# ---------------------------
class PitchTurbineSimple:
    def __init__(self,
                 rated_power_w=3e6,
                 rotor_diameter_m=120.0,
                 rho=1.225,
                 cut_in=3.5,
                 rated_wind=11.5,
                 cut_out=25.0,
                 gearbox_eff=0.97,
                 gen_eff=0.95,
                 dt=0.05):
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
        self.pitch = 0.0
        self.omega = 1.0

        # simple PI pitch controller tuned modestly for this demo
        self.Kp = 5e-7
        self.Ki = 1e-7
        self.integral_error = 0.0

    def aero_power(self, v, pitch_deg):
        if v < self.cut_in or v >= self.cut_out:
            return 0.0
        Cp_max = 0.45
        Cp = Cp_max * np.exp(-0.1 * pitch_deg)
        P_wind = 0.5 * self.rho * self.area * v**3
        P_mech = Cp * P_wind
        return min(P_mech, self.rated_power)

    def step(self, wind_speed):
        P_mech = self.aero_power(wind_speed, self.pitch)
        P_elec = P_mech * self.gearbox_eff * self.gen_eff

        # pitch control to keep near rated if wind >= rated_wind
        error = self.rated_power - P_elec
        if wind_speed >= self.rated_wind:
            self.integral_error += error * self.dt
            dpitch_dt = self.Kp * error + self.Ki * self.integral_error
            self.pitch += dpitch_dt * self.dt
            self.pitch = max(0.0, min(30.0, self.pitch))

        # small inertia effect on omega (very simplified)
        torque_aero = P_mech / max(self.omega, 1e-6)
        torque_gen = P_elec / max(self.omega, 1e-6)
        domega = (torque_aero - torque_gen) * 1e-6
        self.omega += domega * self.dt

        return P_mech, P_elec, self.pitch, self.omega

# ---------------------------
# SMIB with governor + exciter
# ---------------------------
class SMIB_GovExc:
    def __init__(self, base_power_w,
                 H=5.0, D=0.02,
                 X=0.8, Vt=1.0,
                 f0=50.0,
                 # Governor params
                 R=0.05, Tg=0.5,
                 # Exciter params
                 K_A=200.0, T_A=0.1, V_ref=1.0):
        """
        base_power_w : base power (W) for pu conversions
        H : inertia constant (s)
        D : damping coefficient (pu/Hz)
        X : reactance between machine internal and infinite bus (pu)
        Vt: terminal/infinite-bus voltage (pu) [treated constant here]
        f0: nominal frequency (Hz)

        Governor:
          R: droop (pu / Hz)  (typical 0.03-0.05)
          Tg: governor time constant (s)

        Exciter:
          K_A: AVR gain
          T_A: AVR time constant (s)
          V_ref: voltage setpoint (pu)
        """
        self.Sb = base_power_w
        self.H = H
        self.D = D
        self.X = X
        self.Vt = Vt
        self.f0 = f0

        # governor
        self.R = R
        self.Tg = Tg

        # exciter
        self.K_A = K_A
        self.T_A = T_A
        self.V_ref = V_ref

    def electrical_power_pu(self, delta, E):
        # Pe_pu = (E * Vt / X) * sin(delta)
        return (E * self.Vt / self.X) * np.sin(delta)

    def swing_and_controls(self, t, y, Pm_turbine_pu_func, P_load_step_pu):
        """
        State vector y:
         y[0] = delta (rad)
         y[1] = f (Hz)
         y[2] = E (pu)         # internal voltage (exciter state)
         y[3] = Pgov (pu)      # governor mechanical power injection (pu)
        Inputs:
         Pm_turbine_pu_func(t): mechanical power from turbine (pu)
         P_load_step_pu(t): additional load (pu) as injected disturbance (positive => extra load)
        """
        delta, f, E, Pgov = y

        # turbine mechanical power (pu) from external turbine model
        Pm_turb_pu = float(Pm_turbine_pu_func(t))

        # governor (droop): desired Pgov_ref = - (1/R) * (f - f0)  + Pgov_offset
        # We choose Pgov_offset = 0 so governor provides correction around zero.
        Pgov_ref = - (1.0 / self.R) * (f - self.f0)  # pu (if f drops, Pgov_ref increases)

        # limit Pgov_ref to reasonable values (e.g., [-1.5, +1.5] pu)
        Pgov_ref = np.clip(Pgov_ref, -1.5, 1.5)

        # governor dynamics: first-order tracking to Pgov_ref
        dPgov_dt = (Pgov_ref - Pgov) / self.Tg

        # total mechanical power into machine = turbine + governor contribution
        Pm_total_pu = Pm_turb_pu + Pgov

        # electrical power delivered to infinite bus (pu)
        Pe_pu = self.electrical_power_pu(delta, E)

        # consider an external load step that increases demand (positive means more load to serve),
        # so machine must supply Pe + load = Pm_total (convention: Pe + load = Pm)
        # Move load into RHS: net electrical demand = Pe_pu + P_load_step_pu(t)
        P_load = float(P_load_step_pu(t))

        # swing equation: df/dt = (f0 / (2H)) * (Pm_total - (Pe + P_load) - D*(f - f0))
        df_dt = (self.f0 / (2.0 * self.H)) * (Pm_total_pu - (Pe_pu + P_load) - self.D * (f - self.f0))

        # delta dynamics
        ddelta_dt = 2.0 * np.pi * (f - self.f0)

        # exciter dynamics: dE/dt = (K_A*(V_ref - Vt) - E) / T_A
        # Note: terminal voltage Vt treated as constant here (infinite bus). AVR will move E toward K_A*(V_ref - Vt)
        # For demonstration we still show dynamics; if Vt == V_ref, exciter settles to zero change.
        dE_dt = (self.K_A * (self.V_ref - self.Vt) - E) / self.T_A

        return [ddelta_dt, df_dt, dE_dt, dPgov_dt]

# ---------------------------
# Simulation routine
# ---------------------------
def run_day28(sim_time_s=200.0, dt=0.05):
    rated_power_w = 3e6
    turbine = PitchTurbineSimple(rated_power_w=rated_power_w, dt=dt)
    smib = SMIB_GovExc(base_power_w=rated_power_w,
                       H=5.0, D=0.02,
                       X=0.8, Vt=1.0, f0=50.0,
                       R=0.05, Tg=0.5,
                       K_A=200.0, T_A=0.1, V_ref=1.0)

    t_eval = np.arange(0.0, sim_time_s + dt, dt)

    # wind profile: base 8 m/s, gust 16 m/s between 20-80s
    wind_ts = np.ones_like(t_eval) * 8.0
    gust = (t_eval >= 20.0) & (t_eval <= 80.0)
    wind_ts[gust] = 16.0

    # small load step at t = 120s: extra load 0.2 pu
    def P_load_step_pu(t):
        return 0.2 if t >= 120.0 else 0.0

    # Run the turbine forward at dt to get Pm_turbine_pu(t)
    Pm_turb_mech_W = np.zeros_like(t_eval)
    P_turb_elec_W = np.zeros_like(t_eval)
    pitch_ts = np.zeros_like(t_eval)
    omega_ts = np.zeros_like(t_eval)

    for i, t in enumerate(t_eval):
        v = wind_ts[i]
        Pm_mech, P_elec, pitch, omega = turbine.step(v)
        Pm_turb_mech_W[i] = Pm_mech
        P_turb_elec_W[i] = P_elec
        pitch_ts[i] = pitch
        omega_ts[i] = omega

    # convert mechanical turbine power to pu (base = rated_power)
    Pm_turb_pu_ts = Pm_turb_mech_W / rated_power_w
    Pm_func = interp1d(t_eval, Pm_turb_pu_ts, kind="previous", fill_value=(Pm_turb_pu_ts[0], Pm_turb_pu_ts[-1]), bounds_error=False)

    # initial conditions: delta=0 rad, f=f0, E ~ 1.0 pu, Pgov=0
    y0 = [0.0, smib.f0, 1.0, 0.0]

    sol = solve_ivp(lambda t, y: smib.swing_and_controls(t, y, Pm_func, P_load_step_pu),
                    [t_eval[0], t_eval[-1]], y0, t_eval=t_eval, method="RK45", rtol=1e-6)

    delta = sol.y[0, :]
    freq = sol.y[1, :]
    E_ts = sol.y[2, :]
    Pgov_ts = sol.y[3, :]

    Pe_pu_ts = (E_ts * smib.Vt / smib.X) * np.sin(delta)
    Pe_W_ts = Pe_pu_ts * rated_power_w
    Pm_total_pu_ts = Pm_turb_pu_ts + Pgov_ts
    Pm_total_W = Pm_total_pu_ts * rated_power_w

    # Plotting
    plt.figure(figsize=(10, 10))

    plt.subplot(5, 1, 1)
    plt.plot(t_eval, wind_ts, label="Wind (m/s)")
    plt.ylabel("Wind (m/s)")
    plt.legend()

    plt.subplot(5, 1, 2)
    plt.plot(t_eval, Pm_turb_mech_W / 1e6, label="Turbine P_mech (MW)")
    plt.plot(t_eval, Pgov_ts * rated_power_w / 1e6, label="Governor Pm contribution (MW)")
    plt.plot(t_eval, Pm_total_W / 1e6, label="Total Pm (MW)")
    plt.plot(t_eval, Pe_W_ts / 1e6, '--', label="Pe to grid (MW)")
    plt.ylabel("Power (MW)")
    plt.legend()

    plt.subplot(5, 1, 3)
    plt.plot(t_eval, Pgov_ts, label="Pgov (pu)")
    plt.axvline(120.0, color='k', linestyle='--', alpha=0.4)
    plt.ylabel("Pgov (pu)")
    plt.legend()

    plt.subplot(5, 1, 4)
    plt.plot(t_eval, freq, label="Frequency (Hz)")
    plt.axhline(smib.f0, color="k", linestyle="--")
    plt.axvline(120.0, color='k', linestyle='--', alpha=0.4)
    plt.ylabel("Frequency (Hz)")
    plt.legend()

    plt.subplot(5, 1, 5)
    plt.plot(t_eval, E_ts, label="Internal E (pu)")
    plt.ylabel("E (pu)")
    plt.xlabel("Time (s)")
    plt.legend()

    plt.tight_layout()
    plt.show()

    return {
        "t": t_eval,
        "wind": wind_ts,
        "Pm_turb_mech_W": Pm_turb_mech_W,
        "Pgov_W": Pgov_ts * rated_power_w,
        "Pm_total_W": Pm_total_W,
        "Pe_W": Pe_W_ts,
        "freq": freq,
        "delta": delta,
        "E": E_ts,
        "pitch": pitch_ts,
    }

# quick run when file executed
if __name__ == "__main__":
    res = run_day28(sim_time_s=220.0, dt=0.05)
