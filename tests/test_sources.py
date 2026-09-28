import csv
import json
from pathlib import Path

import pytest

from compute_economics.ingestion import parse_mlperf, stage_summary, validate_manifest
from compute_economics.schemas import RunInput

DATA = Path("data")
SUMMARY = DATA / "snapshots/2026-09-27/evidence/selected_summary.csv"


def test_frozen_sources():
    manifest = validate_manifest(DATA)
    assert len(manifest["results_commit"]) == 40
    assert [float(r["Result"]) for r in parse_mlperf(SUMMARY)] == [
        91487.4,
        102703.0,
        112840.0,
        115530.0,
    ]
    for name in ["stable_demand", "demand_disappointment", "delayed_capacity"]:
        run = RunInput.model_validate_json(Path(f"scenarios/{name}.json").read_text())
        assert run.workload.model == "gpt-oss-120b"
        assert run.demand_scale_tokens_s == pytest.approx(102703 * 0.7, rel=1e-12)
    offers = list(csv.DictReader((DATA / "offers.csv").open()))
    assert [o["node_hour_price"] for o in offers[:4]] == ["49.24", "50.44", "68.8", ""]
    assert offers[3]["null_reason"] == "Contact sales"


@pytest.mark.parametrize(
    "field,value",
    [
        ("Units", "Samples/s"),
        ("number_of_nodes", "2"),
        ("Availability", "preview"),
        ("Division", "open"),
        ("version", "v6.0"),
        ("accelerator_model_name", "H200 + MI350X"),
        ("Result", "nan"),
        ("Scenario", "Server"),
        ("Model", "llama2-70b-99"),
        ("Location", "wrong"),
        ("inferred", "1"),
    ],
)
def test_bad_benchmark(tmp_path, field, value):
    with SUMMARY.open() as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    rows[0][field] = value
    path = tmp_path / "candidate.csv"
    with path.open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError):
        stage_summary(path, tmp_path / "stage")
    assert not (tmp_path / "stage").exists()
    validate_manifest(DATA)


def test_schema_drift_and_duplicate(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(SUMMARY.read_text().replace("Organization,", "NewField,"))
    with pytest.raises(ValueError, match="schema drift"):
        parse_mlperf(p)
    with SUMMARY.open() as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    with p.open("w") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows + [rows[0]])
    with pytest.raises(ValueError, match="duplicate"):
        parse_mlperf(p)


def test_logs_accuracy_and_metadata():
    for r in parse_mlperf(SUMMARY):
        prefix = f"closed__CoreWeave__results__{r['Platform']}__{r['Model']}__Offline__"
        log = (SUMMARY.parent / (prefix + "performance__run_1__mlperf_log_summary.txt")).read_text()
        assert "Result is : VALID" in log
        assert f"Tokens per second: {float(r['Result']):g}" in log
        system = json.loads(
            (
                SUMMARY.parent / ("closed__CoreWeave__systems__" + r["Platform"] + ".json")
            ).read_text()
        )
        assert system["number_of_nodes"] == 1 and system["accelerators_per_node"] == 8
        if r["Model"] == "gpt-oss-120b":
            assert float(r["Accuracy"].split(": ")[1]) >= 0.99 * 83.13
            assert (
                r["Accuracy"].split(": ")[1]
                in (SUMMARY.parent / (prefix + "accuracy__accuracy.txt")).read_text()
            )


def test_curated_benchmark_must_reconcile_even_after_manifest_rehash(tmp_path):
    import hashlib
    import shutil

    from compute_economics.validation import validate_data

    data = tmp_path / "data"
    shutil.copytree(DATA, data)
    p = data / "benchmarks.csv"
    p.write_text(p.read_text().replace("91487.4", "99999.0"))
    mp = data / "snapshots/2026-09-27/manifest.json"
    m = json.loads(mp.read_text())
    m["checksums"]["benchmarks.csv"] = hashlib.sha256(p.read_bytes()).hexdigest()
    mp.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="does not reconcile"):
        validate_data(data)
