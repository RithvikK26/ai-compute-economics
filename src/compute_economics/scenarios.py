"""Bounded policies, fixed-policy risk and bracketed decision frontiers."""

from itertools import product

import numpy as np

from compute_economics.economics import evaluate_policy
from compute_economics.schemas import Policy, PolicyResult, RunInput
from compute_economics.validation import validate_run
from compute_economics.workload import DemandTable, build_demand

TIE_FRACTION = 0.01


def with_inputs(run: RunInput, **updates) -> RunInput:
    """Revalidate every changed scenario, never use unvalidated model_copy for input edits."""
    return RunInput.model_validate(dict(run.model_dump(), **updates))


def enumerate_policies(run: RunInput) -> list[Policy]:
    return (
        [Policy(family="on_demand", nodes=0)]
        + [Policy(family="commit", nodes=k) for k in range(1, run.max_fleet_nodes + 1)]
        + [
            Policy(family="own", nodes=k)
            for k in range(max(1, run.spare_nodes + 1), run.max_fleet_nodes + 1)
        ]
    )


def compare_policies(results: list[PolicyResult], constraints: dict | None = None) -> dict:
    constraints = constraints or {}
    feasible = [r for r in results if r.status == "conditional" and r.pv_cost_usd is not None]
    feasible.sort(key=lambda r: (r.pv_cost_usd, r.policy_id))
    winner = feasible[0] if feasible else None
    baseline = next((r for r in feasible if r.family == "on_demand"), None)
    tie = (
        [
            r.policy_id
            for r in feasible
            if r.pv_cost_usd - winner.pv_cost_usd <= abs(winner.pv_cost_usd) * TIE_FRACTION + 1e-8
        ]
        if winner
        else []
    )
    warnings = []
    if winner and winner.nodes == constraints.get("max_fleet_nodes"):
        warnings.append(
            "Lowest-cost policy reaches the fleet search bound; expand within the 128-node cap to test it"
        )
    return {
        "winner": winner.policy_id if winner else None,
        "lowest_pv_usd": winner.pv_cost_usd if winner else None,
        "tie_set": tie,
        "feasible_count": len(feasible),
        "message": "Under the selected assumptions, "
        + winner.policy_id
        + " has the lowest modeled cost."
        if winner
        else "No modeled policy meets demand",
        "savings_vs_od_usd": {
            r.policy_id: baseline.pv_cost_usd - r.pv_cost_usd
            if baseline and r in feasible
            else None
            for r in results
        },
        "warnings": warnings,
    }


def evaluate_all(
    run: RunInput, demand: DemandTable | None = None, *, detailed: bool = False
) -> tuple[list[PolicyResult], dict]:
    demand = demand if demand is not None else build_demand(run)
    report = validate_run(run)
    results = []
    for policy in enumerate_policies(run):
        if report.errors or policy.family in report.policy_exclusions:
            result = evaluate_policy(run, policy, demand, detailed=detailed)
        else:
            result = evaluate_policy(run, policy, demand, detailed=detailed, validated=True)
        results.append(result)
    comparison = compare_policies(results, {"max_fleet_nodes": run.max_fleet_nodes})
    comparison["warnings"] = report.warnings + comparison["warnings"]
    return results, comparison


def evaluate_stress(
    run: RunInput, fixed_policy: Policy, named_paths: dict[str, DemandTable]
) -> dict:
    paths = {}
    for name, demand in named_paths.items():
        fixed = evaluate_policy(run, fixed_policy, demand, detailed=False)
        _, optimum = evaluate_all(run, demand)
        feasible = fixed.status == "conditional"
        paths[name] = {
            "fixed_policy_id": fixed.policy_id,
            "fixed_nodes": fixed.nodes,
            "fixed_pv_usd": fixed.pv_cost_usd,
            "unmet_tokens": fixed.unmet_tokens,
            "feasible": feasible,
            "scenario_optimum": optimum["winner"],
            "tie_set": optimum["tie_set"],
            "regret_usd": fixed.pv_cost_usd - optimum["lowest_pv_usd"]
            if feasible and optimum["winner"]
            else None,
            "in_tie_set": fixed.policy_id in optimum["tie_set"],
        }
    return {
        "fixed_policy_id": fixed_policy.policy_id,
        "paths": paths,
        "stable_across_tested_demand_paths": all(
            p["feasible"] and p["in_tie_set"] for p in paths.values()
        ),
        "reversals": [name for name, p in paths.items() if not p["in_tie_set"]],
    }


def _point(run, demand, axis_value, selected):
    results, comparison = evaluate_all(run, demand)
    fixed = (
        next((r for r in results if r.policy_id == selected.policy_id), None) if selected else None
    )
    alternatives = [
        r.pv_cost_usd
        for r in results
        if r.status == "conditional" and r.policy_id != comparison["winner"]
    ]
    return {
        "value": float(axis_value),
        "winner": comparison["winner"],
        "lowest_pv_usd": comparison["lowest_pv_usd"],
        "tie_set": comparison["tie_set"],
        "fixed_policy_pv_usd": fixed.pv_cost_usd if fixed else None,
        "fixed_policy_utilization": fixed.execution_utilization if fixed else None,
        "fixed_policy_unmet_tokens": fixed.unmet_tokens if fixed else None,
        "runner_up_gap_usd": min(alternatives) - comparison["lowest_pv_usd"]
        if alternatives
        else None,
        "costs": {
            r.policy_id: r.pv_cost_usd if r.status == "conditional" else None for r in results
        },
    }


def crossing_intervals(points: list[dict], fixed_id: str | None) -> dict:
    switches = []
    signs = []
    for left, right in zip(points, points[1:]):
        bracket = [left["value"], right["value"]]
        if left["winner"] != right["winner"]:
            switches.append(
                {
                    "bracket": bracket,
                    "from": left["winner"],
                    "to": right["winner"],
                    "fixed_policy_utilization_bracket": [
                        left["fixed_policy_utilization"],
                        right["fixed_policy_utilization"],
                    ],
                }
            )
        if fixed_id:
            for alternative in left["costs"]:
                if alternative == fixed_id:
                    continue
                values = [
                    left["costs"].get(fixed_id),
                    left["costs"].get(alternative),
                    right["costs"].get(fixed_id),
                    right["costs"].get(alternative),
                ]
                if any(v is None for v in values):
                    continue
                a, b = values[0] - values[1], values[2] - values[3]
                if (a < 0 < b) or (b < 0 < a) or (a == 0) != (b == 0):
                    signs.append(
                        {
                            "bracket": bracket,
                            "fixed_policy": fixed_id,
                            "alternative": alternative,
                            "difference_usd": [a, b],
                        }
                    )
    return {
        "winner_switch_intervals": switches,
        "fixed_policy_sign_change_intervals": signs,
        "scope": "Adjacent tested brackets only; integer fleet/billing discontinuities preserved; no interpolated root.",
        "status": "Crossings found" if switches or signs else "No crossing in tested range",
    }


def sensitivities(run: RunInput, demand: DemandTable, selected: Policy | None) -> dict:
    cases = {
        "demand": [(0.5, {}), (1.0, {}), (1.5, {})],
        "acquisition_cost": [
            (0.75, {"node_acquisition_usd": run.node_acquisition_usd * 0.75}),
            (1.0, {}),
            (1.25, {"node_acquisition_usd": run.node_acquisition_usd * 1.25}),
        ]
        if run.node_acquisition_usd is not None
        else [],
        "transfer_factor": [
            (f, {"transfer_fraction": f, "od_transfer_fraction": f}) for f in [0.5, 0.7, 0.9]
        ],
        "rental_future_price": [(f, {"future_price_multiplier": f}) for f in [0.8, 1.0, 1.2]],
        "commitment_price": [(p, {"commit_price_usd": p}) for p in [32.0, 40.0, 48.0]],
        "discount_rate": [(r, {"discount_rate_fraction": r}) for r in [0.05, 0.10, 0.15]],
        "electricity": [(e, {"electricity_usd_kwh": e}) for e in [0.05, 0.10, 0.15]]
        if run.hosting_mode == "metered_energy"
        else [],
        "residual": [(0.0, {}), (0.2, {})],
    }
    output = {}
    reversals = []
    for name, values in cases.items():
        points = []
        for value, updates in values:
            candidate = with_inputs(run, **updates)
            test_demand = demand.scaled(value) if name == "demand" else demand
            if name == "residual":
                results = []
                for p in enumerate_policies(candidate):
                    c = (
                        with_inputs(
                            candidate, residual_usd=value * p.nodes * candidate.node_acquisition_usd
                        )
                        if p.family == "own" and candidate.node_acquisition_usd is not None
                        else candidate
                    )
                    results.append(evaluate_policy(c, p, test_demand, detailed=False))
                comparison = compare_policies(
                    results, {"max_fleet_nodes": candidate.max_fleet_nodes}
                )
            else:
                results, comparison = evaluate_all(candidate, test_demand)
            fixed = next(
                (r for r in results if selected and r.policy_id == selected.policy_id), None
            )
            alternative = [
                r.pv_cost_usd
                for r in results
                if r.status == "conditional" and (not selected or r.policy_id != selected.policy_id)
            ]
            margin = (
                min(alternative) - fixed.pv_cost_usd
                if fixed and fixed.status == "conditional" and alternative
                else None
            )
            point = {
                "value": value,
                "fixed_policy_id": selected.policy_id if selected else None,
                "fixed_nodes": selected.nodes if selected else None,
                "fixed_pv_usd": fixed.pv_cost_usd if fixed else None,
                "fixed_unmet_tokens": fixed.unmet_tokens if fixed else None,
                "advantage_vs_best_alternative_usd": margin,
                "reoptimized_winner": comparison["winner"],
                "tie_set": comparison["tie_set"],
            }
            points.append(point)
            if selected and selected.policy_id not in comparison["tie_set"]:
                reversals.append(
                    {
                        "assumption": name,
                        "value": value,
                        "winner": comparison["winner"],
                        "fixed_policy_unmet_tokens": point["fixed_unmet_tokens"],
                    }
                )
        margins = [
            p["advantage_vs_best_alternative_usd"]
            for p in points
            if p["advantage_vs_best_alternative_usd"] is not None
        ]
        output[name] = {
            "points": points,
            "decision_margin_range_usd": max(margins) - min(margins) if margins else None,
        }
    influential = max(
        (k for k, v in output.items() if v["decision_margin_range_usd"] is not None),
        key=lambda k: output[k]["decision_margin_range_usd"],
        default=None,
    )
    return {
        "one_at_a_time": output,
        "most_influential_tested_assumption": influential,
        "influence_definition": "Range of fixed selected-policy cost advantage over the best feasible alternative at the disclosed endpoints; not a probability or statistical interval.",
        "tested_reversals": reversals,
    }


def decision_analysis(run: RunInput, *, include_surface: bool = True) -> dict:
    demand = build_demand(run)
    results, comparison = evaluate_all(run, demand)
    planning_comparison = comparison
    planning_results = results
    if run.demand_disappointment:
        planning_run = with_inputs(run, demand_disappointment=False)
        planning_results, planning_comparison = evaluate_all(
            planning_run, build_demand(planning_run)
        )
        comparison["message"] += (
            f" This is the retrospective optimum; the time-zero base policy {planning_comparison['winner']} remains fixed for disappointment exposure."
        )
    selected = next(
        (
            Policy(family=r.family, nodes=r.nodes)
            for r in planning_results
            if r.policy_id == planning_comparison["winner"]
        ),
        None,
    )
    stress = (
        evaluate_stress(
            run,
            selected,
            {
                name: demand.scaled(m)
                for name, m in [("downside", 0.5), ("base", 1.0), ("upside", 1.5)]
            },
        )
        if selected
        else None
    )
    extra = {}
    if selected:
        disappoint = DemandTable(
            demand.period,
            demand.block,
            demand.hours,
            demand.tokens
            if run.demand_disappointment
            else demand.tokens * np.where(demand.period >= 7, 0.5, 1.0),
            demand.month_hours,
            demand.month_labels,
        )
        extra["demand_disappointment"] = evaluate_stress(
            run, selected, {"from_month_7": disappoint}
        )
        adverse = with_inputs(run, future_price_multiplier=0.8, residual_usd=0.0)
        extra["obsolescence_stress"] = evaluate_stress(
            adverse, selected, {"lower_future_rental_and_zero_residual": demand}
        )
        delayed = with_inputs(run, delay_months=min(6, run.horizon_months), max_od_nodes=4)
        extra["combined_adverse"] = evaluate_stress(
            with_inputs(delayed, future_price_multiplier=0.8, residual_usd=0.0),
            selected,
            {"delay_limited_overflow_lower_rent_and_zero_residual": demand},
        )
    axes = {}
    axes["demand"] = [
        _point(run, demand.scaled(float(x)), float(x), selected) for x in np.linspace(0.25, 2.0, 36)
    ]
    axes["acquisition_cost_multiplier"] = (
        [
            _point(
                with_inputs(run, node_acquisition_usd=run.node_acquisition_usd * float(x)),
                demand,
                float(x),
                selected,
            )
            for x in np.linspace(0.75, 1.25, 21)
        ]
        if run.node_acquisition_usd is not None
        else []
    )
    axes["commitment_price_usd_node_hour"] = [
        _point(with_inputs(run, commit_price_usd=float(x)), demand, float(x), selected)
        for x in np.linspace(32, 48, 17)
    ]
    frontier = {
        name: {
            "points": points,
            **crossing_intervals(points, selected.policy_id if selected else None),
        }
        for name, points in axes.items()
    }
    surface = []
    if include_surface and run.node_acquisition_usd is not None:
        for dmult, cmult in product(np.linspace(0.25, 2.0, 20), np.linspace(0.75, 1.25, 20)):
            r = with_inputs(run, node_acquisition_usd=run.node_acquisition_usd * float(cmult))
            _, c = evaluate_all(r, demand.scaled(float(dmult)))
            surface.append(
                {
                    "demand_multiplier": float(dmult),
                    "acquisition_multiplier": float(cmult),
                    "node_acquisition_usd": r.node_acquisition_usd,
                    "winner": c["winner"],
                    "lowest_pv_usd": c["lowest_pv_usd"],
                    "tie_set": c["tie_set"],
                    "status": "conditional" if c["winner"] else "infeasible_or_unavailable",
                }
            )
    return {
        "comparison": comparison,
        "planning_comparison": planning_comparison,
        "selected_policy_id": selected.policy_id if selected else None,
        "policies": [r.model_dump() for r in results],
        "fixed_policy_demand_stress": stress,
        "named_stresses": extra,
        "frontier": frontier,
        "surface": surface,
        "sensitivities": sensitivities(run, demand, selected),
        "scope": "Conditional lowest cost within enumerated fixed policies. Frontier reoptimizes K at each point; stress and sensitivity exposure preserve selected K.",
    }
