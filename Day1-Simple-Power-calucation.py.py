def calculate_power(voltage, resistance): #define the function, fucntion name is calculate_power, arguments are voltage and resistance
    power = voltage ** 2 / resistance #Power formula
    return power #exit the function and return the value of power, wherever the function is called

voltage = 12  # define Volts
resistance = 6  # define Ohms
power = calculate_power(voltage, resistance) #function called, pass the values to the argument
print(f"Power in the system: {power} Watts")#formatted string where {power} replaced by power value in the output
