"""Vectorized whole-node baseline-first batch dispatch, no implicit overflow."""

import math

import numpy as np

from compute_economics.schemas import Policy, RunInput
from compute_economics.workload import DemandTable

ROUNDING_REL_TOL = 1e-10


def _ceil(value):
    nearest = np.rint(value)
    return np.ceil(
        np.where(
            np.abs(value - nearest) <= ROUNDING_REL_TOL * np.maximum(1, np.abs(value)),
            nearest,
            value,
        )
    )


def allocate(
    demand_tokens,
    hours,
    q_tokens_s: float,
    availability_fraction: float,
    max_nodes: int,
    quantum_hours: float = 1.0,
    startup_hours: float = 0.0,
):
    if (
        not math.isfinite(q_tokens_s)
        or q_tokens_s <= 0
        or not 0 < availability_fraction <= 1
        or type(max_nodes) is not int
        or max_nodes < 0
        or not math.isfinite(quantum_hours)
        or quantum_hours <= 0
        or not math.isfinite(startup_hours)
        or startup_hours < 0
    ):
        raise ValueError("invalid rental allocation controls")
    demand = np.asarray(demand_tokens, dtype=float)
    h = np.asarray(hours, dtype=float)
    if (
        not np.isfinite(demand).all()
        or not np.isfinite(h).all()
        or (demand < 0).any()
        or (h <= 0).any()
    ):
        raise ValueError("invalid demand or hours")
    # floor uses the same relative near-integer convention as ceil.
    multiples = h / quantum_hours
    nearest = np.rint(multiples)
    multiples = np.where(
        np.abs(multiples - nearest) <= ROUNDING_REL_TOL * np.maximum(1, np.abs(multiples)),
        nearest,
        multiples,
    )
    per_node = np.maximum(0, np.floor(multiples) * quantum_hours - startup_hours)
    served = np.minimum(demand, 3600 * q_tokens_s * availability_fraction * max_nodes * per_node)
    required = served / (3600 * q_tokens_s * availability_fraction)
    nodes = np.where(
        served > 0,
        np.maximum(
            1, _ceil(np.divide(required, per_node, out=np.zeros_like(required), where=per_node > 0))
        ),
        0,
    ).astype(int)
    per_alloc = np.divide(required, nodes, out=np.zeros_like(required), where=nodes > 0)
    billed = nodes * quantum_hours * _ceil((per_alloc + startup_hours) / quantum_hours)
    if (nodes > max_nodes).any() or (
        np.divide(billed, nodes, out=np.zeros_like(billed), where=nodes > 0) > h + 1e-8
    ).any():
        raise ArithmeticError("billing exceeds block capacity")
    return dict(
        overflow_tokens=served,
        unmet_tokens=np.maximum(0, demand - served),
        od_required_hours=required,
        od_execution_hours=served / (3600 * q_tokens_s),
        od_nodes=nodes,
        od_billed_hours=billed,
    )


def dispatch(run: RunInput, policy: Policy, demand: DemandTable) -> dict:
    if policy.family == "own" and policy.nodes <= run.spare_nodes:
        raise ValueError("owned fleet must exceed spares")
    if run.workload.performance_tokens_s is None:
        raise ValueError("missing throughput")
    q = run.workload.performance_tokens_s * run.transfer_fraction
    q_od = run.workload.performance_tokens_s * run.od_transfer_fraction
    nodes = np.full_like(demand.hours, policy.nodes, dtype=float)
    if policy.family == "own":
        nodes = np.where(demand.period > run.delay_months, policy.nodes - run.spare_nodes, 0.0)
    capacity = 3600 * q * run.availability_fraction * nodes * demand.hours
    baseline = np.minimum(demand.tokens, capacity)
    limit = run.max_od_nodes if run.max_od_nodes is not None else run.assumed_max_od_nodes
    if limit is None:
        raise ValueError("unknown rental capacity")
    od = allocate(
        np.maximum(0, demand.tokens - baseline),
        demand.hours,
        q_od,
        run.od_availability_fraction,
        limit,
        run.billing_quantum_hours,
        run.startup_hours,
    )
    return dict(
        baseline_tokens=baseline,
        baseline_execution_hours=baseline / (3600 * q),
        baseline_capacity_tokens=capacity,
        service_nodes=nodes,
        **od,
    )
