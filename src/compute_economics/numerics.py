"""Scalar binary64 primitives that avoid NumPy CPU-dispatched power kernels."""


def scalar_power(base: float | int, exponent: float | int) -> float:
    """Use Python float operands; retain the platform scalar libm power convention."""
    return float(base) ** float(exponent)
