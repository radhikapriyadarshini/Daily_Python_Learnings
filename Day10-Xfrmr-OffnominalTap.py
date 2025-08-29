import cmath

def xfmr_secondary_voltage(Vp_ll_kV, Z_series_pu, Sbase_MVA, Vp_base_kV, Vs_base_kV, tap_ratio_pu, load_pf=0.95, load_MVA=20):
    # Per-unit framework on system base
    Z_base_p = (Vp_base_kV*1e3)**2/(Sbase_MVA*1e6)
    Z_series = Z_series_pu * Z_base_p
    # Off-nominal tap a = Vp_nom/Vs_nom * tap -> effective turns ratio
    a = (Vp_base_kV/Vs_base_kV) * tap_ratio_pu

    # Load at secondary (line-line), reflect to primary
    S = load_MVA*1e6*(load_pf + 1j*cmath.sqrt(1-load_pf**2))
    Vp_ll = Vp_ll_kV*1e3
    Vp_ph = Vp_ll/cmath.sqrt(3)
    # Assume ideal with series Z on primary side
    # Current (primary) ≈ (S / a^2) / Vp_ll * sqrt(3)
    Sp = S / (a**2)
    Ip_line = Sp.conjugate() / (cmath.sqrt(3)*Vp_ll)
    Vdrop = Ip_line * Z_series
    Vp_ll_load = Vp_ll - Vdrop*cmath.sqrt(3)
    Vs_ll = Vp_ll_load / a
    return abs(Vs_ll)/1e3, a

def refer_Z_secondary_to_primary(Zs_pu_on_xfmr_base, Sxfmr_MVA, Vp_base_kV, Vs_base_kV, tap_ratio_pu, Ssys_MVA, Vsys_base_kV):
    a = (Vp_base_kV/Vs_base_kV) * tap_ratio_pu
    # Z referred to primary (ohm) = a^2 * Z_secondary_ohm
    Zb_s = (Vs_base_kV*1e3)**2/(Sxfmr_MVA*1e6)
    Zs_ohm = Zs_pu_on_xfmr_base * Zb_s
    Zp_ohm = (a**2)*Zs_ohm
    # Convert to system pu
    Zb_sys = (Vsys_base_kV*1e3)**2/(Ssys_MVA*1e6)
    return Zp_ohm / Zb_sys

Vs_kV, a = xfmr_secondary_voltage(132, Z_series_pu=0.08, Sbase_MVA=100, Vp_base_kV=132, Vs_base_kV=33, tap_ratio_pu=1.02, load_pf=0.9, load_MVA=30)
print(f"Secondary voltage ≈ {Vs_kV:.2f} kV (a={a:.3f})")

Zp_pu = refer_Z_secondary_to_primary(0.1, Sxfmr_MVA=50, Vp_base_kV=132, Vs_base_kV=33, tap_ratio_pu=0.98, Ssys_MVA=100, Vsys_base_kV=132)
print(f"Referred series impedance on system base: {Zp_pu:.4f} pu")
