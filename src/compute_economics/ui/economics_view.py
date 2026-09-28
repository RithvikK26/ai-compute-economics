import streamlit as st

from compute_economics.ui.charts import cash_chart, cost_chart, policy_label
from compute_economics.ui.common import dollars, policy_picker, show_chart
from compute_economics.ui.controls import economics_form


def render(bundle):
    st.caption("02 / ECONOMICS · CASH TIMING AND COST BOUNDARY")
    st.header("What must be funded, and when")
    selected = policy_picker(bundle, "economics_policy")
    result = next(p for p in bundle.analysis["policies"] if p["policy_id"] == selected)
    cols = st.columns(3)
    cols[0].metric("Undiscounted TCO", dollars(result["tco_usd"]))
    cols[1].metric("Upfront cash", dollars(result["upfront_usd"]))
    cols[2].metric("Nominal commitment obligation", dollars(result["obligation_usd"]))
    frame = bundle.table("monthly_ledger.csv")
    if frame.empty or not (frame.policy_id == selected).any():
        st.warning("Ledger unavailable for this policy: " + "; ".join(result["warnings"]))
    else:
        selected_frame = frame[frame.policy_id == selected]
        show_chart(cash_chart(selected_frame), "cashflow")
        st.caption(
            "Month 0 is upfront. Operating payments occur at month end; terminal sale proceeds are negative cash flow. No depreciation, debt interest or tax expense is added."
        )
        comparison = st.multiselect(
            "Compare cost composition",
            [p["policy_id"] for p in bundle.analysis["policies"]],
            default=list(dict.fromkeys([selected, "on_demand:0"])),
            format_func=policy_label,
            key="cost_comparison",
        )
        show_chart(
            cost_chart([p for p in bundle.analysis["policies"] if p["policy_id"] in comparison]),
            "cost_components",
        )
        with st.expander("Monthly and annual ledgers"):
            st.dataframe(selected_frame, hide_index=True, width="stretch")
            annual = bundle.table("annual_costs.csv")
            st.dataframe(annual[annual.policy_id == selected], hide_index=True, width="stretch")
            st.caption(
                "Annual operating cash is separate from total cash. Year one includes time-zero investment. Complete ledgers for every policy are available under Export current run."
            )
    unit = result["levelized_usd_million_tokens"]
    st.caption(
        "Levelized cost per million output tokens for the specified input/output workload: "
        + ("undefined / unavailable" if unit is None else f"${unit:.6f}")
        + ". Not a universal token price."
    )
    economics_form(bundle)
