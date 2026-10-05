import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from compute_economics.catalog import build_catalog, query_catalog
from compute_economics.reporting import EXCLUSIONS
from compute_economics.ui.presentation import MISSING_EVIDENCE, display_table, label, number_text
from compute_economics.ui.service import DATA
from compute_economics.validation import read_table, validate_run


@st.cache_data(show_spinner=False)
def public_catalog():
    # Cache only public immutable query results. No connection or user data is shared.
    with tempfile.TemporaryDirectory(prefix="compute-ui-catalog-") as directory:
        db = Path(directory) / "catalog.duckdb"
        build_catalog(DATA, db)
        coverage = query_catalog(
            db,
            "evidence_coverage",
            {"region": "North America", "workload": "gpt-oss-120b-v6.1-offline"},
        )
    return {
        name: read_table(DATA, name)
        for name in ["sources", "offers", "benchmarks", "compatibility"]
    } | {"coverage": coverage}


def render(bundle):
    st.header("What is known. What is assumed.")
    st.write(
        "Observed means published by the source, not independently measured in production. Derived means calculated from named parents. Model and user assumptions remain distinct. Unavailable is null, never zero."
    )
    report = validate_run(bundle.run)
    cols = st.columns(3)
    cols[0].metric("Snapshot", bundle.run.data_snapshot_id)
    cols[1].metric("Review as of", bundle.run.analysis_as_of.isoformat())
    cols[2].metric("Preserved overrides", len(bundle.run.override_history))
    st.caption(
        "Historical snapshot. These are saved source ages as of the run’s review date, not a claim that live prices or inventory are current."
    )
    st.subheader("Input provenance")
    records = []
    for e in bundle.run.evidence + bundle.run.override_history:
        records.append(
            {
                "Input": label(e.input_id),
                "Input ID": e.input_id,
                "Value": "Unavailable" if e.value is None else number_text(e.value),
                "Unit": e.unit,
                "Evidence class": label(e.evidence_class),
                "Source": e.source_url,
                "Locator": e.source_locator,
                "Observed UTC": str(e.observed_at_utc or "Not applicable"),
                "Freshness": report.source_freshness.get(e.input_id, "Assumption / not applicable"),
                "Rationale": e.rationale or e.confidence_note,
                "Original parents": ", ".join(e.parent_input_ids),
                "Limits": e.limitations,
                "Artifact SHA-256": e.raw_artifact_sha256,
            }
        )
    kind = st.multiselect(
        "Evidence classes",
        ["observed", "derived", "analyst_assumption", "user_assumption", "unavailable"],
        default=["observed", "derived", "analyst_assumption", "user_assumption", "unavailable"],
        key="evidence_classes",
        format_func=label,
    )
    frame = pd.DataFrame(records)
    st.dataframe(
        frame[frame["Evidence class"].isin([label(k) for k in kind])],
        hide_index=True,
        width="stretch",
        column_config={"Source": st.column_config.LinkColumn("Source")},
    )
    st.subheader("Material missing evidence")
    for item in MISSING_EVIDENCE:
        st.write("• " + item)
    catalog = public_catalog()
    with st.expander("Source catalog and dates"):
        display_table(pd.DataFrame(catalog["sources"]))
        display_table(pd.DataFrame(catalog["offers"]).replace("", "Unavailable / not applicable"))
    with st.expander("Benchmark compatibility and reference anchors"):
        st.write(
            "gpt-oss-120b is primary. Llama 2 70B 99.9 Offline is secondary historical validation. Exact model, dataset, quality, runtime, precision and topology must match the admitted reference; production transfer remains assumed."
        )
        display_table(pd.DataFrame(catalog["benchmarks"]))
        display_table(pd.DataFrame(catalog["compatibility"]))
        display_table(pd.DataFrame(catalog["coverage"]))
    with st.expander("Methodology, units and exclusions", expanded=True):
        st.write(EXCLUSIONS)
        st.write(
            "The engine uses actual UTC calendar months, whole-node baseline-first dispatch, bounded rental overflow and end-month cash flows. NPV and delivered work use matching discount factors. Terminal proceeds appear once. Fixed-policy stresses never resize the fleet."
        )
        st.write(
            "Practical ties are within 1% of the lowest feasible present-value cost. A result is stable only when the selected policy is feasible and in the tie set across all three tested demand paths. These are deterministic tests, not forecast probabilities."
        )
        st.write(
            "Evidence freshness review thresholds: 30 days for offers, 180 for benchmarks/configurations/contracts, and 400 for annual disclosures. A historical snapshot is never labeled a current quote."
        )
        st.code(
            f"Schema {bundle.run.schema_version}\nModel {bundle.run.model_version}\nRun {bundle.envelope['run_hash']}",
            language=None,
        )
