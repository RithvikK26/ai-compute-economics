"""Application acceptance: real AppTest runs against the stable engine."""

import hashlib
import json
import socket
import zipfile
from dataclasses import replace
from io import BytesIO

import pytest
from streamlit.testing.v1 import AppTest

from compute_economics.reporting import digest, load_run, safe_text
from compute_economics.ui.service import DATA, ROOT, compute_bytes


def app():
    result = AppTest.from_file(ROOT / "app.py", default_timeout=90).run()
    assert not result.exception
    return result


def input_by_label(at, kind, label):
    return next(x for x in getattr(at, kind) if x.label == label)


def click(at, label):
    input_by_label(at, "button", label).click().run(timeout=90)
    assert not at.exception
    return at


def all_text(at):
    return "\n".join(
        x.value
        for kind in ["markdown", "caption", "info", "warning", "error"]
        for x in getattr(at, kind)
    )


@pytest.mark.parametrize(
    "preset,scenario,winner,selected",
    [
        ("Stable demand", "stable_demand", "own:6", "own:6"),
        ("Demand disappointment", "demand_disappointment", "own:5", "own:6"),
        ("Delayed capacity", "delayed_capacity", "commit:7", "commit:7"),
    ],
)
def test_required_presets(preset, scenario, winner, selected):
    at = app()
    at.selectbox(key="preset").select(preset)
    click(at, "Load preset")
    bundle = at.session_state["completed"]
    assert bundle.run.scenario_id == scenario
    assert bundle.analysis["comparison"]["winner"] == winner
    assert bundle.analysis["selected_policy_id"] == selected
    assert "Under the selected assumptions" in all_text(at)
    if preset == "Demand disappointment":
        assert "fleet is not resized" in all_text(at)


def test_all_four_views_and_evidence(monkeypatch):
    attempted = []

    def deny_network(*args, **kwargs):
        attempted.append(True)
        raise AssertionError("Offline app attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    at = app()
    counts = {}
    for view in ["Decision", "Economics", "Risk & Capacity", "Evidence & Methodology"]:
        at.radio(key="view").set_value(view).run(timeout=90)
        assert not at.exception
        counts[view] = len(at.get("plotly_chart"))
        assert len(at.download_button) == 7
    assert not attempted, "All four views must render without network access"
    assert counts["Decision"] == 2
    assert counts["Economics"] == 2
    assert counts["Risk & Capacity"] == 2
    assert "Observed means published" in all_text(at)
    assert "Unavailable is null, never zero" in all_text(at)
    assert "99% of 83.13%" in str(at.session_state["completed"].run.workload.quality)
    assert any("Artifact SHA-256" in x.value.columns for x in at.dataframe)
    assert any(
        "contact sales" in str(x.value).lower() or "Contact sales" in x.value.to_string()
        for x in at.dataframe
    )


def test_frontier_spec_and_threshold_visibility():
    at = app()
    text = all_text(at)
    for label in [
        "Demand and utilization threshold",
        "Acquisition and commitment thresholds",
        "Most influential tested assumption",
        "Practical tie set",
        "Key limitation",
        "Tested reversal",
    ]:
        assert label in text
    charts = at.get("plotly_chart")
    fig = json.loads(charts[0].proto.spec)
    heatmap = fig["data"][0]
    assert heatmap["type"] == "heatmap"
    assert len(heatmap["z"]) == 20 and len(heatmap["z"][0]) == 20
    assert any(t.get("name") == "Tested fleet boundaries" and t["x"] for t in fig["data"])
    assert "customdata" in heatmap
    assert "Demand multiplier" in fig["layout"]["xaxis"]["title"]["text"]
    assert any(
        m.label == "Demand-path stability" and m.value == "Varies by scenario" for m in at.metric
    )


def test_invalid_edit_keeps_previous_result_and_downloads():
    at = app()
    before = at.session_state["completed"]
    old_hash = before.envelope["run_hash"]
    input_by_label(at, "number_input", "Baseline throughput transfer (0–1)").set_value(1.2)
    # A widget rerun alone cannot calculate or replace exports.
    at.run()
    assert at.session_state["completed"].envelope["run_hash"] == old_hash
    click(at, "Run scenario")
    assert any("Benchmark-to-production transfer factor" in e.value for e in at.error)
    assert at.session_state["completed"].envelope["run_hash"] == old_hash
    assert at.session_state["completed"].files["scenario.json"] == before.files["scenario.json"]
    input_by_label(at, "number_input", "Baseline throughput transfer (0–1)").set_value(0.65)
    click(at, "Run scenario")
    assert not at.error and at.session_state["completed"].envelope["run_hash"] != old_hash


def test_missing_b300_price_has_no_fallback():
    at = app()
    input_by_label(at, "selectbox", "Configuration").select("cw-b300-8")
    click(at, "Run scenario")
    bundle = at.session_state["completed"]
    assert bundle.run.od_price_usd is None
    assert bundle.run.workload.performance_tokens_s == 112840.0
    assert bundle.analysis["comparison"]["winner"] is None
    assert all(
        p["status"] == "unavailable" and p["pv_cost_usd"] is None
        for p in bundle.analysis["policies"]
    )
    assert "unavailable values are not zero" in all_text(at)
    assert len(at.download_button) == 7
    at.radio(key="view").set_value("Economics").run()
    assert not at.exception
    assert "Ledger unavailable" in all_text(at)
    at.radio(key="view").set_value("Risk & Capacity").run()
    assert not at.exception
    assert "Risk and regret are unavailable" in all_text(at)


def test_infeasible_owned_capacity_is_visible():
    at = app()
    at.selectbox(key="preset").select("Delayed capacity")
    click(at, "Load preset")
    at.radio(key="view").set_value("Risk & Capacity").run()
    at.selectbox(key="capacity_policy").select("own:6").run()
    assert not at.exception
    assert any(
        m.label == "Unmet output tokens" and float(m.value.replace(",", "")) > 0 for m in at.metric
    )
    chart = json.loads(at.get("plotly_chart")[0].proto.spec)
    assert any(t["name"] == "Unmet demand" and t["type"] == "scatter" for t in chart["data"])


def test_economic_controls_validate_without_erasing_result():
    at = app()
    at.radio(key="view").set_value("Economics").run()
    before = at.session_state["completed"].envelope["run_hash"]
    input_by_label(at, "number_input", "Whole-node idle power (kW)").set_value(12.0)
    click(at, "Apply economic assumptions")
    assert "idle exceeds load" in all_text(at)
    assert at.session_state["completed"].envelope["run_hash"] == before
    input_by_label(at, "number_input", "Whole-node idle power (kW)").set_value(2.0)
    input_by_label(at, "text_input", "Complete owned node (USD)").set_value("450000")
    click(at, "Apply economic assumptions")
    assert at.session_state["completed"].run.node_acquisition_usd == 450000.0
    assert any(
        "node_acquisition_usd" in e.parent_input_ids
        for e in at.session_state["completed"].run.override_history
    )


def test_download_import_roundtrip_and_bytes(tmp_path):
    at = app()
    bundle = at.session_state["completed"]
    assert all(d.proto.url for d in at.download_button)
    at.download_button(key="download:scenario.json").click().run()
    assert (
        not at.exception
        and at.session_state["completed"].envelope["run_hash"] == bundle.envelope["run_hash"]
    )
    with zipfile.ZipFile(BytesIO(bundle.zip_bytes())) as z:
        assert set(z.namelist()) == set(bundle.files)
        assert z.read("decision_memo.md") == bundle.files["decision_memo.md"]
    path = tmp_path / "scenario.json"
    path.write_bytes(bundle.files["scenario.json"])
    restored, envelope = load_run(path, DATA)
    assert digest(restored.model_dump(mode="json")) == envelope["run_hash"]
    at.file_uploader(key="scenario_upload").set_value(
        ("scenario.json", bundle.files["scenario.json"], "application/json")
    )
    click(at, "Import and run")
    assert (
        at.session_state["completed"].envelope["expected_output_sha256"]
        == bundle.envelope["expected_output_sha256"]
    )
    assert (
        at.session_state["completed"].files["monthly_ledger.csv"]
        == bundle.files["monthly_ledger.csv"]
    )


def test_bad_import_and_missing_file_keep_last_run():
    at = app()
    before = at.session_state["completed"].envelope["run_hash"]
    click(at, "Import and run")
    assert "Select a scenario JSON" in all_text(at)
    at.file_uploader(key="scenario_upload").set_value(
        ("bad.json", b'{"schema_version":"bogus"}', "application/json")
    )
    click(at, "Import and run")
    assert at.error and at.session_state["completed"].envelope["run_hash"] == before


def test_two_sessions_are_isolated():
    first = app()
    second = app()
    initial = second.session_state["completed"].envelope["run_hash"]
    assert first.session_state["completed"] is not second.session_state["completed"]
    input_by_label(first, "number_input", "Demand multiplier (×)").set_value(0.5)
    click(first, "Run scenario")
    assert first.session_state["completed"].run.demand_multiplier == 0.5
    assert second.session_state["completed"].run.demand_multiplier == 1.0
    second.run()
    assert second.session_state["completed"].envelope["run_hash"] == initial
    assert (
        first.session_state["completed"].files["scenario.json"]
        != second.session_state["completed"].files["scenario.json"]
    )


def test_import_size_rejected_before_computation():
    with pytest.raises(ValueError, match="1 MB"):
        compute_bytes(b" " * 1_000_001)


def test_ui_has_not_changed_frozen_engine_or_source_data():
    # Lock exact pre-UI source bytes, not a comparison against newly generated values.
    frozen = json.loads((ROOT / "tests/fixtures/pre_ui_integrity.json").read_text())
    approved = json.loads(
        (ROOT / "tests/fixtures/deterministic_reduction_integrity.json").read_text()
    )
    assert approved["file"] == "src/compute_economics/economics.py"
    assert frozen[approved["file"]] == approved["original_sha256"]
    # The approved scalar-power correction changes only these two implementation files.
    # Keep the original fixture hashes and every other exact-byte guard intact.
    power_changes = {
        "src/compute_economics/economics.py": (
            "4da12631c7eee084a0ed2271e82f3505244aef88572a931d60f2a7024820e89c",
            "db9e17f0414877e024cdf1ffd37eba4bfee713296cd48e845aa8d2ba23adef99",
        ),
        "src/compute_economics/workload.py": (
            "8385082326db66de9b919288e8ac5d48f4c913e0ed9bcb045061f3d20849cfd1",
            "674d0410e55282fc6422cebfedff34df3b9caef3a1a26e8c7d322fc025bcc624",
        ),
    }
    for name, expected in frozen.items():
        if name == approved["file"]:
            expected = approved["approved_sha256"]
        if name in power_changes:
            previous, current = power_changes[name]
            assert expected == previous, name
            expected = current
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def test_imported_scenario_name_is_escaped_in_display():
    at = app()
    label = "![scenario](https://example.invalid/image.png) <b>name</b>"
    bundle = at.session_state["completed"]
    at.session_state["completed"] = replace(
        bundle, run=bundle.run.model_copy(update={"scenario_id": label})
    )
    at.run()
    assert not at.exception
    assert any(safe_text(label) in caption.value for caption in at.caption)
    assert label not in all_text(at)


def test_display_tables_preserve_values_and_explain_units(monkeypatch):
    from copy import deepcopy

    import pandas as pd

    from compute_economics.ui.presentation import display_table

    rows = [
        {
            "bracket": [0.9500000000000001, 1.0],
            "from": "own:1",
            "to": "own:2",
            "fixed_policy_utilization_bracket": [0.8174880792235923, 0.85],
        }
    ]
    before = deepcopy(rows)
    captured = []
    monkeypatch.setattr(
        "compute_economics.ui.presentation.st.dataframe",
        lambda frame, **kwargs: captured.append(frame),
    )
    display_table(pd.DataFrame(rows), axis="demand")
    assert rows == before
    shown = captured[0].iloc[0]
    assert shown["Fixed-capacity utilization"] == "81.7%–85.0%"
    assert shown["Tested interval"] == "0.95–1×"
    assert shown["Preferred policy before"] == "Own 1 node + overflow"
    assert "0000000001" not in captured[0].to_string()


def test_public_copy_and_display_do_not_change_export_contract():
    at = app()
    bundle = at.session_state["completed"]
    original = dict(bundle.files)
    assert at.title[0].value == "Rent, commit, or own AI compute?"
    assert at.selectbox(key="preset").label == "Scenario preset"
    assert at.file_uploader(key="scenario_upload").proto.max_upload_size_mb == 1
    assert bundle.envelope["run_hash"][:12] not in all_text(at)
    assert "Key limitation:" in all_text(at)
    assert "spot pricing is not modeled" in all_text(at)
    assert all("_" not in str(c) for table in at.dataframe for c in table.value.columns)
    for view in ["Economics", "Risk & Capacity", "Evidence & Methodology"]:
        at.radio(key="view").set_value(view).run(timeout=90)
        assert not at.exception
        assert at.session_state["completed"].files == original
