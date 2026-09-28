import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from compute_economics.ui.charts import capacity_chart, finish, policy_label
from compute_economics.ui.common import policy_picker, show_chart


def stress_table(paths):
    rows = []
    for path, p in paths.items():
        rows.append(
            {
                "Demand path": path.replace("_", " ").title(),
                "Fixed policy": policy_label(p["fixed_policy_id"]),
                "Nodes": p["fixed_nodes"],
                "Full service": p["feasible"],
                "PV cost (USD)": p["fixed_pv_usd"],
                "Regret (USD)": p["regret_usd"],
                "Unmet tokens": p["unmet_tokens"],
                "In practical tie": p["in_tie_set"],
                "Hindsight optimum": policy_label(p["scenario_optimum"]),
            }
        )
    frame = pd.DataFrame(rows)
    for column in ["PV cost (USD)", "Regret (USD)"]:
        frame[column] = pd.to_numeric(frame[column]).round(-3)
    st.dataframe(
        frame.style.format(
            {
                **{name: "${:,.0f}" for name in ["PV cost (USD)", "Regret (USD)"]},
                "Unmet tokens": "{:,.0f}",
            },
            na_rep="Unavailable",
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Costs rounded to the nearest $1,000. Unavailable regret is blank; full precision remains in exports."
    )


def render(bundle):
    a = bundle.analysis
    st.caption("03 / RISK & CAPACITY · FIXED FLEET, CHANGING DEMAND")
    st.header("Does the plan still work?")
    stress = a["fixed_policy_demand_stress"]
    if stress:
        st.write(
            f"Stress policy: **{policy_label(stress['fixed_policy_id'])}**. Its node count stays fixed in every path. Scenario optima are hindsight references used to calculate regret."
        )
        stress_table(stress["paths"])
        st.caption(
            "Regret is unavailable when the fixed policy cannot deliver full service; unmet work remains visible instead."
        )
    else:
        st.warning(
            "No feasible selected policy. Risk and regret are unavailable until required evidence or service capacity is supplied."
        )
    selected = policy_picker(bundle, "capacity_policy")
    block = bundle.table("block_ledger.csv")
    p = next(p for p in a["policies"] if p["policy_id"] == selected)
    if block.empty or not (block.policy_id == selected).any():
        st.info("Capacity ledger unavailable: " + "; ".join(p["warnings"]))
    else:
        show_chart(capacity_chart(block[block.policy_id == selected]), "capacity_service")
        cols = st.columns(3)
        cols[0].metric("Unmet output tokens", f"{p['unmet_tokens']:,.0f}")
        cols[1].metric(
            "Execution / paid-calendar hours",
            "Undefined"
            if p["execution_utilization"] is None
            else f"{p['execution_utilization']:.1%}",
        )
        cols[2].metric(
            "Execution / available hours",
            "Undefined"
            if p["available_utilization"] is None
            else f"{p['available_utilization']:.1%}",
        )
        st.caption(
            "Availability reduces productive capacity. Utilization measures realized execution. Spare nodes remain paid and powered; shortages are never stacked as delivered output."
        )
        with st.expander("Block-level billing and capacity"):
            st.dataframe(block[block.policy_id == selected], hide_index=True, width="stretch")
    st.subheader("Sensitivity of the fixed policy")
    sensitivity = a["sensitivities"]
    rows = []
    for name, test in sensitivity["one_at_a_time"].items():
        rows += [dict(assumption=name, **p) for p in test["points"]]
    frame = pd.DataFrame(rows)
    if not frame.empty:
        fig = go.Figure()
        for name, test in sensitivity["one_at_a_time"].items():
            points = [p for p in test["points"] if p["fixed_pv_usd"] is not None]
            if points:
                fig.add_trace(
                    go.Scatter(
                        x=[p["fixed_pv_usd"] for p in points],
                        y=[name.replace("_", " ")] * len(points),
                        mode="lines+markers",
                        name=name,
                        showlegend=False,
                        customdata=[p["value"] for p in points],
                        hovertemplate="Tested value: %{customdata}<br>Fixed-policy PV: %{x:$,.0f}<extra></extra>",
                        line_color="#087F72",
                    )
                )
        show_chart(
            finish(
                fig,
                "Fixed-policy cost at disclosed sensitivity points",
                "Present-value cost · USD",
                "Assumption",
                390,
            ),
            "sensitivity_fixed",
        )
        st.caption(
            sensitivity["influence_definition"]
            + " Fleet size is fixed here; the decision surface separately reoptimizes it."
        )
        with st.expander("Sensitivity values and reoptimized outcomes"):
            st.dataframe(frame, hide_index=True, width="stretch")
    with st.expander("Named adverse cases", expanded=True):
        for name, test in a["named_stresses"].items():
            st.markdown("**" + name.replace("_", " ").title() + "**")
            stress_table(test["paths"])
