"""Human-readable views of engine values; never used to calculate or export a run."""

import math
import re
from numbers import Real

import streamlit as st

from compute_economics.reporting import MISSING_EVIDENCE as ENGINE_LIMITATIONS

B300_LIMITATION = (
    "Public B300 on-demand pricing is unavailable in the frozen source snapshot; "
    "spot pricing is not modeled."
)
MISSING_EVIDENCE = [
    B300_LIMITATION if item.startswith("B300 on-demand price") else item
    for item in ENGINE_LIMITATIONS
]
LABELS = {
    "stable_demand": "Stable demand",
    "demand_disappointment": "Demand disappointment",
    "delayed_capacity": "Delayed capacity",
    "acquisition_cost": "Hardware acquisition cost",
    "acquisition_cost_multiplier": "Hardware acquisition cost multiplier",
    "transfer_factor": "Benchmark-to-production transfer factor",
    "transfer_fraction": "Benchmark-to-production transfer factor",
    "od_transfer_fraction": "Rental benchmark-to-production transfer factor",
    "rental_future_price": "Future rental price",
    "commitment_price": "Commitment price",
    "commitment_price_usd_node_hour": "Commitment price (USD/node-hour)",
    "discount_rate": "Annual discount rate",
    "electricity": "Electricity price",
    "residual": "Terminal proceeds",
    "demand": "Demand",
    "value": "Tested value",
    "from": "Preferred policy before",
    "to": "Preferred policy after",
    "bracket": "Tested interval",
    "fixed_policy_utilization_bracket": "Fixed-capacity utilization",
    "fixed_unmet_tokens": "Unserved workload (output tokens)",
    "reoptimized_winner": "Lowest-cost feasible policy after reoptimization",
    "fixed_policy_unmet_tokens": "Unserved workload (output tokens)",
    "fixed_policy_pv_usd": "Fixed-policy present-value cost (USD)",
    "fixed_pv_usd": "Fixed-policy present-value cost (USD)",
    "advantage_vs_best_alternative_usd": "Advantage over best alternative (USD)",
    "winner": "Lowest-cost feasible policy",
    "tie_set": "Practical tie set",
    "policy_id": "Policy",
    "fixed_policy_id": "Fixed policy",
    "configuration_id": "Configuration",
    "lowest_pv_usd": "Lowest present-value cost (USD)",
    "pv_usd": "Present-value cost (USD)",
    "cash_usd": "Cash flow (USD)",
    "operating_cash_usd": "Operating cash flow (USD)",
    "unmet_tokens": "Unserved workload (output tokens)",
    "od_nodes": "On-demand nodes",
    "od_execution_hours": "On-demand execution (node-hours)",
    "od_billed_hours": "On-demand billed time (node-hours)",
    "od_required_hours": "On-demand required time (node-hours)",
    "baseline_execution_hours": "Baseline execution (node-hours)",
    "node_acquisition_usd": "Hardware acquisition cost (USD)",
    "node_hour_price": "Price (USD/node-hour)",
    "analyst_assumption": "Model assumption",
    "user_assumption": "User assumption",
    "metered_energy": "Metered energy",
    "all_in_colo": "All-in colocation",
    "on_demand": "On-demand",
    "node_acquisition": "Hardware acquisition",
    "precommission": "Before commissioning",
    "commit_setup": "Commitment setup",
    "commit_fees": "Commitment fees",
    "url": "Source URL",
    "artifact_hash": "Artifact SHA-256",
}


def label(value):
    value = str(value)
    if value in LABELS:
        return LABELS[value]
    # Preserve user text and audit identifiers; only field-style names are humanized.
    if not re.fullmatch(r"[a-z][a-z0-9_]*", value):
        return value
    words = value.replace("_", " ").capitalize()
    for raw, pretty in [
        ("usd", "USD"),
        ("gpu", "GPU"),
        ("kwh", "kWh"),
        ("kw", "kW"),
        ("it", "IT"),
        ("id", "ID"),
        ("pv", "PV"),
        ("od", "on-demand"),
    ]:
        words = re.sub(rf"\b{raw}\b", pretty, words, flags=re.IGNORECASE)
    return words


def configuration_label(value):
    return {"cw-b200-8": "CoreWeave B200 · 8 GPUs", "cw-b300-8": "CoreWeave B300 · 8 GPUs"}.get(
        value, value
    )


def number_text(value):
    if value is None or (isinstance(value, Real) and not math.isfinite(value)):
        return "Unavailable"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Real):
        if 0 < abs(value) < 0.001:
            return f"{value:.3g}"
        # Three decimal places retain the 0.025 acquisition-bracket spacing.
        return f"{value:,.3f}".rstrip("0").rstrip(".") if value % 1 else f"{value:,.0f}"
    return str(value)


def assumption_value(name, value):
    if value is None:
        return "Unavailable"
    if name in {"transfer_factor", "discount_rate", "residual"}:
        return f"{value:.1%}"
    if name == "commitment_price":
        return f"${value:,.2f}/node-hour"
    if name == "electricity":
        return f"${value:.2f}/kWh"
    return f"{value:.2f}×"


def display_table(frame, axis=None):
    """Format a detached table; original frames, analysis and export bytes stay intact."""
    from compute_economics.ui.charts import policy_label

    if frame.empty:
        st.caption("No results for this selection.")
        return
    shown = frame.copy(deep=True)
    for column in shown.columns:

        def cell(value, column=column):
            if value is None or (isinstance(value, Real) and not math.isfinite(value)):
                return "Unavailable"
            if isinstance(value, (list, tuple)):
                if column == "tie_set":
                    return ", ".join(policy_label(v) for v in value) or "None"
                if "utilization" in column:
                    return "–".join("Unavailable" if v is None else f"{v:.1%}" for v in value)
                unit = " USD/node-hour" if axis == "commitment_price_usd_node_hour" else "×"
                return "–".join(number_text(v) for v in value) + (
                    unit if column == "bracket" else ""
                )
            if isinstance(value, str):
                if column == "month" and value == "time_zero":
                    return "Upfront"
                if re.fullmatch(r"(?:own|commit|on_demand):\d+", value):
                    return policy_label(value)
                if column == "configuration_id":
                    return configuration_label(value)
                if column in {
                    "assumption",
                    "category",
                    "evidence_class",
                    "pricing_kind",
                    "match_level",
                    "admission_status",
                }:
                    return label(value)
                return value
            if isinstance(value, Real) and not isinstance(value, bool):
                if (
                    "utilization" in column
                    or column.endswith("_fraction")
                    or column == "unused_paid_share"
                ):
                    return f"{value:.1%}"
                if column.endswith("_usd"):
                    return f"${value:,.2f}"
                if "tokens" in column or column in {"nodes", "period", "model_year"}:
                    return f"{value:,.0f}"
                return number_text(value)
            return value

        if column == "value" and "assumption" in frame:
            shown[column] = [assumption_value(n, v) for n, v in zip(frame.assumption, frame.value)]
        else:
            shown[column] = shown[column].map(cell)
    shown = shown.rename(columns=label)
    config = (
        {"Source URL": st.column_config.LinkColumn("Source URL")} if "Source URL" in shown else None
    )
    st.dataframe(shown, hide_index=True, width="stretch", column_config=config)
