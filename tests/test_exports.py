import json
from pathlib import Path

import pytest
from conftest import changed

from compute_economics.cli import main
from compute_economics.reporting import (
    apply_overrides,
    digest,
    export_run,
    load_run,
    read_json,
    safe_csv,
    safe_text,
    validate_admission,
)
from compute_economics.scenarios import decision_analysis
from compute_economics.schemas import RunInput

DATA = Path("data")


def test_roundtrip_reproduces_outputs_and_hash(tmp_path, run):
    inputs = apply_overrides(changed(run, max_fleet_nodes=2))
    envelope, analysis = export_run(inputs, tmp_path / "first")
    restored, saved = load_run(tmp_path / "first/scenario.json", DATA)
    assert restored == inputs
    assert saved["run_hash"] == digest(restored.model_dump(mode="json"))
    second, rerun = export_run(
        restored, tmp_path / "second", expected_output_sha256=saved["expected_output_sha256"]
    )
    assert rerun == analysis
    assert second["run_hash"] == envelope["run_hash"]
    assert (tmp_path / "first/decision_memo.md").read_text() == (
        tmp_path / "second/decision_memo.md"
    ).read_text()
    assert len((tmp_path / "first/scenario.json").read_bytes()) < 1_000_000
    for filename in [
        "monthly_ledger.csv",
        "block_ledger.csv",
        "cost_ledger.csv",
        "annual_costs.csv",
        "policy_comparison.csv",
        "decision_surface.csv",
        "provenance.csv",
    ]:
        assert (tmp_path / "first" / filename).stat().st_size > 0
    memo = (tmp_path / "first/decision_memo.md").read_text()
    for expected in [
        "Decision frontier",
        "Tested reversals",
        "Most influential",
        "Material missing evidence",
        "Stable across",
        "Policy comparison",
        "Cash flow",
    ]:
        assert expected in memo


def test_overrides_retain_observations(run):
    changed_run = apply_overrides(changed(run, od_price_usd=75.0))
    assert changed_run.evidence == run.evidence
    override = next(e for e in changed_run.override_history if "od_price_usd" in e.parent_input_ids)
    assert override.value == 75.0 and override.evidence_class == "user_assumption"
    assert apply_overrides(changed_run) == changed_run


@pytest.mark.parametrize(
    "payload", [b'{"x":1,"x":2}', b'{"value":NaN}', b"[" * 22 + b"0" + b"]" * 22, b" " * 1_000_001]
)
def test_unsafe_json(tmp_path, payload):
    p = tmp_path / "input.json"
    p.write_bytes(payload)
    with pytest.raises(ValueError):
        read_json(p)


@pytest.mark.parametrize(
    "field,value",
    [
        ("quality", "99%"),
        ("scenario", "Server"),
        ("precision", "fp8"),
        ("runtime", "arbitrary"),
        ("dataset", "different-context-length"),
        ("performance_tokens_s", 999999.0),
    ],
)
def test_workload_safeguards(run, field, value):
    raw = run.model_dump(mode="json")
    raw["workload"][field] = value
    with pytest.raises(ValueError):
        bad = RunInput.model_validate_json(json.dumps(raw))
        validate_admission(bad, DATA)


def test_tampered_evidence_or_snapshot(run):
    bad = changed(run, source_checksums={})
    with pytest.raises(ValueError):
        validate_admission(bad, DATA)
    altered = run.evidence[0].model_copy(update={"value": 4.0})
    bad = changed(run, evidence=[altered] + run.evidence[1:])
    with pytest.raises(ValueError):
        validate_admission(bad, DATA)


def test_b300_no_implicit_price_fallback(run):
    with pytest.raises(ValueError, match="B300 price is null"):
        validate_admission(changed(run, configuration_id="cw-b300-8"), DATA)


def test_csv_and_markdown_injection():
    assert safe_csv("=CMD()") == "'=CMD()"
    assert safe_csv(-120.0) == -120.0
    assert "&lt;script&gt;" in safe_text("<script>")
    assert "\\[" in safe_text("[untrusted](http://example.com)")


def test_cli_validation_and_invalid_input(tmp_path):
    assert main(["validate-data"]) == 0
    p = tmp_path / "bad.json"
    p.write_text('{"unexpected":1}')
    assert main(["run", str(p), "--output", str(tmp_path / "out")]) == 2
    assert not (tmp_path / "out").exists()


def test_deterministic_analysis_and_isolation(run):
    small = changed(run, max_fleet_nodes=1)
    first = decision_analysis(small, include_surface=False)
    decision_analysis(changed(small, demand_multiplier=0.5), include_surface=False)
    assert first == decision_analysis(small, include_surface=False)
