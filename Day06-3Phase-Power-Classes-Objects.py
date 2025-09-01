import math

class ThreePhaseLoad:
    def __init__(self, Vline, Iline, PF):
        self.Vline = Vline
        self.Iline = Iline
        self.PF = PF
    
    def calc_power(self):
        return round(math.sqrt(3) * self.Vline * self.Iline * self.PF, 2)
    
    def __str__(self):
        return f"3-Phase Load: V={self.Vline} V, I={self.Iline} A, PF={self.PF}, Power={self.calc_power()} W"

# Example
load1 = ThreePhaseLoad(415, 10, 0.9)
print(load1)
