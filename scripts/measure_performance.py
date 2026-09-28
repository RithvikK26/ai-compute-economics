"""Single-run local timings; no GPU benchmark, forecast or hosting guarantee."""

import argparse
import importlib.metadata
import json
import platform
import resource
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def deny_network(*args, **kwargs):
    raise AssertionError("Performance measurement must remain offline")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["engine", "app"])
    args = parser.parse_args()
    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    socket.create_connection = deny_network
    report = {
        "mode": args.mode,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ["duckdb", "numpy", "pandas", "pydantic", "streamlit", "plotly", "pytest"]
        },
        "network": "blocked",
        "samples": 1,
    }
    if args.mode == "engine":
        from compute_economics.reporting import load_run
        from compute_economics.scenarios import decision_analysis, evaluate_all
        from compute_economics.workload import build_demand

        run, _ = load_run(ROOT / "scenarios/stable_demand.json", ROOT / "data")
        demand = build_demand(run)
        evaluate_all(run, demand)  # Warm imports and one baseline evaluation.
        start = time.perf_counter()
        for scale in [0.5, 1.0, 1.5]:
            evaluate_all(run, demand.scaled(scale))
        report["warm_three_path_comparison_seconds"] = time.perf_counter() - start
        start = time.perf_counter()
        result = decision_analysis(run)
        report["full_analysis_seconds"] = time.perf_counter() - start
        report["policies"] = len(result["policies"])
        report["surface_cells"] = len(result["surface"])
    else:
        from streamlit.testing.v1 import AppTest

        start = time.perf_counter()
        app = AppTest.from_file(ROOT / "app.py", default_timeout=90).run()
        assert not app.exception
        report["initial_apptest_seconds"] = time.perf_counter() - start
        report["view_rerun_seconds"] = {}
        for view in ["Decision", "Economics", "Risk & Capacity", "Evidence & Methodology"]:
            start = time.perf_counter()
            app.radio(key="view").set_value(view).run()
            assert not app.exception
            report["view_rerun_seconds"][view] = time.perf_counter() - start
        report["note"] = (
            "AppTest process, not browser paint time or a hosted concurrent-user load test."
        )
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_process_rss_bytes"] = rss if platform.system() == "Darwin" else rss * 1024
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
