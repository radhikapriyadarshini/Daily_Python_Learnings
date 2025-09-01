def parallel_resistance(resistances):
    """Calculate equivalent resistance of resistors in parallel."""
    if not resistances:
        return 0
    inv_sum = 0
    for r in resistances:
        inv_sum += 1/r
    return 1 / inv_sum

# Example
resistors = (10, 20, 30)  # tuple also works
Req = parallel_resistance(resistors)
print("Parallel Equivalent Resistance:", round(Req, 2), "Ω")
