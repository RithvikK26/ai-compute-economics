"""Narrow offline MLPerf parser: unexpected source shape is a hard error."""

import csv
import hashlib
import json
import math
from pathlib import Path

MLPERF_COLUMNS = [
    "Organization",
    "Availability",
    "Division",
    "SystemType",
    "SystemName",
    "Platform",
    "Model",
    "MlperfModel",
    "Scenario",
    "Result",
    "Accuracy",
    "number_of_nodes",
    "host_processor_model_name",
    "host_processors_per_node",
    "host_processor_core_count",
    "accelerator_model_name",
    "accelerators_per_node",
    "total_accelerators",
    "Location",
    "framework",
    "operating_system",
    "notes",
    "compliance",
    "errors",
    "version",
    "inferred",
    "has_power",
    "Units",
    "weight_data_types",
    "design_power_watts",
    "PrivateID",
]
SYSTEMS = {"B200-SXM-180GBx8_TRT": "B200", "B300-SXM-270GBx8_TRT": "B300"}
MODELS = {"gpt-oss-120b", "llama2-70b-99.9"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_mlperf(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != MLPERF_COLUMNS:
            raise ValueError("unexplained benchmark schema drift")
        rows = list(reader)
    selected = []
    seen = set()
    for r in rows:
        if (
            r["Organization"] != "CoreWeave"
            or r["Platform"] not in SYSTEMS
            or r["Model"] not in MODELS
            or r["Scenario"] != "Offline"
        ):
            continue
        required = {
            "Availability": "available",
            "Division": "closed",
            "SystemType": "datacenter",
            "number_of_nodes": "1",
            "accelerators_per_node": "8",
            "total_accelerators": "8",
            "version": "v6.1",
            "errors": "0",
            "Units": "Tokens/s",
            "inferred": "0",
            "weight_data_types": "fp4",
        }
        if any(r[k] != v for k, v in required.items()):
            raise ValueError("benchmark admission mismatch")
        if (
            r["MlperfModel"] != r["Model"]
            or not r["framework"]
            or r["accelerator_model_name"] != "NVIDIA " + r["Platform"].split("x8")[0]
        ):
            raise ValueError("model/system/runtime mismatch")
        expected = (
            f"./closed/CoreWeave/results/{r['Platform']}/{r['Model']}/Offline/performance/run_1"
        )
        if r["Location"] != expected:
            raise ValueError("result path mismatch")
        key = (r["Platform"], r["Model"])
        if key in seen:
            raise ValueError("duplicate benchmark key")
        seen.add(key)
        result = float(r["Result"])
        if not math.isfinite(result) or result <= 0:
            raise ValueError("invalid throughput")
        selected.append(r)
    if seen != {(s, m) for s in SYSTEMS for m in MODELS}:
        raise ValueError("required exact workload rows missing")
    return selected


def validate_manifest(data: Path) -> dict:
    manifest = json.loads((data / "snapshots/2026-09-27/manifest.json").read_text())
    for name, expected in manifest["checksums"].items():
        path = data / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"artifact checksum mismatch: {name}")
    return manifest


def stage_summary(candidate: Path, stage: Path) -> list[dict]:
    """Validate before staging; never replace a validated snapshot automatically."""
    rows = parse_mlperf(candidate)
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "selected_rows.json").write_text(json.dumps(rows, indent=2))
    (stage / "manifest.json").write_text(
        json.dumps({"candidate_sha256": sha256(candidate), "review_status": "pending"})
    )
    return rows
