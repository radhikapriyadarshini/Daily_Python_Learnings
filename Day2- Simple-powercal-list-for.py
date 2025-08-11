def calculate_power(voltage, resistance): # calculate power, definie function argument Voltage and resistance
    power = voltage ** 2 / resistance #power formula
    return power #return power, exiting the loop
    
voltage = 230 # voltage
resistances = [46, 92, 115, 230] #resistance in list
powers = [] #list to store individual power value

for r in resistances: #define for loop for each resistance power is caluclated r=0~3
    p = calculate_power(voltage, r) # calauclate power for each r
    powers.append(p) #append ads the value of power in Powers list, basically each append adds value in the end
    print(f"Load with {r} Ω: {p:.2f} Watts")

total_power = sum(powers) #calculate the Sum of (Power for all r )
print("\nTotal Power in the System:", round(total_power, 2), "Watts")
