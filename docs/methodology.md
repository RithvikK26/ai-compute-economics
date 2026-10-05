# Implemented methodology

The authoritative requirements are [the amended specification](build_specification.md) and [amendment](amendment.md). [The original design](original_build_specification.md) preserves the prior technical requirements; Git history retains the unedited development document. Economic methodology is unchanged.

Demand is generated once from the preserved 71,892.1 tokens/s teaching scale, 4/8 baseline equivalents, 80%/20% monthly duration blocks and 0.5% monthly growth. Actual UTC month hours include leap February. Demand is immutable across hardware; separate .5/1/1.5 multipliers are deterministic paths, not probabilities.

Each policy uses one homogeneous workload and configuration. Performance is published node throughput times an explicit transfer factor, distinct from productive availability. Baseline-first dispatch serves the minimum of demand and q × 3600 × availability × service nodes × block hours. Owned nodes serve only after commissioning and exclude spares. On-demand overflow is bounded; its allocated nodes are integer and paid hours include startup and billing-quantum rounding. Relative rounding tolerance is 1e-10. Physical ratio rounding is clamped only within 1e-9; greater violations raise errors. Neither safeguard creates service capacity.

Commitments are fixed-node take-or-pay contracts exactly matching the horizon. Time-zero setup and prepaid usage, remaining monthly payments, unused-paid allocation and full nominal obligation are distinct. Unused spend is an attribution of existing cost.

Owned cash includes complete nodes and separate incremental installation/network/storage costs at time zero. Operations and whole-node idle/load energy start after commissioning. All nodes, including spares, idle outside productive execution. Facility kWh applies PUE once. All-in colocation disables metered electricity/demand/space charges. Residual proceeds and exit cost enter once at the horizon. No debt interest, taxes or depreciation expense enters cash NPV. Economic life below the operating horizon excludes ownership; contract terms beyond the horizon are excluded without hiding liabilities.

Monthly end-period discount factors are (1+r)^(-t/12). TCO sums cash; present-value work uses the same monthly discounting as cost. Zero delivered work yields null unit costs. The reported denominator is output tokens for the specified input/output workload, not a universal token tariff.

Ranking requires meeting demand within relative 1e-9 and respecting the upfront cash limit. Null cash limit means the explicit 'No upfront cash constraint' scenario setting. Only feasible policies enter the 1% practical tie set or regret baseline. Negative net cost is allowed for unusual residual assumptions, with warnings. Bound warnings disclose finite search. All-on-demand is evaluated once, commitments K=1…32 and ownership K=max(1,spares+1)…32 by default; expansion is capped at 128.

Demand frontier: 0.25…2.0 in 0.05 steps. Acquisition line: 0.75…1.25 in 0.025 steps. Commitment line: $32…$48/node-hour in $1 steps. The 20×20 heatmap uses evenly spaced demand/acquisition multipliers. Actual billing and capacity are recomputed. All adjacent winner changes and selected-policy sign-change brackets are retained; there is no interpolation through discontinuities. No crossing in the tested range is an explicit result, not a global claim.

One-at-a-time sensitivities use the specification's endpoints. Residual stress is 0%/20% of each policy's node acquisition value. The fixed selected policy retains K; scenario optima are separately labeled. Influence is the range of the selected policy's cost advantage against the best feasible alternative across disclosed endpoints. This is an analytical ranking of tested decision sensitivity, not statistical confidence. Named stresses include demand disappointment, lower future rental price with zero residual, and a combined delay/limited-capacity/obsolescence case.

Run hashes cover canonical sorted full input JSON, versions, overrides, pinned source checksums and explicit evidence-review date. Export creation timestamp is excluded. Results receive a separate deterministic hash. All runs are local and offline; reports use deterministic templates rather than an LLM.

## Application boundary

The four-view Streamlit application calls the same validated reporting adapter as the CLI. Form submissions calculate a complete run; widget drafts do not alter saved results. Advanced JSON edits pass the same admission checks. Charts reshape emitted results only. Private temporary export directories are removed after their bytes are loaded into the session. Global caching is limited to public catalog tables.

A demand-disappointment scenario retains the fleet selected at time zero on the unshocked demand path. Its retrospective minimum is labeled separately. Frontier cells reoptimize the policy; fixed-policy stress and regret never silently resize the original fleet. White borders on the surface separate sampled winning fleets, not exact economic roots.
