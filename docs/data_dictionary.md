# Data dictionary and boundaries

Strict typed contracts live in schemas.py. Dates are ISO UTC/calendar dates; financial currency is USD only. Float64 calculations retain full machine precision; formatting is presentation only. Unknown values remain null with a reason; zero is an explicit assertion/exclusion. Numerical evidence classes are observed, derived, analyst_assumption, user_assumption and unavailable. User assumptions reference original input IDs and do not replace source observations.

- sources: exact URL, retrieval/review date, publisher, artifact hash and reuse note.
- configurations: actual provider/SKU, GPU count, topology context, raw memory and host notes. No inferred FLOPS throughput or unverified GB/GiB conversion.
- offers: exact region/product/billing unit, packaged-node price, inclusion flags, capacity status and unavailable-price reason. Not every catalog row is rankable.
- benchmarks: exact release/commit, submitter, system, model/quality/dataset, precision/runtime, whole-system node/GPU count, metric, accuracy, result path and system/rules references.
- compatibility: explicit workload/configuration association, transfer differences and review note. It never promotes a benchmark transfer to an observed deployment measurement.
- assumptions: original numerical defaults with evidence metadata; applicable sensitivity ranges are specified in methodology and machine-readable results.
- RunInput: immutable validated settings, workload identity, reference anchors, source checksums, evidence, override history, scenario and capacity/cash constraints.
- DemandTable: read-only NumPy arrays with unique period/block keys, common tokens and conserved monthly hours.
- PolicyResult: status, fixed node count, NPV/TCO, unit economics, utilization, obligations, service gaps, warnings and category/month/block ledgers.

Monthly ledger has time-zero plus actual calendar months. Cost ledger is long-form category × period and reconciles to monthly and total cash/PV. Block ledger separates baseline/overflow/unmet tokens and productive execution from allocated/billed hours. Annual summaries distinguish operating spend from total cash, including time-zero investment in model year one. Effective homogeneous GPU-hours, billed rental GPU-hours and owned calendar GPU-hours are different diagnostics.

SQL catalog inputs are exact CSV strings, with explicit casts where needed; this prevents silent CSV type inference. Source validation precedes construction. Database creation uses one private writer; query operations use separate read-only connections. There is no persisted user-scenario state in DuckDB.

## File contracts

| File | Grain / principal fields | Meaning |
|---|---|---|
| `data/sources.csv` | source ID; URL, retrieval/review date, artifact path/hash | Frozen source provenance |
| `data/configurations.csv` | configuration ID; node/GPU packaging, raw memory | System identity, not a performance estimate |
| `data/offers.csv` | provider/configuration/region/product | Price, billing boundary, inclusion flags, availability limits |
| `data/benchmarks.csv` | admitted whole-system benchmark record | Tokens/s, exact workload, quality, release, logs and topology |
| `data/compatibility.csv` | workload × configuration | Explicit transfer and compatibility treatment |
| `data/assumptions.json` | input ID | Original defaults and their evidence classifications |
| `scenario.json` | one run envelope | Schema/model versions, canonical run hash, expected output hash, full inputs, overrides; creation time is informational |
| `results.json` | one complete analysis | Policies, comparison, fixed-policy stress, sensitivities, frontier and surface |
| `policy_comparison.csv` | one policy | Feasibility, costs, service, warnings and metrics |
| `monthly_ledger.csv` | policy × period | Cash and discounted cash; period 0 is upfront |
| `block_ledger.csv` | policy × month × demand block | Demand, delivered work, unmet tokens, execution and billing |
| `cost_ledger.csv` | policy × category × period | Signed cash components and PV |
| `annual_costs.csv` | policy × model year | Operating versus total cash |
| `decision_surface.csv` | demand × acquisition test point | Reoptimized winner, cost, ties and assumed acquisition value |
| `provenance.csv` | evidence/override record | Value, units, source, parents, reason and limits |
| `decision_memo.md` | one run | Deterministic conditional interpretation and missing evidence |

Tokens mean output tokens for the named input/output workload. Rates use tokens/s per complete benchmark node or USD/node-hour as explicitly labeled. Demand is not regenerated when hardware changes. Empty CSV cells represent nulls, not zeros. Execution/paid-calendar utilization differs from execution/available-hours utilization; unused-paid share is an allocation, not extra spend. Percentages in the UI are presentation conversions of fraction-valued engine fields.

Schema `1.0`, economic model `0.1.0`; contracts are in [schemas.py](../src/compute_economics/schemas.py). Exported JSON is limited to 1 MB and depth 20. Unknown/duplicate keys, nonfinite numbers and incompatible versions are rejected. Free text is escaped for Markdown and CSV spreadsheet injection; user data are not executable inputs.
