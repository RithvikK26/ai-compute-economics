import numpy as np
import pytest
from conftest import changed

from compute_economics.economics import (
    capital_recovery,
    cash_totals,
    energy_kwh,
    evaluate_policy,
    simplified_own_breakeven,
)
from compute_economics.schemas import Ancillary, Policy
from compute_economics.workload import build_demand


def test_pv_oracle():
    cash = [1200.0] + [100.0] * 12
    cash[-1] -= 120.0
    pv, tco = cash_totals(cash, 0.1)
    assert pv == pytest.approx(2230.95787384216, rel=1e-9)
    assert tco == 2280
    assert cash_totals(cash, 0.0) == (2280.0, 2280.0)


def test_energy_oracles():
    assert energy_kwh(2, 720, 2, 10, 600, 0, 1.25) == (7680, 9600)
    assert energy_kwh(2, 720, 2, 10, 0, 0, 1.25) == (2880, 3600)
    assert energy_kwh(2, 720, 2, 10, 600, 0, 1.25)[1] * 0.1 == 960


def test_closed_form_and_historical_arithmetic():
    assert simplified_own_breakeven(100000, 10000, 20, 5)["utilization"] == pytest.approx(2 / 3)
    assert simplified_own_breakeven(200000, 10000, 20, 5)["utilization"] is None
    assert simplified_own_breakeven(100000, 10000, 5, 5)["utilization"] is None
    assert 4 / 10 == 0.4
    assert capital_recovery(1200, 120, 0, 1) == 1080
    assert 68.8 / (102703 * 3600) * 1e6 == pytest.approx(0.18608133, abs=1e-8)


def test_zero_demand_commitment(run):
    from datetime import date

    r = changed(
        run,
        start_date=date(2026, 11, 1),
        horizon_months=1,
        commit_term_months=1,
        demand_multiplier=0.0,
        commit_price_usd=10.0,
    )
    result = evaluate_policy(r, Policy(family="commit", nodes=2), build_demand(r))
    assert result.obligation_usd == 14400
    assert result.tco_usd == 14400
    assert result.execution_utilization == 0
    assert result.levelized_usd_million_tokens is None
    assert result.unused_commitment_usd == 14400


@pytest.mark.parametrize("family,nodes", [("on_demand", 0), ("commit", 4), ("own", 4)])
def test_ledgers_reconcile(run, family, nodes):
    result = evaluate_policy(run, Policy(family=family, nodes=nodes), build_demand(run))
    assert sum(r["cash_usd"] for r in result.cost_ledger) == pytest.approx(result.tco_usd)
    assert sum(r["pv_usd"] for r in result.cost_ledger) == pytest.approx(result.pv_cost_usd)
    assert sum(r["pv_usd"] for r in result.monthly_ledger) == pytest.approx(result.pv_cost_usd)
    assert sum(result.category_pv_usd.values()) == pytest.approx(result.pv_cost_usd)
    assert not any("depreciation" in k or "interest" in k for k in result.category_pv_usd)
    if family == "on_demand":
        assert result.upfront_usd == 0 and "electricity" not in result.category_pv_usd


def test_prepayment_and_terminal_once(run):
    policy = Policy(family="commit", nodes=2)
    a = evaluate_policy(run, policy, build_demand(run))
    r = changed(run, prepaid_fraction=1.0)
    b = evaluate_policy(r, policy, build_demand(r))
    assert a.obligation_usd == b.obligation_usd
    assert a.tco_usd == pytest.approx(b.tco_usd)
    assert b.pv_cost_usd > a.pv_cost_usd
    r = changed(run, residual_usd=120000.0, exit_usd=1000.0)
    result = evaluate_policy(r, Policy(family="own", nodes=2), build_demand(r))
    residual = [x for x in result.cost_ledger if x["category"] == "residual" and x["cash_usd"]]
    assert len(residual) == 1 and residual[0]["period"] == 36 and residual[0]["cash_usd"] == -120000


def test_all_in_and_shared_fee(run):
    with pytest.raises(ValueError):
        changed(run, hosting_mode="all_in_colo")
    r = changed(
        run,
        hosting_mode="all_in_colo",
        electricity_usd_kwh=0.0,
        all_in_colo_monthly_usd=1000.0,
        ancillary=[
            Ancillary(
                item_id="service",
                mode="fixed_monthly",
                scope="shared",
                rate_usd=100.0,
                rationale="synthetic",
            )
        ],
    )
    result = evaluate_policy(r, Policy(family="own", nodes=2), build_demand(r))
    assert "electricity" not in result.category_pv_usd
    assert (
        sum(x["cash_usd"] for x in result.cost_ledger if x["category"] == "ancillary:service")
        == 3600
    )


def test_delay_and_spare_idle(run):
    r = changed(run, delay_months=6, spare_nodes=1)
    result = evaluate_policy(r, Policy(family="own", nodes=2), build_demand(r))
    assert all(x["it_kwh"] == 0 for x in result.monthly_ledger[:7])
    assert all(x["it_kwh"] >= 2 * 2 * x["hours"] for x in result.monthly_ledger[7:])
    assert result.upfront_usd == 850000


@pytest.mark.parametrize(
    "updates",
    [
        {"commit_term_months": 40},
        {"usable_life_months": 12},
        {"od_price_usd": None},
        {"node_acquisition_usd": None},
    ],
)
def test_missing_and_term_life_gates(run, updates):
    r = changed(run, **updates)
    family = "commit" if "commit_term_months" in updates else "own"
    out = evaluate_policy(r, Policy(family=family, nodes=2), build_demand(r))
    assert out.status == "unavailable" and out.pv_cost_usd is None


def test_price_and_capacity_monotonicity(run):
    p = Policy(family="own", nodes=4)
    base = evaluate_policy(run, p, build_demand(run))
    for fields in [
        {"node_acquisition_usd": 500000.0},
        {"od_price_usd": 80.0},
        {"electricity_usd_kwh": 0.2},
    ]:
        r = changed(run, **fields)
        out = evaluate_policy(r, p, build_demand(r))
        assert out.pv_cost_usd >= base.pv_cost_usd
    costs = []
    for m in [0.5, 1.0, 1.5]:
        costs.append(evaluate_policy(run, p, build_demand(run).scaled(m)).pv_cost_usd)
    assert np.diff(costs).min() >= 0


def test_independent_fixture_file():
    import json
    from pathlib import Path

    from compute_economics.economics import simplified_commit_breakeven

    fixtures = json.loads(Path("tests/fixtures/independent_oracles.json").read_text())
    c = fixtures["cash"]
    values = [c["upfront_usd"]] + [c["monthly_usd"]] * c["months"]
    values[-1] -= c["terminal_proceeds_usd"]
    assert cash_totals(values, c["annual_rate"]) == pytest.approx(
        (c["expected_pv_usd"], c["expected_tco_usd"]), rel=1e-9
    )
    b = fixtures["commit_breakeven"]
    assert simplified_commit_breakeven(b["price_usd"], b["rental_usd"]) == b["expected_used_share"]
    assert simplified_commit_breakeven(4, 0) is None


@pytest.mark.parametrize(
    "included,cost_field",
    [("installation", "install_usd"), ("network", "network_usd"), ("storage", "storage_usd")],
)
def test_included_capital_component_not_charged_twice(run, included, cost_field):
    with pytest.raises(ValueError, match="quote includes"):
        changed(run, acquisition_includes=[included], **{cost_field: 1000.0})


def test_setup_once_and_engine_zero_discount(run):
    r = changed(run, commit_setup_usd=100.0, discount_rate_fraction=0.0)
    out = evaluate_policy(r, Policy(family="commit", nodes=2), build_demand(r))
    assert out.pv_cost_usd == pytest.approx(out.tco_usd)
    assert sum(x["cash_usd"] for x in out.cost_ledger if x["category"] == "commit_setup") == 200.0
    assert out.upfront_usd == 200.0
