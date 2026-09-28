"""Audit only the approved last-bit changes against the original published fixtures."""

import json
import math
import subprocess
from decimal import Decimal
from pathlib import Path

BASELINE = "82c64796ba0e7a9067064ae67719ed04ab832a0a"
ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "pv_cost_usd",
    "lowest_pv_usd",
    "fixed_pv_usd",
    "fixed_policy_pv_usd",
    "levelized_usd_million_tokens",
    "regret_usd",
    "runner_up_gap_usd",
    "advantage_vs_best_alternative_usd",
    "decision_margin_range_usd",
}


def audit(before, after, path="", changes=None):
    if changes is None:
        changes = []
    assert type(before) is type(after), path
    if isinstance(before, dict):
        assert before.keys() == after.keys(), path
        for key in before:
            audit(before[key], after[key], path + "/" + key, changes)
    elif isinstance(before, list):
        assert len(before) == len(after), path
        for i, (a, b) in enumerate(zip(before, after, strict=True)):
            audit(a, b, path + "/" + str(i), changes)
    elif before != after:
        assert isinstance(before, float), (path, before, after)
        assert "bracket" not in path, ("Decision threshold changed", path)
        leaf = path.rsplit("/", 1)[-1]
        assert leaf in ALLOWED or any(
            key in path
            for key in ["/costs/", "/category_pv_usd/", "/savings_vs_od_usd/", "/difference_usd/"]
        ), ("Unexpected changed field", path)
        delta = Decimal(str(after)) - Decimal(str(before))
        bound = Decimal("4e-16") if leaf == "levelized_usd_million_tokens" else Decimal("8e-9")
        assert abs(delta) <= bound, ("Beyond diagnosed absolute range", path, delta)
        # Differences of nearby PV totals can amplify ULP counts through cancellation.
        # Direct PV totals and levelized costs must retain the diagnosed <=4 ULP bound.
        if leaf in {"pv_cost_usd", "lowest_pv_usd", "levelized_usd_million_tokens"}:
            assert abs(after - before) <= 4 * max(math.ulp(before), math.ulp(after)), path
        changes.append({"path": path, "before": before, "after": after, "delta": str(delta)})
    return changes


def main():
    reports = {}
    for preset in ["stable_demand", "demand_disappointment", "delayed_capacity"]:
        directory = Path("examples") if preset == "stable_demand" else Path("examples") / preset
        name = (directory / "results.json").as_posix()
        original = subprocess.check_output(["git", "show", BASELINE + ":" + name], cwd=ROOT)
        changes = audit(json.loads(original), json.loads((ROOT / name).read_text()))
        reports[preset] = {
            "changed_numbers": len(changes),
            "decision_outcomes_and_brackets": "identical",
        }
    print(json.dumps({"status": "PASS", "baseline": BASELINE, "presets": reports}, indent=2))


if __name__ == "__main__":
    main()
