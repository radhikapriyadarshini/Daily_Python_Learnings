import math

class PUTool:
    def __init__(self, Sbase_MVA: float, Vbase_kV: float, three_phase=True):
        self.Sb = Sbase_MVA * 1e6
        self.Vb = Vbase_kV * 1e3
        self.phases = 3 if three_phase else 1
        if three_phase:
            self.Ib = self.Sb / (math.sqrt(3)*self.Vb)
            self.Zb = (self.Vb**2) / self.Sb
        else:
            self.Ib = self.Sb / self.Vb
            self.Zb = (self.Vb**2) / self.Sb

    def to_pu(self, V=None, I=None, S_MVA=None, Z_ohm=None):
        return {
            "V_pu": None if V is None else V/self.Vb,
            "I_pu": None if I is None else I/self.Ib,
            "S_pu": None if S_MVA is None else (S_MVA*1e6)/self.Sb,
            "Z_pu": None if Z_ohm is None else Z_ohm/self.Zb
        }

    def from_pu(self, V_pu=None, I_pu=None, S_pu=None, Z_pu=None):
        return {
            "V": None if V_pu is None else V_pu*self.Vb,
            "I": None if I_pu is None else I_pu*self.Ib,
            "S_MVA": None if S_pu is None else S_pu*self.Sb/1e6,
            "Z_ohm": None if Z_pu is None else Z_pu*self.Zb
        }

def change_base_Z(Z_pu_old, Sbase_old_MVA, Vbase_old_kV, Sbase_new_MVA, Vbase_new_kV):
    Zb_old = (Vbase_old_kV*1e3)**2/(Sbase_old_MVA*1e6)
    Zb_new = (Vbase_new_kV*1e3)**2/(Sbase_new_MVA*1e6)
    return Z_pu_old * (Zb_old/Zb_new)

# Demo
pu = PUTool(100, 132, three_phase=True)
print(pu.to_pu(V=132e3, I=438.7, S_MVA=50, Z_ohm=20))
print(change_base_Z(Z_pu_old=0.15, Sbase_old_MVA=50, Vbase_old_kV=11, Sbase_new_MVA=100, Vbase_new_kV=11))
