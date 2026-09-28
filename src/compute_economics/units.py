"""Dimensional conversions and tolerance only; never infer workload throughput."""

import math


def node_to_gpu_rate(node_rate: float, gpu_count: int) -> float:
    if (
        not math.isfinite(node_rate)
        or node_rate < 0
        or type(gpu_count) is not int
        or gpu_count <= 0
    ):
        raise ValueError("nonnegative price and positive integer GPU count required")
    return node_rate / gpu_count


def ceil_tolerant(value: float) -> int:
    """Snap relative distance <=1e-10 to nearest integer before ceiling."""
    nearest = round(value)
    if abs(value - nearest) <= 1e-10 * max(1, abs(value)):
        return nearest
    return math.ceil(value)


def watts_to_kw(value: float) -> float:
    return value / 1000


def cents_to_usd(value: float) -> float:
    return value / 100
