import numpy as np

def transmission_losses(currents, resistances, load_power):
    """Calculate line losses and efficiency"""
    currents = np.array(currents)
    resistances = np.array(resistances)
    
    losses = (currents**2) * resistances  # vectorized
    total_loss = losses.sum()
    
    efficiency = (load_power / (load_power + total_loss)) * 100
    return total_loss, efficiency

# Example
currents = [100, 80, 60]
resistances = [0.5, 0.8, 0.6]
load_power = 50000  # W
loss, eff = transmission_losses(currents, resistances, load_power)
print("Total Loss:", round(loss, 2), "W")
print("Efficiency:", round(eff, 2), "%")
