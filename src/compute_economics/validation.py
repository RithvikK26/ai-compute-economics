"""Source and run gates; exclusions remain distinct from warnings."""

import csv
import json
import math
from datetime import date, datetime
from pathlib import Path

from compute_economics.ingestion import parse_mlperf, sha256, validate_manifest
from compute_economics.schemas import RunInput, ValidationReport


def read_table(data: Path, name: str) -> list[dict]:
    with (data / f"{name}.csv").open(newline="") as f:
        return list(csv.DictReader(f))


def validate_tables(tables: dict[str, list[dict]]) -> None:
    for name, key in [
        ("sources", "source_id"),
        ("configurations", "configuration_id"),
        ("offers", "offer_id"),
        ("benchmarks", "benchmark_id"),
    ]:
        rows = tables[name]
        if len({r[key] for r in rows}) != len(rows):
            raise ValueError(f"duplicate {name} key")
    sources = {r["source_id"]: r for r in tables["sources"]}
    configs = {r["configuration_id"]: r for r in tables["configurations"]}
    for s in sources.values():
        if not all(s.get(k) for k in ["url", "license_note", "artifact_hash", "retrieval_date"]):
            raise ValueError("missing source evidence")
    for o in tables["offers"]:
        if o["source_id"] not in sources or o["configuration_id"] not in configs:
            raise ValueError("broken offer foreign key")
        if not o["artifact_hash"] or not o["source_locator"]:
            raise ValueError("missing offer evidence")
        if o["admission_status"] == "catalog_only":
            if (
                o["currency"] != "USD"
                or o["raw_unit"] not in ("USD/GPU-hour", "USD/instance-hour")
                or o["pricing_kind"] not in ("on_demand_headline", "capacity_block")
            ):
                raise ValueError("invalid catalog-only offer boundary")
            if not o["null_reason"]:
                raise ValueError("catalog-only restriction must be explained")
            price = float(o["raw_price"])
            if not math.isfinite(price) or price < 0:
                raise ValueError("invalid catalog price")
            if o["pricing_kind"] == "on_demand_headline" and o["node_hour_price"]:
                raise ValueError("unconfirmed packaging cannot yield node price")
            if o["pricing_kind"] == "capacity_block" and (
                float(o["node_hour_price"]) != price or o["gpu_count"] != "8"
            ):
                raise ValueError("capacity block normalization mismatch")
            continue
        if (
            o["currency"] != "USD"
            or o["raw_unit"] != "USD/node-hour"
            or o["pricing_kind"] != "on_demand"
            or o["price_component"] != "complete_node"
        ):
            raise ValueError("unsupported offer unit/product/currency")
        if o["gpu_count"] != configs[o["configuration_id"]]["gpu_count"]:
            raise ValueError("GPU count mismatch")
        if not o["region"]:
            raise ValueError("missing region")
        if o["node_hour_price"] == "":
            if not o["null_reason"] or o["admission_status"] != "unavailable":
                raise ValueError("unknown price must be unavailable")
        else:
            p = float(o["node_hour_price"])
            if not math.isfinite(p) or p < 0 or p != float(o["raw_price"]) or o["null_reason"]:
                raise ValueError("price does not reconcile")
    benchmark_ids = {b["benchmark_id"] for b in tables["benchmarks"]}
    keys = set()
    for c in tables["compatibility"]:
        key = (c["configuration_id"], c["workload_id"])
        if key in keys:
            raise ValueError("duplicate compatibility join")
        keys.add(key)
        if c["configuration_id"] not in configs or c["benchmark_id"] not in benchmark_ids:
            raise ValueError("broken compatibility foreign key")
        if c["match_level"] == "conditional_transfer" and not c["differences"]:
            raise ValueError("missing transfer differences")
    for b in tables["benchmarks"]:
        if b["configuration_id"] not in configs or b["source_id"] not in sources:
            raise ValueError("broken benchmark foreign key")
        if (
            b["node_count"] != "1"
            or b["gpu_count"] != "8"
            or b["availability"] != "available"
            or b["division"] != "closed"
            or b["scenario"] != "Offline"
            or b["release"] != "v6.1"
            or b["unit"] != "tokens/s/node"
        ):
            raise ValueError("benchmark mismatch")


def validate_data(data: Path) -> dict:
    manifest = validate_manifest(data)
    tables = {
        name: read_table(data, name)
        for name in ["sources", "configurations", "offers", "benchmarks", "compatibility"]
    }
    validate_tables(tables)
    for source in tables["sources"]:
        if sha256(data / source["artifact_path"]) != source["artifact_hash"]:
            raise ValueError("Source artifact identity mismatch")
    evidence = data / "snapshots/2026-09-27/evidence"
    published = {
        (r["Platform"], r["Model"]): r for r in parse_mlperf(evidence / "selected_summary.csv")
    }
    for benchmark in tables["benchmarks"]:
        raw = published.get((benchmark["system_id"], benchmark["model"]))
        if (
            raw is None
            or float(benchmark["value"]) != float(raw["Result"])
            or benchmark["accuracy"] != raw["Accuracy"]
            or benchmark["runtime"] != raw["framework"]
            or benchmark["result_path"] != raw["Location"]
            or benchmark["commit"] != manifest["results_commit"]
        ):
            raise ValueError("Curated benchmark does not reconcile to frozen official row")
    prices = json.loads((evidence / "coreweave_pricing_extract.json").read_text())
    raw_prices = {"cw-" + r["family"].lower() + "-8": r for r in prices["rows"]}
    for offer in tables["offers"]:
        if offer["source_id"] != "S01":
            continue
        raw = raw_prices[offer["configuration_id"]]
        price = float(offer["node_hour_price"]) if offer["node_hour_price"] else None
        if (
            price != raw["price"]
            or offer["region"] != prices["region"]
            or int(offer["gpu_count"]) != raw["gpus"]
        ):
            raise ValueError("Curated offer does not reconcile to frozen price extract")
    return manifest


def freshness(observed: str, cutoff: date, age_days: int) -> str:
    age = (cutoff - datetime.fromisoformat(observed).date()).days
    return "future" if age < 0 else "stale" if age > age_days else "within_review_window"


def validate_run(run: RunInput, as_of: date | None = None) -> ValidationReport:
    errors = []
    warnings = [
        "Illustrative scenario using public reference data and analyst assumptions.",
        "Benchmark-to-production and purchased-system transfer is assumed.",
        "Batch blocks omit within-block bursts; no interactive SLO claim.",
    ]
    exclusions = {}
    ages = {}
    cutoff = as_of or run.analysis_as_of
    for e in run.evidence:
        if e.observed_at_utc:
            threshold = (
                30
                if e.measurement_kind == "list_price"
                else 400
                if e.measurement_kind == "financial_disclosure"
                else 180
            )
            status = freshness(e.observed_at_utc.isoformat(), cutoff, threshold)
            ages[e.input_id] = status
            if status != "within_review_window":
                warnings.append(f"{e.input_id}: {status} evidence")
                if not run.historical_snapshot and not run.stale_acknowledged:
                    errors.append("fresh-mode evidence requires acknowledgement")
    if run.historical_snapshot:
        warnings.append("Historical snapshot; not a live quote.")
    if run.max_od_nodes is None and run.assumed_max_od_nodes is None:
        errors.append("Unknown rental capacity requires explicit assumed limit")
    if not run.capacity_acknowledged:
        errors.append("Live capacity must be acknowledged as assumed")
    if run.workload.performance_tokens_s is None:
        errors.append("Unavailable workload performance")
    if run.od_price_usd is None:
        errors.append("Unavailable on-demand price; no zero/fallback substitution")
    if run.commit_price_usd is None:
        exclusions["commit"] = "Unavailable commitment price"
    if run.commit_term_months != run.horizon_months:
        exclusions["commit"] = "Contract term must equal horizon; no hidden tail liabilities"
    if run.node_acquisition_usd is None:
        exclusions["own"] = "Unavailable acquisition price"
    if run.usable_life_months < run.horizon_months - run.delay_months:
        exclusions["own"] = "Economic life cannot cover operating horizon"
    if run.spare_nodes >= run.max_fleet_nodes:
        exclusions["own"] = "Fleet bound cannot exceed spares"
    if (
        run.node_acquisition_usd is not None
        and run.residual_usd > run.node_acquisition_usd * run.max_fleet_nodes
    ):
        warnings.append("Residual exceeds maximum enumerated asset purchase cost")
    return ValidationReport(
        errors=list(dict.fromkeys(errors)),
        warnings=warnings,
        policy_exclusions=exclusions,
        source_freshness=ages,
    )
