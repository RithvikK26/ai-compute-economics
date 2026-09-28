"""Compare every exported file against fixtures and a fresh JSON round trip, offline."""

import json
import socket
import tempfile
from pathlib import Path

from compute_economics.reporting import export_run, load_run

ROOT = Path(__file__).resolve().parents[1]


def deny_network(*args, **kwargs):
    raise AssertionError("Reproduction must not open a network connection")


def compare(left, right):
    names = {p.name for p in left.iterdir() if p.is_file()}
    assert names == {p.name for p in right.iterdir() if p.is_file()}, "Export file set changed"
    for name in sorted(names):
        if name == "scenario.json":
            a, b = [json.loads((folder / name).read_text()) for folder in (left, right)]
            # Export time is expressly excluded from the deterministic run contract.
            a.pop("created_at_utc")
            b.pop("created_at_utc")
            assert a == b, f"Envelope mismatch: {name}"
        else:
            assert (left / name).read_bytes() == (right / name).read_bytes(), name
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
