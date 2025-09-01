def series_resistance(resistances):
    """Calculate equivalent resistance of resistors in series."""
    if not resistances:  # error handling
        return 0
    return sum(resistances)  # list sum

# Example
resistors = [10, 20, 30]
Req = series_resistance(resistors)
print("Series Equivalent Resistance:", Req, "Ω")
