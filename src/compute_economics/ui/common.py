import pandas as pd
import streamlit as st

from compute_economics.ui.charts import policy_label


def dollars(value):
    if value is None:
        return "Unavailable"
    return f"${round(value / 1000) * 1000:,.0f}" if abs(value) >= 1000 else f"${value:,.2f}"


def show_chart(fig, key):
    if fig is None:
        st.info("Unavailable: this view needs a complete eligible cost/performance input.")
    else:
        st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})


def policy_table(bundle):
    comparison = bundle.analysis["comparison"]
    rows = []
    for p in bundle.analysis["policies"]:
        rows.append(
            {
                "Policy": policy_label(p["policy_id"]),
                "Configuration": p["configuration_id"],
                "Status": p["status"],
                "Nodes": p["nodes"],
                "PV cost (USD)": p["pv_cost_usd"],
                "Savings vs full-service OD (USD)": comparison["savings_vs_od_usd"][p["policy_id"]],
                "Upfront (USD)": p["upfront_usd"],
                "Obligation (USD)": p["obligation_usd"],
                "Unused-paid share (%)": (
                    None if p["unused_paid_share"] is None else p["unused_paid_share"] * 100
                ),
                "Unmet tokens": p["unmet_tokens"],
                "Practical tie": p["policy_id"] in comparison["tie_set"],
            }
        )
    frame = pd.DataFrame(rows)
    money_columns = [name for name in frame.columns if "(USD)" in name]
    frame[money_columns] = frame[money_columns].round(-3)
    st.caption(
        "Displayed costs rounded to the nearest $1,000; audit exports retain full precision."
    )
    st.dataframe(
        frame.style.format(
            {**{name: "${:,.0f}" for name in money_columns}, "Unmet tokens": "{:,.0f}"},
            na_rep="Unavailable",
        ),
        hide_index=True,
        width="stretch",
        column_config={
            "Unused-paid share (%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )


def policy_picker(bundle, key):
    ids = [p["policy_id"] for p in bundle.analysis["policies"]]
    selected = bundle.analysis["selected_policy_id"]
    return st.selectbox(
        "Inspect a fixed policy",
        ids,
        index=ids.index(selected) if selected in ids else 0,
        format_func=policy_label,
        key=key,
    )
