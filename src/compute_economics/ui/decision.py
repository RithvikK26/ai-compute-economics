import pandas as pd
import streamlit as st

from compute_economics.reporting import MISSING_EVIDENCE
from compute_economics.ui.charts import frontier_chart, policy_label, surface_chart
from compute_economics.ui.common import dollars, policy_table, show_chart


def render(bundle):
    a = bundle.analysis
    c = a["comparison"]
    risk = a["fixed_policy_demand_stress"]
    s = a["sensitivities"]
    st.caption("01 / DECISION · CONDITIONAL, WITHIN THE TESTED POLICY FAMILY")
    st.header("Where the decision changes")
    if c["winner"]:
        st.markdown(
            f"### Under the selected assumptions, **{policy_label(c['winner'])}** has the lowest modeled cost."
        )
        if bundle.run.demand_disappointment:
            st.warning(
                f"Hindsight comparison only. The time-zero policy remains {policy_label(a['selected_policy_id'])}; the fleet is not resized after demand falls."
            )
        cols = st.columns(3)
        winner = next(p for p in a["policies"] if p["policy_id"] == c["winner"])
        cols[0].metric("Lowest present-value cost", dollars(c["lowest_pv_usd"]))
        cols[1].metric("Upfront cash", dollars(winner["upfront_usd"]))
        cols[2].metric(
            "Demand-path stability",
            "Stable" if risk and risk["stable_across_tested_demand_paths"] else "Not stable",
        )
        st.caption(
            "Practical tie set · within 1% of the minimum: "
            + ", ".join(policy_label(p) for p in c["tie_set"])
        )
    else:
        st.warning(
            c["message"]
            + ". Review missing inputs and service gaps below; unavailable values are not zero."
        )
    st.info("Decision-limiting evidence: " + MISSING_EVIDENCE[0])
    show_chart(surface_chart(a), "decision_surface")
    st.caption(
        "20 × 20 tested scenarios · color identifies the sourcing family; hover shows fleet size, cost and ties. White borders separate tested cells with different winning fleets; they are not exact thresholds. Each cell reoptimizes K. A fleet-size switch is distinct from a change in sourcing family."
    )
    left, right = st.columns(2)
    with left:
        st.markdown("**Demand and utilization threshold**")
        switches = a["frontier"]["demand"]["winner_switch_intervals"]
        nearby = sorted(switches, key=lambda x: abs(sum(x["bracket"]) / 2 - 1))
        if nearby:
            p = nearby[0]
            lo, hi = p["bracket"]
            st.write(
                f"The decision changes within the tested {lo:g}–{hi:g}× demand bracket: {policy_label(p['from'])} → {policy_label(p['to'])}."
            )
            u = p["fixed_policy_utilization_bracket"]
            if all(v is not None for v in u):
                st.caption(f"Selected fixed-policy execution utilization: {u[0]:.1%}–{u[1]:.1%}.")
        else:
            st.write(
                "No crossing in the tested demand range (0.25–2.0×), or insufficient feasible evidence."
            )
    with right:
        st.markdown("**Acquisition and commitment thresholds**")
        for axis, label in [
            ("acquisition_cost_multiplier", "Acquisition"),
            ("commitment_price_usd_node_hour", "Commitment"),
        ]:
            f = a["frontier"][axis]
            cross = f["winner_switch_intervals"]
            if cross:
                p = min(
                    cross,
                    key=lambda x: abs(
                        sum(x["bracket"]) / 2
                        - (1 if label == "Acquisition" else bundle.run.commit_price_usd or 40)
                    ),
                )
                lo, hi = p["bracket"]
                unit = "× node acquisition" if label == "Acquisition" else "USD/node-hour"
                st.write(
                    f"{label}: {lo:g}–{hi:g} {unit}; {policy_label(p['from'])} → {policy_label(p['to'])}."
                )
            else:
                st.write(f"{label}: {f['status']}.")
    st.caption(
        "Thresholds are tested brackets, not interpolated roots; whole-node and billing discontinuities remain visible."
    )
    st.markdown(
        "**Most influential tested assumption:** "
        + str(s["most_influential_tested_assumption"] or "Unavailable").replace("_", " ")
    )
    reversals = s["tested_reversals"]
    if reversals:
        p = reversals[0]
        st.write(
            f"Tested reversal: {p['assumption'].replace('_', ' ')} = {p['value']:g} moves the preferred policy to {policy_label(p['winner'])}."
        )
    else:
        st.write(
            "No reversal in the disclosed one-at-a-time tests, or insufficient feasible evidence."
        )
    with st.expander("Explore every crossing and reversal"):
        axis = st.selectbox(
            "Frontier axis",
            list(a["frontier"]),
            format_func=lambda x: x.replace("_", " ").title(),
            key="frontier_axis",
        )
        show_chart(frontier_chart(a, axis), "frontier_line")
        st.caption(
            "Lines connect tested points for orientation; only the reported adjacent brackets establish switches. Missing data are gaps."
        )
        st.dataframe(pd.DataFrame(a["frontier"][axis]["winner_switch_intervals"]), hide_index=True)
        st.dataframe(pd.DataFrame(reversals), hide_index=True)
        st.caption(s["influence_definition"])
    st.subheader("Policy comparison")
    st.caption(
        "Conditional on compatible performance and assumed capacity. Infeasible and unavailable policies never enter the minimum or tie set."
    )
    policy_table(bundle)
    with st.expander("Warnings and the evidence needed next"):
        for item in MISSING_EVIDENCE:
            st.write("• " + item)
        for warning in c["warnings"]:
            st.write("• " + warning)
        for p in a["policies"]:
            if p["warnings"]:
                st.caption(policy_label(p["policy_id"]) + ": " + "; ".join(p["warnings"]))
