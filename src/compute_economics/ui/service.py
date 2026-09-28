"""Session-owned UI adapter around the stable engine and export contract."""

import json
import tempfile
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pandas as pd

from compute_economics.reporting import MAX_JSON_BYTES, export_run, load_run
from compute_economics.schemas import Evidence, RunInput

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PRESETS = {
    "Stable demand": "stable_demand",
    "Demand disappointment": "demand_disappointment",
    "Delayed capacity": "delayed_capacity",
}


@dataclass(frozen=True)
class ViewRun:
    run: RunInput
    analysis: dict
    envelope: dict
    files: dict[str, bytes]

    def table(self, filename):
        payload = self.files[filename]
        return pd.read_csv(BytesIO(payload)) if payload.strip() else pd.DataFrame()

    def zip_bytes(self):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in self.files.items():
                archive.writestr(name, data)
        return buffer.getvalue()


def compute_bytes(payload: bytes) -> ViewRun:
    if len(payload) > MAX_JSON_BYTES:
        raise ValueError("Scenario exceeds the 1 MB import limit.")
    with tempfile.TemporaryDirectory(prefix="compute-ui-") as directory:
        path = Path(directory) / "input.json"
        path.write_bytes(payload)
        run, prior = load_run(path, DATA)
        output = Path(directory) / "output"
        envelope, analysis = export_run(
            run, output, expected_output_sha256=prior["expected_output_sha256"] if prior else None
        )
        files = {p.name: p.read_bytes() for p in output.iterdir() if p.is_file()}
    return ViewRun(run, analysis, envelope, files)


def compute_preset(name):
    return compute_bytes((ROOT / "scenarios" / f"{PRESETS[name]}.json").read_bytes())


def candidate(
    base: RunInput, updates: dict, configuration: str, model: str, price_reason: str = ""
) -> bytes:
    raw = base.model_dump(mode="json")
    raw.update(updates)
    family = "b200" if configuration == "cw-b200-8" else "b300"
    anchor = next(
        r
        for r in base.benchmark_references
        if r.model == model and r.benchmark_id.startswith(family + "-")
    )
    raw["configuration_id"] = configuration
    raw["workload"] = anchor.model_dump(mode="json")
    # Never carry B200 pricing into a B300 selection. A price is explicit and requires rationale.
    if configuration == "cw-b300-8" and raw["od_price_usd"] is not None:
        if not price_reason.strip():
            raise ValueError(
                "B300 price: provide a rationale for this assumed offer, or leave its price unavailable."
            )
        parent = next(e for e in base.evidence if e.input_id == "od_price_usd")
        override = Evidence.model_validate(
            dict(
                parent.model_dump(),
                input_id="ui:b300-price",
                value=raw["od_price_usd"],
                configuration_id=configuration,
                evidence_class="user_assumption",
                measurement_kind="hypothetical",
                source_id=None,
                source_url=None,
                source_locator="Explicit UI price assumption",
                observed_at_utc=None,
                raw_artifact_sha256=None,
                parent_input_ids=["offer:cw-b300-8-na-od"],
                rationale=price_reason,
                low=raw["od_price_usd"],
                base=raw["od_price_usd"],
                high=raw["od_price_usd"],
                zero_assertion="Explicit user zero" if raw["od_price_usd"] == 0 else None,
            )
        )
        raw["override_history"] = [
            e for e in raw["override_history"] if e["input_id"] != "ui:b300-price"
        ] + [override.model_dump(mode="json")]
    return json.dumps(raw, allow_nan=False).encode()
