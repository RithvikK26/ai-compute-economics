from datetime import date

import numpy as np
import pytest
from conftest import changed

from compute_economics.capacity import allocate, dispatch
from compute_economics.schemas import Policy, RunInput
from compute_economics.workload import DemandTable, build_demand


def scalar(block):
    return {k: float(v[0]) for k, v in block.items()}


def test_independent_capacity_overflow(run):
    w = run.workload.model_copy(update={"performance_tokens_s": 1000.0})
    r = changed(
        run,
        workload=w,
        transfer_fraction=1.0,
        od_transfer_fraction=1.0,
        availability_fraction=0.9,
        od_availability_fraction=1.0,
    )
    d = DemandTable(
        np.array([1]),
        np.array([0]),
        np.array([10.0]),
        np.array([100_000_000.0]),
        np.array([10.0]),
        ("synthetic",),
    )
    out = scalar(dispatch(r, Policy(family="commit", nodes=2), d))
    assert out["baseline_tokens"] == 64_800_000
    assert out["overflow_tokens"] == 35_200_000
    assert out["unmet_tokens"] == 0


@pytest.mark.parametrize(
    "demand,served,billed,unmet",
    [(18e6, 18e6, 5, 0), (18.36e6, 18.36e6, 6, 0), (100e6, 72e6, 20, 28e6), (0, 0, 0, 0)],
)
def test_rental_oracles(demand, served, billed, unmet):
    out = scalar(allocate([demand], [10.0], 1000.0, 1.0, 2))
    assert out["overflow_tokens"] == served
    assert out["od_billed_hours"] == billed
    assert out["unmet_tokens"] == unmet
    if demand == 18e6:
        assert billed * 10 == 50


@pytest.mark.parametrize(
    "quantum,startup,limit",
    [(11.0, 0.0, 2), (1.0, 10.0, 2), (1.0, 0.0, 0), (3.0, 0.5, 4), (0.1, 0.2, 5)],
)
def test_limits_rounding(quantum, startup, limit):
    out = scalar(allocate([50e6], [10.0], 1000.0, 0.9, limit, quantum, startup))
    assert out["od_nodes"] <= limit
    assert out["overflow_tokens"] + out["unmet_tokens"] == pytest.approx(50e6)
    assert out["od_billed_hours"] >= out["od_required_hours"] - 1e-8
    assert out["od_billed_hours"] <= out["od_nodes"] * 10 + 1e-8


def test_calendar_and_hardware_invariance(run):
    d = build_demand(run)
    assert d.month_hours.sum() == 26304
    assert d.month_hours[d.month_labels.index("2028-02")] == 696
    altered = changed(
        run,
        configuration_id="cw-b300-8",
        workload=run.workload.model_copy(update={"performance_tokens_s": 112840.0}),
    )
    assert np.array_equal(build_demand(altered).tokens, d.tokens)
    with pytest.raises(ValueError):
        d.tokens[0] = 0
    for p in range(1, 37):
        assert d.hours[d.period == p].sum() == pytest.approx(d.month_hours[p - 1])


def test_conservation_and_delay(run):
    for limit in [0, 1, 4, 32]:
        r = changed(run, delay_months=6, max_od_nodes=limit, spare_nodes=1)
        d = build_demand(r)
        out = dispatch(r, Policy(family="own", nodes=4), d)
        np.testing.assert_allclose(
            out["baseline_tokens"] + out["overflow_tokens"] + out["unmet_tokens"],
            d.tokens,
            rtol=1e-9,
        )
        assert (out["baseline_tokens"][d.period <= 6] == 0).all()
        assert (
            out["baseline_execution_hours"]
            <= out["service_nodes"] * d.hours * r.availability_fraction + 1e-8
        ).all()
    with pytest.raises(ValueError):
        dispatch(r, Policy(family="own", nodes=1), d)


@pytest.mark.parametrize(
    "field,value",
    [
        ("transfer_fraction", 1.1),
        ("availability_fraction", 0.0),
        ("pue", 0.9),
        ("od_price_usd", -1.0),
        ("od_price_usd", float("nan")),
        ("block_fractions", []),
        ("currency", "EUR"),
        ("delay_months", 37),
        ("start_date", date(2026, 10, 2)),
    ],
)
def test_invalid_run(run, field, value):
    with pytest.raises(ValueError):
        RunInput.model_validate(dict(run.model_dump(), **{field: value}))


def test_unknown_capacity_and_duplicate_blocks(run):
    r = changed(run, max_od_nodes=None)
    with pytest.raises(ValueError):
        dispatch(r, Policy(family="on_demand", nodes=0), build_demand(r))
    with pytest.raises(ValueError):
        DemandTable(
            np.array([1, 1]),
            np.array([0, 0]),
            np.array([1.0, 1.0]),
            np.zeros(2),
            np.array([2.0]),
            ("x",),
        )
