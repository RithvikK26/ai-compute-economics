"""Rebuildable DuckDB, private writer then independent read-only connections."""

from pathlib import Path

import duckdb

from compute_economics.validation import validate_data

SQL = Path(__file__).with_name("sql")


def build_catalog(data: Path, destination: Path) -> None:
    validate_data(data)
    with duckdb.connect(str(destination)) as con:
        for name in ["sources", "configurations", "offers", "benchmarks", "compatibility"]:
            # Names are internal constants; file path passed as a bound parameter.
            con.execute(
                f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv(?, all_varchar=true)",
                [str(data / f"{name}.csv")],
            )


def query_catalog(database: Path, query: str, parameters: dict) -> list[dict]:
    if query not in ["eligible_offers", "evidence_coverage"]:
        raise ValueError("unknown catalog query")
    with duckdb.connect(str(database), read_only=True) as con:
        cursor = con.execute((SQL / f"{query}.sql").read_text(), parameters)
        return [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]


def aggregate_ledger(rows: list[dict]) -> list[dict]:
    import pandas as pd

    frame = pd.DataFrame(rows)
    with duckdb.connect() as con:
        con.register("ledger", frame)
        cursor = con.execute((SQL / "annual_costs.sql").read_text())
        return [dict(zip([x[0] for x in cursor.description], r)) for r in cursor.fetchall()]
