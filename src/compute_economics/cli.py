"""Offline command-line contract for Packages 1–7."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from compute_economics.catalog import build_catalog, query_catalog
from compute_economics.reporting import export_run, load_run
from compute_economics.validation import validate_data


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Conditional compute economics; offline frozen evidence"
    )
    parser.add_argument("--data", type=Path, default=Path("data"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-data")
    prep = sub.add_parser("catalog")
    prep.add_argument("--output", type=Path, default=Path("catalog.duckdb"))
    run = sub.add_parser("run")
    run.add_argument("scenario", type=Path)
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-data":
            manifest = validate_data(args.data)
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "snapshot": manifest["snapshot_id"],
                        "checked_artifacts": len(manifest["checksums"]),
                    }
                )
            )
        elif args.command == "catalog":
            build_catalog(args.data, args.output)
            print(f"Built offline catalog: {args.output}")
        else:
            inputs, envelope = load_run(args.scenario, args.data)
            # Use the relational catalog for actual run coverage, not only demonstration tests.
            with tempfile.TemporaryDirectory(prefix="compute-catalog-") as tmp:
                db = Path(tmp) / "catalog.duckdb"
                build_catalog(args.data, db)
                coverage = query_catalog(
                    db,
                    "evidence_coverage",
                    {"region": inputs.region, "workload": inputs.workload.workload_id},
                )
                if not any(r["configuration_id"] == inputs.configuration_id for r in coverage):
                    raise ValueError("Configuration absent from analytical catalog")
            exported, analysis = export_run(
                inputs,
                args.output,
                expected_output_sha256=envelope["expected_output_sha256"] if envelope else None,
            )
            print(analysis["comparison"]["message"])
            print(f"Run hash: {exported['run_hash']}\nOutputs: {args.output.resolve()}")
    except (ValueError, OSError, ArithmeticError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
