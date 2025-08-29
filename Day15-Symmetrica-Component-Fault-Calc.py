import cmath

def fault_currents(Vpref_pu, Z1, Z2, Z0, Zf=0.0, fault="3PH"):
    """
    Vpref_pu: prefault positive-seq voltage at fault bus (pu)
    Z1,Z2,Z0: Thevenin seq impedances to the fault (pu)
    Zf: fault impedance (pu)
    fault in {"3PH","LG","LL","LLG"}
    Returns phase currents (Ia, Ib, Ic) in pu (phasors).
    """
    a = cmath.exp(1j*2*cmath.pi/3)
    if fault.upper()=="3PH":
        If1 = Vpref_pu / (Z1 + Zf)
        I1, I2, I0 = If1, 0, 0
    elif fault.upper()=="LG":
        denom = Z1 + Z2 + Z0 + 3*Zf
        If1 = Vpref_pu / denom
        I1 = I2 = I0 = If1
    elif fault.upper()=="LL":
        denom = Z1 + Z2 + Zf
        I1 = Vpref_pu / denom
        I2 = -I1
        I0 = 0
    elif fault.upper()=="LLG":
        denom = Z1 + ((Z2*(Z0+3*Zf))/(Z2+Z0+3*Zf))
        I1 = Vpref_pu / denom
        I2 = - (Z0+3*Zf)/(Z2+Z0+3*Zf) * I1
        I0 = - (Z2)/(Z2+Z0+3*Zf) * I1
    else:
        raise ValueError("Unknown fault type")

    # Phase currents from sequence components: [Ia, Ib, Ic]^T = T * [I0, I1, I2]
    T = [
        [1, 1, 1],
        [1, a*a, a],
        [1, a, a*a]
    ]
    I0I1I2 = [I0, I1, I2]
    Ia = sum(T[0][k]*I0I1I2[k] for k in range(3))
    Ib = sum(T[1][k]*I0I1I2[k] for k in range(3))
    Ic = sum(T[2][k]*I0I1I2[k] for k in range(3))
    return Ia, Ib, Ic

# Demo (typical strong grid)
Z1, Z2, Z0 = 0.2+1j*0.8, 0.2+1j*0.8, 0.1+1j*0.4
for ft in ["3PH","LG","LL","LLG"]:
    Ia,Ib,Ic = fault_currents(1.0, Z1,Z2,Z0, Zf=0.0, fault=ft)
    print(ft, "I_fault_pu ≈", round(abs(Ia),3), "(phase A magnitude)")
