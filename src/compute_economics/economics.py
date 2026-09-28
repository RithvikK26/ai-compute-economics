"""Cash-based unlevered economics. Positive costs, negative sale proceeds."""

import numpy as np

from compute_economics.capacity import dispatch
from compute_economics.schemas import Policy, PolicyResult, RunInput
from compute_economics.validation import validate_run
from compute_economics.workload import DemandTable


def bounded_ratio(numerator, denominator):
    if not denominator:
        return None
    value = float(numerator / denominator)
    if value < -1e-9 or value > 1 + 1e-9:
        raise ArithmeticError("Physical ratio outside conservation tolerance")
    return min(1.0, max(0.0, value))


def discount_factors(annual_fraction: float, periods: int):
    return (1 + annual_fraction) ** (-np.arange(periods + 1) / 12)


def cash_totals(cash_usd, annual_fraction: float):
    cash = np.asarray(cash_usd, dtype=float)
    return float(cash @ discount_factors(annual_fraction, len(cash) - 1)), float(cash.sum())


def energy_kwh(nodes, hours, idle_kw, load_kw, execution_hours, auxiliary_kw, pue):
    it = nodes * idle_kw * hours + (load_kw - idle_kw) * execution_hours + auxiliary_kw * hours
    return it, it * pue


def simplified_own_breakeven(fixed_usd, capacity_hours, rental_usd_hour, variable_usd_hour):
    if fixed_usd == 0:
        return {"utilization": None, "reason": "Examine marginal costs; no fixed burden"}
    if capacity_hours <= 0 or rental_usd_hour <= variable_usd_hour:
        return {"utilization": None, "reason": "No cost breakeven"}
    u = fixed_usd / (capacity_hours * (rental_usd_hour - variable_usd_hour))
    return {
        "utilization": u if u <= 1 else None,
        "reason": "Feasible" if u <= 1 else "No feasible crossing",
    }


def simplified_commit_breakeven(commit_usd_hour, rental_usd_hour):
    if rental_usd_hour <= 0:
        return None
    share = commit_usd_hour / rental_usd_hour
    return share if 0 <= share <= 1 else None


def capital_recovery(investment_usd, terminal_usd, annual_rate, years):
    pv = investment_usd - terminal_usd / (1 + annual_rate) ** years
    crf = annual_rate / (1 - (1 + annual_rate) ** (-years)) if annual_rate else 1 / years
    return pv * crf


def evaluate_policy(
    run: RunInput,
    policy: Policy,
    demand: DemandTable,
    *,
    detailed: bool = True,
    validated: bool = False,
) -> PolicyResult:
    warnings = []
    if not validated:
        report = validate_run(run)
        reason = (
            report.errors + [report.policy_exclusions[policy.family]]
            if policy.family in report.policy_exclusions
            else report.errors
        )
        if policy.family == "own" and policy.nodes <= run.spare_nodes:
            reason = reason + ["Owned nodes must exceed spares"]
        if reason:
            return PolicyResult(
                policy_id=policy.policy_id,
                family=policy.family,
                nodes=policy.nodes,
                configuration_id=run.configuration_id,
                status="unavailable",
                unmet_tokens=float(demand.tokens.sum()),
                warnings=reason,
            )
    service = dispatch(run, policy, demand)
    T = run.horizon_months
    K = policy.nodes
    own = policy.family == "own"
    commit = policy.family == "commit"
    if len(demand.month_hours) != T:
        raise ValueError("demand calendar must match horizon")
    H = demand.month_hours

    def monthly(values):
        return np.bincount(demand.period, weights=values, minlength=T + 1)[1:]

    baseline_exec = monthly(service["baseline_execution_hours"])
    od_exec = monthly(service["od_execution_hours"])
    billed = monthly(service["od_billed_hours"])
    active = np.arange(1, T + 1) > run.delay_months
    it = np.zeros(T)
    facility = np.zeros(T)
    categories = {}

    def add(name, period_values=None, upfront=0.0, terminal=0.0):
        arr = np.zeros(T + 1)
        arr[0] = upfront
        if period_values is not None:
            arr[1:] = period_values
        arr[-1] += terminal
        categories[name] = arr

    price = run.od_price_usd * np.where(np.arange(1, T + 1) >= 13, run.future_price_multiplier, 1.0)
    add("on_demand", price * billed)
    add(
        "variable_service",
        monthly(service["overflow_tokens"]) * run.variable_usd_million_tokens / 1e6,
    )
    obligation = 0.0
    if commit:
        obligation = K * run.commit_price_usd * H.sum()
        add(
            "commitment",
            (1 - run.prepaid_fraction) * K * run.commit_price_usd * H,
            upfront=run.prepaid_fraction * obligation,
        )
        add("commit_setup", upfront=K * run.commit_setup_usd)
        add("commit_fees", np.full(T, run.commit_fee_monthly_usd))
    if own:
        add("node_acquisition", upfront=K * run.node_acquisition_usd)
        add("installation", upfront=run.install_usd)
        add("network", upfront=run.network_usd)
        add("storage", upfront=run.storage_usd)
        add(
            "operations",
            active
            * (run.fixed_operations_annual_usd + K * run.per_node_operations_annual_usd)
            / 12,
        )
        add("precommission", (~active) * run.precommission_monthly_usd)
        it, facility = energy_kwh(
            K, H, run.idle_kw, run.load_kw, baseline_exec, run.auxiliary_kw, run.pue
        )
        it = it * active
        facility = facility * active
        if run.hosting_mode == "metered_energy":
            add("electricity", facility * run.electricity_usd_kwh)
            add(
                "hosting",
                active
                * (
                    run.space_monthly_usd
                    + run.contracted_kw * run.demand_charge_usd_kw_month
                    + run.other_site_monthly_usd
                ),
            )
        else:
            add("hosting", active * (run.all_in_colo_monthly_usd + run.other_site_monthly_usd))
        add("exit", terminal=run.exit_usd)
        add("residual", terminal=-run.residual_usd)
        if run.residual_usd > K * run.node_acquisition_usd:
            warnings.append("Residual exceeds initial node asset purchase cost")
        if (run.load_kw - run.idle_kw) * run.pue * run.electricity_usd_kwh > float(
            price.min()
        ) / run.od_availability_fraction:
            warnings.append(
                "Owned marginal energy exceeds rental cost: economic dispatch is outside the baseline-first policy family"
            )
    for item in run.ancillary:
        if item.included_in_base:
            continue
        if item.scope not in ("shared", policy.family):
            continue
        if item.mode == "per_billed_node_hour":
            value = billed * item.rate_usd
        else:
            value = np.full(T, item.rate_usd * item.quantity)
        add("ancillary:" + item.item_id, value)
    discount = discount_factors(run.discount_rate_fraction, T)
    cash = sum(categories.values())
    pv = float(cash @ discount)
    tco = float(cash.sum())
    delivered = monthly(service["baseline_tokens"] + service["overflow_tokens"])
    unmet = monthly(service["unmet_tokens"])
    total_demand = float(demand.tokens.sum())
    full = float(unmet.sum()) <= 1e-9 * total_demand
    funded = run.upfront_cash_limit_usd is None or cash[0] <= run.upfront_cash_limit_usd
    if not full:
        warnings.append("Unserved work: ineligible for full-service ranking")
    if not funded:
        warnings.append("Upfront cash limit exceeded")
    paid_hours = K * H.sum() if commit else K * H[active].sum() if own else 0.0
    available_hours = (
        K * H.sum() * run.availability_fraction
        if commit
        else (K - run.spare_nodes) * H[active].sum() * run.availability_fraction
        if own
        else 0.0
    )
    utilization = bounded_ratio(baseline_exec.sum(), paid_hours)
    available_util = bounded_ratio(baseline_exec.sum(), available_hours)
    unused = 1 - utilization if utilization is not None else None
    work_pv = float(delivered @ discount[1:])
    total_work = float(delivered.sum())
    gpu_hours = float(run.gpu_count * (baseline_exec.sum() + od_exec.sum()))
    monthly_rows = []
    block_rows = []
    cost_rows = []
    if detailed:
        for p in range(T + 1):
            monthly_rows.append(
                dict(
                    policy_id=policy.policy_id,
                    period=p,
                    month="time_zero" if p == 0 else demand.month_labels[p - 1],
                    hours=0.0 if p == 0 else float(H[p - 1]),
                    demand_tokens=0.0 if p == 0 else float(monthly(demand.tokens)[p - 1]),
                    delivered_tokens=0.0 if p == 0 else float(delivered[p - 1]),
                    unmet_tokens=0.0 if p == 0 else float(unmet[p - 1]),
                    baseline_execution_hours=0.0 if p == 0 else float(baseline_exec[p - 1]),
                    od_execution_hours=0.0 if p == 0 else float(od_exec[p - 1]),
                    od_billed_hours=0.0 if p == 0 else float(billed[p - 1]),
                    baseline_nodes=K,
                    idle_node_hours=0.0
                    if p == 0
                    else float(max(0, K * H[p - 1] - baseline_exec[p - 1]))
                    if (commit or (own and active[p - 1]))
                    else 0.0,
                    it_kwh=0.0 if p == 0 else float(it[p - 1]),
                    facility_kwh=0.0 if p == 0 else float(facility[p - 1]),
                    discount_factor=float(discount[p]),
                    cash_usd=float(cash[p]),
                    pv_usd=float(cash[p] * discount[p]),
                    **{c + "_usd": float(v[p]) for c, v in categories.items()},
                )
            )
        for i in range(len(demand.tokens)):
            block_rows.append(
                dict(
                    policy_id=policy.policy_id,
                    period=int(demand.period[i]),
                    block=int(demand.block[i]),
                    duration_hours=float(demand.hours[i]),
                    demand_tokens=float(demand.tokens[i]),
                    **{k: float(v[i]) for k, v in service.items()},
                )
            )
        for category, values in categories.items():
            for p, value in enumerate(values):
                kind = (
                    "terminal"
                    if category in ["exit", "residual"]
                    else "capital"
                    if p == 0
                    else "operating"
                )
                cost_rows.append(
                    dict(
                        policy_id=policy.policy_id,
                        period=p,
                        category=category,
                        flow_kind=kind,
                        cash_usd=float(value),
                        pv_usd=float(value * discount[p]),
                    )
                )
    return PolicyResult(
        policy_id=policy.policy_id,
        family=policy.family,
        nodes=K,
        configuration_id=run.configuration_id,
        status="conditional" if full and funded else "ineligible",
        pv_cost_usd=pv,
        tco_usd=tco,
        upfront_usd=float(cash[0]),
        obligation_usd=float(obligation),
        delivered_tokens=total_work,
        unmet_tokens=float(unmet.sum()),
        service_fraction=bounded_ratio(total_work, total_demand),
        execution_utilization=utilization,
        available_utilization=available_util,
        unused_paid_share=unused,
        unused_commitment_usd=float(obligation * unused) if commit and unused is not None else None,
        levelized_usd_million_tokens=1e6 * pv / work_pv if work_pv else None,
        undiscounted_usd_million_tokens=1e6 * tco / total_work if total_work else None,
        effective_gpu_hours=gpu_hours,
        billed_rental_gpu_hours=float(run.gpu_count * billed.sum()),
        owned_calendar_gpu_hours=float(run.gpu_count * K * H.sum()) if own else 0.0,
        effective_gpu_hour_cost_usd=tco / gpu_hours if gpu_hours else None,
        monthly_ledger=monthly_rows,
        block_ledger=block_rows,
        cost_ledger=cost_rows,
        category_pv_usd={c: float(v @ discount) for c, v in categories.items()},
        warnings=warnings,
        source_dependencies=[e.input_id for e in run.evidence],
    )
