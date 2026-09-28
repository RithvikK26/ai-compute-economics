"""Package 8 entry point: session-local controls and presentation only."""

import streamlit as st

from compute_economics.reporting import safe_text
from compute_economics.ui import decision, economics_view, evidence, risk
from compute_economics.ui.controls import publish, sidebar
from compute_economics.ui.service import compute_preset

st.set_page_config(
    page_title="Compute Economics | Decision Workbench", page_icon="◈", layout="wide"
)
st.markdown(
    """<style>
.block-container {max-width:1280px;padding-top:4.5rem;padding-bottom:3rem;}
 .block-container h1, .block-container h2, .block-container h3 {letter-spacing:-0.035em;} .block-container h1 {font-weight:650;font-size:2rem;line-height:1.25;}
.block-container h2 {font-size:1.65rem;}
[data-testid="stMetric"] {background:white;border:1px solid #DFE6EA;border-radius:9px;padding:16px 20px;}
[data-testid="stMetricValue"] {font-size:clamp(1rem, 1.8vw, 1.65rem);}
[data-testid="stMetricLabel"] p {white-space:normal;}
@media (max-width:1100px) { [data-testid="stMetric"] {padding:12px 8px;} }
[data-testid="stSidebar"] {border-right:1px solid #DFE6EA;}
[data-testid="stCaptionContainer"] {color:#516778;}
</style>""",
    unsafe_allow_html=True,
)
if "completed" not in st.session_state:
    with st.spinner("Preparing the frozen example and decision frontier…"):
        publish(compute_preset("Stable demand"))
bundle = st.session_state["completed"]
sidebar(bundle)
st.caption("COMPUTE ECONOMICS / CAPACITY SOURCING")
st.title("A decision, with its boundaries.")
st.caption(
    f"{bundle.run.workload.model} · MLPerf v6.1 Offline · {bundle.run.configuration_id} · {bundle.run.horizon_months} calendar months · USD"
)
st.caption(
    "Illustrative scenario using public reference data and analyst assumptions. Benchmark performance is not production throughput."
)
view = st.radio(
    "View",
    ["Decision", "Economics", "Risk & Capacity", "Evidence & Methodology"],
    horizontal=True,
    key="view",
    label_visibility="collapsed",
)
if st.session_state.get("input_error"):
    st.error(
        "Input not applied. The last completed result is retained.\n\n"
        + st.session_state["input_error"]
    )
st.caption(
    f"Completed scenario: {safe_text(bundle.run.scenario_id)} · run {bundle.envelope['run_hash'][:12]} · controls are drafts until submitted"
)
{
    "Decision": decision.render,
    "Economics": economics_view.render,
    "Risk & Capacity": risk.render,
    "Evidence & Methodology": evidence.render,
}[view](bundle)
# Errors raised by a form rendered in the current view should be visible immediately.
if st.session_state.get("input_error"):
    st.error(st.session_state["input_error"])
with st.expander("Export current run"):
    st.caption(
        "Downloads contain the last completed run, never unsaved controls. JSON includes source checksums and overrides; ledgers retain full numerical precision."
    )
    columns = st.columns(3)
    for i, (name, label, mime) in enumerate(
        [
            ("scenario.json", "Reproducible scenario · JSON", "application/json"),
            ("monthly_ledger.csv", "Monthly ledger · CSV", "text/csv"),
            ("decision_memo.md", "Decision memo · Markdown", "text/markdown"),
            ("block_ledger.csv", "Capacity and billing · CSV", "text/csv"),
            ("decision_surface.csv", "Decision surface · CSV", "text/csv"),
            ("provenance.csv", "Provenance · CSV", "text/csv"),
        ]
    ):
        columns[i % 3].download_button(
            label,
            bundle.files[name],
            file_name=name,
            mime=mime,
            key="download:" + name,
            on_click="ignore",
        )
    st.download_button(
        "All results and audit files · ZIP",
        bundle.zip_bytes(),
        file_name="compute-economics-run.zip",
        mime="application/zip",
        key="download:zip",
        on_click="ignore",
    )
