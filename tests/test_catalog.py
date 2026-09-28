from copy import deepcopy
from pathlib import Path

import pytest

from compute_economics.catalog import aggregate_ledger, build_catalog, query_catalog
from compute_economics.validation import read_table, validate_tables


def test_offline_catalog(tmp_path):
    db = tmp_path / "catalog.duckdb"
    build_catalog(Path("data"), db)
    args = dict(cutoff="2026-09-27", region="North America", historical=True, acknowledged=False)
    rows = query_catalog(db, "eligible_offers", args)
    assert len(rows) == 3
    assert len({r["configuration_id"] for r in rows}) == 3
    assert query_catalog(db, "eligible_offers", dict(args, region="Europe")) == []
    assert (
        query_catalog(db, "eligible_offers", dict(args, cutoff="2027-01-01", historical=False))
        == []
    )
    coverage = query_catalog(
        db, "evidence_coverage", dict(region="North America", workload="gpt-oss-120b-v6.1-offline")
    )
    assert len(coverage) == 8
    assert {
        r["family"]: r["evidence_status"]
        for r in coverage
        if r["configuration_id"].startswith("cw-")
    } == {
        "B200": "conditional",
        "B300": "missing_price",
        "H100": "missing_compatible_performance",
        "H200": "missing_compatible_performance",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("currency", ""),
        ("raw_unit", "USD/GPU-hour"),
        ("pricing_kind", "spot"),
        ("price_component", "software_addon"),
        ("artifact_hash", ""),
        ("raw_price", "1"),
    ],
)
def test_bad_offer(field, value):
    tables = {
        n: read_table(Path("data"), n)
        for n in ["sources", "configurations", "offers", "benchmarks", "compatibility"]
    }
    tables["offers"][0][field] = value
    with pytest.raises(ValueError):
        validate_tables(tables)


def test_duplicate_join_and_quote_zero():
    tables = {
        n: read_table(Path("data"), n)
        for n in ["sources", "configurations", "offers", "benchmarks", "compatibility"]
    }
    bad = deepcopy(tables)
    bad["compatibility"].append(bad["compatibility"][0])
    with pytest.raises(ValueError):
        validate_tables(bad)
    tables["offers"][3]["node_hour_price"] = "0"
    with pytest.raises(ValueError):
        validate_tables(tables)


def test_sql_ledger_totals():
    rows = [
        dict(policy_id="own:1", period=p, category=c, cash_usd=v, pv_usd=v, flow_kind=k)
        for p, c, v, k in [
            (0, "capex", 1200.0, "capital"),
            (1, "energy", 100.0, "operating"),
            (12, "residual", -120.0, "terminal"),
        ]
    ]
    totals = aggregate_ledger(rows)
    assert sum(r["cash_usd"] for r in totals) == 1180
    assert sum(r["operating_cash_usd"] for r in totals) == 100


def test_reference_products_never_join_as_on_demand(tmp_path):
    db = tmp_path / "catalog.duckdb"
    build_catalog(Path("data"), db)
    for region in ["US East (Ohio)", "US West (Oregon)", "not specified"]:
        assert (
            query_catalog(
                db,
                "eligible_offers",
                dict(cutoff="2026-09-27", region=region, historical=True, acknowledged=False),
            )
            == []
        )
    rows = read_table(Path("data"), "offers")
    aws = [r for r in rows if r["pricing_kind"] == "capacity_block"]
    assert [float(r["raw_price"]) / int(r["gpu_count"]) for r in aws] == [5.97, 14.04]
    assert all(r["admission_status"] == "catalog_only" for r in aws)
