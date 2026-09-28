import pytest
from conftest import changed

from compute_economics.economics import evaluate_policy
from compute_economics.scenarios import (
    compare_policies,
    crossing_intervals,
    decision_analysis,
    enumerate_policies,
    evaluate_all,
    evaluate_stress,
)
from compute_economics.schemas import Policy
from compute_economics.workload import build_demand


def test_65_policies_and_infeasible_never_wins(run):
    assert len(enumerate_policies(run)) == 65
    r = changed(run, max_od_nodes=0, delay_months=6)
    results, c = evaluate_all(r)
    assert c["winner"] is not None
    assert all(x.status == "ineligible" for x in results if x.family == "own")
    assert c["winner"].startswith("commit:")
    assert c["savings_vs_od_usd"][c["winner"]] is None
    r = changed(r, upfront_cash_limit_usd=0.0, commit_price_usd=None)
    _, c = evaluate_all(r)
    assert c["winner"] is None
    assert c["message"] == "No modeled policy meets demand"


def test_ties_negative_and_zero_cost(run):
    result = evaluate_policy(run, Policy(family="own", nodes=4), build_demand(run))
    a = result.model_copy(update={"pv_cost_usd": 100.0, "status": "conditional"})
    b = result.model_copy(
        update={"policy_id": "own:5", "nodes": 5, "pv_cost_usd": 100.9, "status": "conditional"}
    )
    c = result.model_copy(
        update={"policy_id": "own:6", "nodes": 6, "pv_cost_usd": 102.0, "status": "conditional"}
    )
    assert compare_policies([a, b, c])["tie_set"] == [a.policy_id, b.policy_id]
    assert compare_policies(
        [a.model_copy(update={"pv_cost_usd": -100.0}), b.model_copy(update={"pv_cost_usd": -99.5})]
    )["tie_set"] == [a.policy_id, b.policy_id]


def test_bound_warning(run):
    r = changed(
        run,
        max_fleet_nodes=1,
        node_acquisition_usd=0.0,
        fixed_operations_annual_usd=0.0,
        per_node_operations_annual_usd=0.0,
        install_usd=0.0,
    )
    _, c = evaluate_all(r)
    assert c["winner"] == "own:1"
    assert any("search bound" in w for w in c["warnings"])


def test_fixed_policy_regret_and_shortage(run):
    r = changed(run, max_od_nodes=0)
    d = build_demand(r)
    p = Policy(family="commit", nodes=8)
    stress = evaluate_stress(r, p, {"low": d.scaled(0.1), "high": d.scaled(2.0)})
    assert all(v["fixed_nodes"] == 8 for v in stress["paths"].values())
    assert stress["paths"]["high"]["regret_usd"] is None
    assert stress["paths"]["high"]["unmet_tokens"] > 0
    assert stress["paths"]["low"]["regret_usd"] >= 0
    assert not stress["stable_across_tested_demand_paths"]


def test_multiple_discontinuous_crossings():
    points = [
        {
            "value": float(x),
            "winner": "own:1" if v < 0 else "on_demand:0",
            "fixed_policy_utilization": 0.5,
            "costs": {"own:1": 100.0 + v, "on_demand:0": 100.0},
        }
        for x, v in enumerate([-1.0, 2.0, -3.0, 4.0])
    ]
    crossings = crossing_intervals(points, "own:1")
    assert len(crossings["fixed_policy_sign_change_intervals"]) == 3
    assert [r["bracket"] for r in crossings["winner_switch_intervals"]] == [
        [0.0, 1.0],
        [1.0, 2.0],
        [2.0, 3.0],
    ]


def test_risk_output_and_surface(run):
    r = changed(run, max_fleet_nodes=2)
    result = decision_analysis(r)
    assert len(result["surface"]) == 400
    assert len(result["frontier"]["demand"]["points"]) == 36
    assert len(result["frontier"]["acquisition_cost_multiplier"]["points"]) == 21
    assert result["sensitivities"]["most_influential_tested_assumption"]
    winner = result["comparison"]["winner"]
    for sensitivity in result["sensitivities"]["one_at_a_time"].values():
        assert all(p["fixed_policy_id"] == winner for p in sensitivity["points"])
    assert "combined_adverse" in result["named_stresses"]


@pytest.mark.parametrize("family,nodes", [("commit", 2), ("own", 2)])
def test_zero_cash_limit(run, family, nodes):
    r = changed(run, upfront_cash_limit_usd=0.0, commit_setup_usd=1.0)
    out = evaluate_policy(r, Policy(family=family, nodes=nodes), build_demand(r))
    assert out.status == "ineligible"


def test_disappointment_preserves_time_zero_selection(run):
    _, planning = evaluate_all(run)
    shocked = decision_analysis(changed(run, demand_disappointment=True), include_surface=False)
    assert shocked["selected_policy_id"] == planning["winner"] == "own:6"
    assert shocked["comparison"]["winner"] == "own:5"
    assert "retrospective" in shocked["comparison"]["message"]
    assert all(
        p["fixed_nodes"] == 6 for p in shocked["fixed_policy_demand_stress"]["paths"].values()
    )
