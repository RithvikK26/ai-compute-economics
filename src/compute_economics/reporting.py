"""Deterministic, auditable reports and safe versioned scenario interchange."""

import csv
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from compute_economics.catalog import aggregate_ledger
from compute_economics.economics import evaluate_policy
from compute_economics.scenarios import decision_analysis
from compute_economics.schemas import Evidence, Policy, RunInput
from compute_economics.validation import read_table, validate_data, validate_run
from compute_economics.workload import build_demand

MAX_JSON_BYTES = 1_000_000
MISSING_EVIDENCE = [
    "Measured production throughput, wall power and workload quality on the exact rented/purchased system are unavailable; the transfer factor is assumed.",
    "Complete purchase, colocation and commitment quotes, deployment dates and actual inventory are unavailable. Cost and capacity defaults are hypothetical.",
    "B300 on-demand price is unavailable (contact sales). Its benchmark is a performance reference, not an eligible zero-priced alternative.",
    "B300 memory descriptions differ by configuration/provider; preserve raw values until exact-SKU memory is verified.",
    "Real demand distribution, usable life and residual proceeds need validation. No publicly audited matching ownership-versus-rental case validates the full TCO model.",
]
EXCLUSIONS = "Batch inference only; no latency SLO, backlog, cross-provider overflow, mixed fleet, training, replacement, taxes, debt interest, depreciation expense, company margin, facility construction or supply guarantee. Fixed owned operations include assumed site space/support/labor; workload-specific additional storage, egress and service overhead default to explicitly excluded zero. The 80%/20% blocks omit within-block bursts."


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _no_duplicates(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key: {k}")
        out[k] = v
    return out


def read_json(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("Scenario JSON exceeds 1 MB")
    obj = json.loads(
        raw,
        object_pairs_hook=_no_duplicates,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON number")),
    )

    def depth(x, n=0):
        if n > 20:
            raise ValueError("JSON nesting exceeds 20")
        if isinstance(x, dict):
            for v in x.values():
                depth(v, n + 1)
        elif isinstance(x, list):
            for v in x:
                depth(v, n + 1)

    depth(obj)
    return obj


def apply_overrides(run: RunInput) -> RunInput:
    """Retain the original evidence and append idempotent user-assumption records."""
    history = list(run.override_history)
    base = {e.input_id: e for e in run.evidence}
    known = {e.input_id for e in history}
    values = run.model_dump(mode="json")
    values["performance_tokens_s"] = run.workload.performance_tokens_s
    for key, parent in base.items():
        if key not in values or values[key] == parent.value:
            continue
        value = values[key]
        if isinstance(value, (dict, list)):
            value = canonical(value)
        override_id = "override:" + key + ":" + digest(value)[:12]
        if override_id in known:
            continue
        history.append(
            Evidence(
                input_id=override_id,
                value=value,
                unit=parent.unit,
                source_id=None,
                source_url=None,
                source_locator="Saved input edit",
                observed_at_utc=None,
                region=run.region,
                currency=parent.currency,
                configuration_id=run.configuration_id,
                evidence_class="user_assumption",
                measurement_kind="hypothetical",
                user_adjustable=True,
                confidence_note="User scenario override; original source retained",
                limitations="Override is not an observed market/benchmark value",
                raw_artifact_sha256=None,
                parser_version="1.0",
                review_status="reviewed",
                parent_input_ids=[key],
                rationale="Scenario input differs from frozen default",
                null_reason="Explicit unavailable/unconstrained user setting"
                if value is None
                else None,
                zero_assertion="Explicit user zero" if value == 0 else None,
                low=float(value) if isinstance(value, (float, int)) else None,
                base=float(value) if isinstance(value, (float, int)) else None,
                high=float(value) if isinstance(value, (float, int)) else None,
            )
        )
    return RunInput.model_validate(dict(run.model_dump(), override_history=history))


def validate_admission(run: RunInput, data: Path):
    manifest = validate_data(data)
    if (
        run.data_snapshot_id != manifest["snapshot_id"]
        or run.source_checksums != manifest["checksums"]
    ):
        raise ValueError("Snapshot ID/checksums do not match frozen data")
    original = [
        Evidence.model_validate_json(json.dumps(e))
        for e in json.loads((data / "assumptions.json").read_text())
    ]
    if [e.model_dump() for e in run.evidence] != [e.model_dump() for e in original]:
        raise ValueError("Original evidence modified; use input overrides, not source edits")
    parent_ids = {e.input_id for e in original}
    parent_ids.update("offer:" + o["offer_id"] for o in read_table(data, "offers"))
    for override in run.override_history:
        if (
            override.evidence_class != "user_assumption"
            or not set(override.parent_input_ids) <= parent_ids
        ):
            raise ValueError("Invalid override lineage")
    if run.configuration_id == "cw-b300-8" and run.od_price_usd is not None:
        if not any(
            "offer:cw-b300-8-na-od" in e.parent_input_ids
            and e.value == run.od_price_usd
            and e.evidence_class == "user_assumption"
            for e in run.override_history
        ):
            raise ValueError(
                "B300 price is null: an explicit price assumption referencing its quote-only offer is required"
            )
    configs = {x["configuration_id"]: x for x in read_table(data, "configurations")}
    if run.configuration_id not in configs:
        raise ValueError("Unadmitted configuration")
    if run.gpu_count != int(configs[run.configuration_id]["gpu_count"]):
        raise ValueError("GPU packaging mismatch")
    matching = [
        x
        for x in read_table(data, "benchmarks")
        if x["benchmark_id"] == run.workload.benchmark_id
        and x["configuration_id"] == run.configuration_id
    ]
    if not matching:
        raise ValueError("No exact workload/configuration benchmark association")
    b = matching[0]
    w = run.workload
    for field in ["model", "release", "scenario"]:
        if getattr(w, field) != b[field]:
            raise ValueError(f"Benchmark {field} mismatch")
    if w.measurement_kind == "benchmark_measurement":
        for field in ["quality", "dataset", "precision", "runtime", "topology"]:
            if getattr(w, field) != b[field]:
                raise ValueError(
                    f"Benchmark {field} mismatch; changed workload requires explicit user measurement"
                )
        if w.performance_tokens_s != float(b["value"]):
            raise ValueError("Altered throughput cannot be labeled observed benchmark")
    frozen_benchmarks = {b["benchmark_id"]: b for b in read_table(data, "benchmarks")}
    for reference in run.benchmark_references:
        anchor = frozen_benchmarks.get(reference.benchmark_id)
        if anchor is None or reference.performance_tokens_s != float(anchor["value"]):
            raise ValueError("Reference anchor mismatch")
        if any(
            getattr(reference, k) != anchor[k]
            for k in [
                "model",
                "quality",
                "dataset",
                "precision",
                "runtime",
                "topology",
                "release",
                "scenario",
            ]
        ):
            raise ValueError("Reference metadata mismatch")
    if w.workload_id != w.model + "-v6.1-offline":
        raise ValueError("Workload ID mismatch")
    if not run.historical_snapshot:
        errors = validate_run(run).errors
        if errors:
            raise ValueError("; ".join(errors))


def load_run(path: Path, data: Path):
    obj = read_json(path)
    envelope = None
    if "run_input" in obj:
        expected = {
            "schema_version",
            "created_at_utc",
            "run_hash",
            "expected_output_sha256",
            "run_input",
        }
        if set(obj) != expected or obj["schema_version"] != "1.0":
            raise ValueError("Invalid export envelope")
        envelope = obj
        raw = obj["run_input"]
        if digest(raw) != obj["run_hash"]:
            raise ValueError("Run hash mismatch")
    else:
        raw = obj
    run = RunInput.model_validate_json(json.dumps(raw, allow_nan=False))
    validate_admission(run, data)
    run = apply_overrides(run)
    return run, envelope


def safe_text(value):
    text = html.escape(str(value), quote=True)
    for char in ["\\", "`", "*", "_", "[", "]", "|"]:
        text = text.replace(char, "\\" + char)
    return text.replace("\r", " ").replace("\n", " ")


def safe_csv(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: safe_csv(v) for k, v in r.items()} for r in rows)


def money(value):
    return "unavailable" if value is None else f"${value:,.0f}"


def render_memo(run: RunInput, analysis: dict, selected_result=None) -> str:
    comparison = analysis["comparison"]
    risk = analysis["fixed_policy_demand_stress"]
    sens = analysis["sensitivities"]
    lines = [
        "# Conditional sourcing decision frontier",
        "",
        comparison["message"],
        "",
        "**Illustrative scenario using public reference data and analyst assumptions.**",
        f"Run `{digest(run.model_dump(mode='json'))}` · model {run.model_version} · snapshot {run.data_snapshot_id} · evidence review as of {run.analysis_as_of.isoformat()}.",
        "",
        f"Workload: **{safe_text(run.workload.model)} / MLPerf {run.workload.release} / Offline**. Quality: {safe_text(run.workload.quality)}. Dataset: {safe_text(run.workload.dataset)}.",
        f"Published reference: {run.workload.performance_tokens_s if run.workload.performance_tokens_s is not None else 'unavailable'} output tokens/s per complete node. Baseline transfer {run.transfer_fraction:.0%}; rental transfer {run.od_transfer_fraction:.0%}; productive availability {run.availability_fraction:.0%}/{run.od_availability_fraction:.0%}. These are distinct assumptions, not production measurements.",
        "",
        "## Decision frontier and reversals",
        "",
        f"Current lowest modeled present-value cost: **{money(comparison['lowest_pv_usd'])}** across {comparison['feasible_count']} feasible policies. Practical tie set (within 1%): {', '.join(comparison['tie_set']) or 'none'}.",
    ]
    lines += [
        "",
        "| Benchmark reference | System | Output tokens/s per submitted node | Role |",
        "|---|---|---:|---|",
    ]
    for reference in run.benchmark_references:
        lines.append(
            f"| {reference.model} / v6.1 Offline | {reference.benchmark_id.split('-')[0].upper()} × 8 GPUs | {reference.performance_tokens_s:,.1f} | {'Primary' if reference.model == 'gpt-oss-120b' else 'Secondary historical validation'} |"
        )
    lines += [
        "",
        "These are published system benchmarks with distinct workload quality requirements. B300 lacks a rental price; no financial ranking or cloud/owned equivalence is inferred from this table.",
    ]
    for name, frontier in analysis["frontier"].items():
        lines += ["", f"**{name.replace('_', ' ')}** — {frontier['status']}."]
        if frontier["points"]:
            lines.append(
                f"Tested range: {frontier['points'][0]['value']:g} to {frontier['points'][-1]['value']:g}; K is reoptimized at each point."
            )
        for switch in frontier["winner_switch_intervals"]:
            lo, hi = switch["bracket"]
            unit = ""
            if name == "acquisition_cost_multiplier":
                unit = f" ({money(lo * run.node_acquisition_usd)}–{money(hi * run.node_acquisition_usd)} per node)"
            util = switch["fixed_policy_utilization_bracket"]
            ulabel = ""
            if all(v is not None for v in util):
                ulabel = f" Selected fixed-policy utilization: {util[0]:.1%}–{util[1]:.1%}."
            lines.append(
                f"- The modeled decision changes between **{lo:g} and {hi:g}**{unit}: `{switch['from']}` → `{switch['to']}`.{ulabel}"
            )
        lines.append(
            "All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots."
        )
    lines += [
        "",
        f"Most influential tested assumption: **{sens['most_influential_tested_assumption'] or 'unavailable'}**. {sens['influence_definition']}",
        "",
        f"Stable across tested downside/base/upside demand paths: **{'yes' if risk and risk['stable_across_tested_demand_paths'] else 'no' if risk else 'unavailable'}**.",
    ]
    if risk:
        for name, p in risk["paths"].items():
            lines.append(
                f"- {name}: fixed `{p['fixed_policy_id']}`, scenario optimum `{p['scenario_optimum']}`, regret {money(p['regret_usd'])}, unmet {p['unmet_tokens']:,.0f} tokens; {'in' if p['in_tie_set'] else 'outside'} practical tie set."
            )
    lines += ["", "**Tested reversals:**"]
    for item in sens["tested_reversals"]:
        lines.append(
            f"- {item['assumption']} = {item['value']:g}: reoptimized policy `{item['winner']}`; selected policy unmet {item['fixed_policy_unmet_tokens'] or 0:,.0f} tokens."
        )
    if not sens["tested_reversals"]:
        lines.append(
            "No reversal in the disclosed one-at-a-time range; this does not establish global robustness."
        )
    for name, stress in analysis["named_stresses"].items():
        for path, p in stress["paths"].items():
            lines.append(
                f"- {name} ({path}): selected K stays {p['fixed_nodes']}; scenario optimum `{p['scenario_optimum']}`; regret {money(p['regret_usd'])}; unmet {p['unmet_tokens']:,.0f}; {'remains in' if p['in_tie_set'] else 'leaves'} tie set."
            )
    lines += [
        "",
        "## Policy comparison",
        "",
        "| Policy | Status | PV cost | Upfront | Contract obligation | Unmet tokens | Savings vs full-service OD |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for p in analysis["policies"]:
        lines.append(
            f"| {p['policy_id']} | {p['status']} | {money(p['pv_cost_usd'])} | {money(p['upfront_usd'])} | {money(p['obligation_usd'])} | {p['unmet_tokens']:,.0f} | {money(comparison['savings_vs_od_usd'][p['policy_id']])} |"
        )
    if selected_result:
        lines += [
            "",
            "## Cash flow and capacity",
            "",
            f"Selected-policy undiscounted TCO: {money(selected_result.tco_usd)}; upfront {money(selected_result.upfront_usd)}; obligation {money(selected_result.obligation_usd)}.",
            f"Levelized cost per million output tokens for the specified input/output workload: {money(selected_result.levelized_usd_million_tokens) if selected_result.levelized_usd_million_tokens is None else f'${selected_result.levelized_usd_million_tokens:.6f}'}. Zero-work costs are null.",
            f"Baseline execution utilization: {selected_result.execution_utilization if selected_result.execution_utilization is not None else 'undefined'}; available-capacity utilization: {selected_result.available_utilization if selected_result.available_utilization is not None else 'undefined'}. Unused commitment allocation {money(selected_result.unused_commitment_usd)} is part of existing spend, not an extra expense.",
            "",
            "| Cost category | Present value |",
            "|---|---:|",
        ]
        lines += [
            f"| {safe_text(k)} | {money(v)} |" for k, v in selected_result.category_pv_usd.items()
        ]
        lines += [
            "",
            "Monthly cash, block capacity, cost-category and annual operating/total cash ledgers accompany this memo. Positive values are costs; sale proceeds are negative once at the horizon.",
        ]
    lines += ["", "## Material missing evidence", ""] + ["- " + item for item in MISSING_EVIDENCE]
    lines += [
        "",
        "## Assumptions, provenance and scope",
        "",
        EXCLUSIONS,
        "",
        f"Synthetic demand scale stays {run.demand_scale_tokens_s:g} tokens/s regardless of hardware. This is the preserved teaching scale; it is not the primary benchmark throughput.",
        "",
        f"Source/runtime: {safe_text(run.workload.runtime)}. Precision: {safe_text(run.workload.precision)}. Topology: {safe_text(run.workload.topology)}.",
        safe_text(run.workload.transfer_differences),
        "",
        "No upfront cash constraint."
        if run.upfront_cash_limit_usd is None
        else f"Upfront cash limit: {money(run.upfront_cash_limit_usd)}.",
        "",
        f"Original observations and assumptions: {len(run.evidence)}; separately preserved overrides: {len(run.override_history)}. Full values, bounds, timestamps, locators, versions and artifact checksums are in scenario.json and provenance.csv.",
        "",
    ]
    for warning in comparison["warnings"]:
        lines.append("- " + safe_text(warning))
    lines += [
        "",
        "[CoreWeave prices](https://www.coreweave.com/pricing) · [Pinned MLPerf results](https://github.com/mlcommons/inference_results_v6.1/tree/10ecdffda3bb94d71f0203a6ca8e20c17943f27c) · [Pinned quality rules](https://github.com/mlcommons/inference_policies/blob/d3eba2f21026d868ad65cdcad2bb81e4a17ce3d3/inference_rules.adoc).",
        "",
    ]
    return "\n".join(lines)


def export_run(run: RunInput, output: Path, *, expected_output_sha256: str | None = None):
    analysis = decision_analysis(run)
    output_hash = digest(analysis)
    if expected_output_sha256 and expected_output_sha256 != output_hash:
        raise ValueError("Reproduction failed: output hash mismatch")
    winner = analysis["selected_policy_id"]
    selected = next(
        (
            Policy(family=p["family"], nodes=p["nodes"])
            for p in analysis["policies"]
            if p["policy_id"] == winner
        ),
        None,
    )
    # Export complete ledgers for every evaluated policy, not only the winner.
    detailed = [
        evaluate_policy(run, Policy(family=p["family"], nodes=p["nodes"]), build_demand(run))
        for p in analysis["policies"]
    ]
    selected_result = next(
        (r for r in detailed if selected and r.policy_id == selected.policy_id), None
    )
    output.mkdir(parents=True, exist_ok=True)
    envelope = {
        "schema_version": "1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_hash": digest(run.model_dump(mode="json")),
        "expected_output_sha256": output_hash,
        "run_input": run.model_dump(mode="json"),
    }
    (output / "scenario.json").write_text(json.dumps(envelope, indent=2, allow_nan=False) + "\n")
    (output / "results.json").write_text(json.dumps(analysis, indent=2, allow_nan=False) + "\n")
    (output / "decision_memo.md").write_text(render_memo(run, analysis, selected_result))
    write_csv(output / "monthly_ledger.csv", [r for p in detailed for r in p.monthly_ledger])
    write_csv(output / "block_ledger.csv", [r for p in detailed for r in p.block_ledger])
    costs = [r for p in detailed for r in p.cost_ledger]
    write_csv(output / "cost_ledger.csv", costs)
    write_csv(output / "annual_costs.csv", aggregate_ledger(costs) if costs else [])
    write_csv(
        output / "policy_comparison.csv",
        [
            {k: v for k, v in p.items() if not isinstance(v, (list, dict))}
            for p in analysis["policies"]
        ],
    )
    write_csv(
        output / "decision_surface.csv",
        [dict(p, tie_set=";".join(p["tie_set"])) for p in analysis["surface"]],
    )
    write_csv(
        output / "provenance.csv",
        [
            dict(e.model_dump(mode="json"), parent_input_ids=";".join(e.parent_input_ids))
            for e in run.evidence + run.override_history
        ],
    )
    return envelope, analysis
