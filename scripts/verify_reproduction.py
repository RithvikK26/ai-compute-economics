"""Compare every exported file against fixtures and a fresh JSON round trip, offline."""

import csv
import difflib
import hashlib
import io
import json
import shutil
import socket
import tempfile
from pathlib import Path

from compute_economics.reporting import export_run, load_run

ROOT = Path(__file__).resolve().parents[1]


def deny_network(*args, **kwargs):
    raise AssertionError("Reproduction must not open a network connection")


def mismatch(left, right, name):
    """Retain exact bytes and diagnostics without relaxing the comparison."""
    parent = ROOT / "artifacts/reproduction-failures"
    parent.mkdir(parents=True, exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix="mismatch-", dir=parent))
    for label, folder in [("expected", left), ("generated", right)]:
        (target / label).mkdir()
        for source in folder.iterdir():
            if source.is_file():
                shutil.copyfile(source, target / label / source.name)
    a, b = [(folder / name).read_bytes() for folder in (left, right)]

    def describe(raw):
        return {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "crlf": raw.count(b"\r\n"),
            "lone_lf": raw.count(b"\n") - raw.count(b"\r\n"),
            "final_newline": raw.endswith(b"\n"),
        }

    details = {"file": name, "expected": describe(a), "generated": describe(b)}
    details["first_byte_difference"] = next(
        (i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b))
    )
    if name.endswith(".csv"):
        aa, bb = [list(csv.reader(io.StringIO(raw.decode(), newline=""))) for raw in (a, b)]
        details["parsed_cells_equal"] = aa == bb
        details["differing_rows"] = [
            {
                "row": i + 1,
                "expected": aa[i] if i < len(aa) else None,
                "generated": bb[i] if i < len(bb) else None,
            }
            for i in range(max(len(aa), len(bb)))
            if (aa[i] if i < len(aa) else None) != (bb[i] if i < len(bb) else None)
        ]
    (target / "comparison.json").write_text(json.dumps(details, indent=2) + "\n")
    (target / "text.diff").write_text(
        "".join(
            difflib.unified_diff(
                a.decode().splitlines(keepends=True),
                b.decode().splitlines(keepends=True),
                fromfile="expected/" + name,
                tofile="generated/" + name,
            )
        )
    )
    raise AssertionError(f"{name}: exact-byte mismatch; retained in {target}")


def compare(left, right):
    names = {p.name for p in left.iterdir() if p.is_file()}
    assert names == {p.name for p in right.iterdir() if p.is_file()}, "Export file set changed"
    for name in sorted(names):
        if name == "scenario.json":
            a, b = [json.loads((folder / name).read_text()) for folder in (left, right)]
            # Export time is expressly excluded from the deterministic run contract.
            a.pop("created_at_utc")
            b.pop("created_at_utc")
            if a != b:
                mismatch(left, right, name)
        else:
            if (left / name).read_bytes() != (right / name).read_bytes():
                mismatch(left, right, name)
    return len(names)


def main():
    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    socket.create_connection = deny_network
    counts = {}
    with tempfile.TemporaryDirectory(prefix="compute-reproduction-") as directory:
        for preset in ("stable_demand", "demand_disappointment", "delayed_capacity"):
            run, _ = load_run(ROOT / "scenarios" / f"{preset}.json", ROOT / "data")
            generated = Path(directory) / preset
            export_run(run, generated)
            reference = ROOT / "examples"
            if preset != "stable_demand":
                reference /= preset
            fixture_count = compare(reference, generated)
            saved, envelope = load_run(generated / "scenario.json", ROOT / "data")
            replay = Path(directory) / (preset + "-replay")
            export_run(saved, replay, expected_output_sha256=envelope["expected_output_sha256"])
            counts[preset] = {
                "fixture_files": fixture_count,
                "replayed_files": compare(generated, replay),
            }
    print(json.dumps({"status": "PASS", "network": "blocked", "presets": counts}, indent=2))


if __name__ == "__main__":
    main()
