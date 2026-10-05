# AI COMPUTE ECONOMICS & CAPACITY MODEL — BUILD SPECIFICATION

Research cutoff: September 27, 2026. Version 1.0. Historical technical requirements; current operation and validation are documented separately. Development-only instructions have been removed from this public copy.

This document defines the product, equations, data contracts, source requirements, interface, tests, and validation requirements. It uses public information and original analytical design. Company names identify research sources, not clients, partners, or endorsements. No employer-confidential information is required.

Evidence convention: [S01]–[S32] refer to exact URLs and acquisition instructions in Section 3. Numerical design defaults and test fixtures are explicitly assumptions, not market observations. Web pages were inspected or located on the research date; undated live pages are observations retrieved on that date, not verified historical time series. The implemented snapshot is pinned by its artifact manifest.

## 1. Executive Summary

**Build a transparent capacity-sourcing decision workbench for an AI operator with a defined inference workload.** The central question is: “How much baseline capacity should we own or commit to, and how much demand should we leave to on-demand rental, given uncertain demand, realistic system granularity, and uncertain performance?”

This is more useful than declaring one universally cheapest GPU or choosing exclusively between renting and owning. The tool should identify the lowest present-value cost among a small, explicitly enumerated set of sourcing policies, show when that answer changes, and disclose the evidence needed before taking action.

The primary user is a strategic-finance or infrastructure-planning analyst supporting a workload owner. The decision horizon is 36 calendar months by default. The MVP supports a single homogeneous workload per run, a single hardware configuration per policy, monthly demand blocks, and three policy families: all on-demand; a fixed number of committed systems plus on-demand overflow; and a fixed number of owned systems in leased colocation plus on-demand overflow. It does not design or finance a new data center.

The flagship case is gpt-oss-120b under MLPerf Inference v6.1 Offline, using the published CoreWeave B200 and B300 results and the applicable workload quality threshold. Retain Llama 2 70B 99.9 Offline as a secondary validation/reference workload for historical comparability [S10–S12]. Neither workload is a recommendation for a production model. Arbitrary production demand requires explicitly assumed or measured workload performance. H100/H200 can remain useful cost-only reference systems without invented token throughput.

Deliver a Python package, curated source tables, meaningful SQL transformations, a Streamlit application, a reproducible example decision memo, and tests. Use DuckDB as an embedded analytical layer over versioned CSV/JSON files. No external database, GPU, API key, or paid subscription is needed to run the finished demonstration.

The design emphasizes **decision integrity**: common workload denominators; explicit uncertainty; whole-node capacity; contract obligations; deployment delay; source provenance; and the ability to say “insufficient evidence.” It should not claim production infrastructure expertise, measured customer savings, or employer endorsement.

## 2. Market & Technical Scope

### 2.1 Relevant systems and their admission rules

Model a purchasable or rentable system, not an accelerator name alone. Every configuration includes provider/OEM, SKU, GPU count, memory as reported, interconnect, software context, and billing unit. “HGX B200,” “DGX B200,” and a cloud B200 instance are distinct configurations; equal chip names do not establish equal total cost or performance.

| System family | Evidence and current relevance | Product treatment |
|---|---|---|
| H100 SXM and H200 SXM | Public CoreWeave and Crusoe rental references; installed Hopper remains a relevant sourcing alternative [S01, S02] | Include 8-GPU cost reference rows; no default token performance from another generation or benchmark version |
| B200 HGX/DGX | Public node pricing, system documentation, and current inference results [S01, S03, S11] | Primary runnable workload demonstration; owned-system costs and performance transfer remain assumptions |
| B300 Blackwell Ultra | Current system documentation and available-category MLPerf results; some rental offers are quote-only [S04, S05, S11] | Include benchmark and catalog rows; financial comparison requires an explicit complete offer or user assumption |
| GB200 and GB300 NVL72 | Rack-scale architecture; cloud billing slices can be smaller than the physical 72-GPU domain [S01, S06] | Catalog/context only in MVP; full rack economics and topology enter Phase 2 |
| AMD MI300X, MI350X/MI355X | AMD publishes specifications and Crusoe advertises AMD capacity [S02, S07] | Record alternatives and portability risks; add decision-engine configurations only after matching workload evidence and all-in prices |
| NVIDIA Rubin | Vendor roadmap and MLPerf v6.1 preview-system evidence exist [S08, S12] | Watchlist/obsolescence context, not assumed generally procurable capacity; require a real SKU, offer, and compatible result to admit |
| Google TPU and AWS Trainium | Material custom-silicon alternatives; Ironwood documentation and Trn3 availability are public [S09a, S09b] | Research context in MVP; Phase 2 requires software-porting costs, workload parity, billing granularity, and validated throughput |
| A100, L40S, RTX PRO Blackwell | Potentially attractive for smaller or less memory-intensive inference; public pricing exists [S01, S02] | Excluded from initial decision catalog to avoid unsupported universal rankings; no claim that they are inferior |

Important inconsistency: NVIDIA’s B300 documentation reports 288 GB per GPU, whereas the inspected CoreWeave B300 offer/result reports 270 GB; other provider descriptions also differ [S01, S04, S11]. Preserve the provider’s raw value and unit convention. Do not silently replace it with a marketing value or assume that unit conversion alone resolves the difference. Effective memory must be verified for the actual SKU.

### 2.2 Sourcing models

**On-demand:** no modeled long-term minimum; pay for whole-system billed intervals. Unit price may bundle host resources but does not necessarily include storage, egress, or managed services. An advertised price is not proof of current capacity.

**Fixed-capacity commitment:** a modeled contract for K systems, paid throughout the horizon, with an explicit payment schedule and capacity status. The demonstration contract is hypothetical unless a complete public offer supports its exact terms. Never label a generic percentage discount “CoreWeave reserved pricing.”

**Ownership:** purchase complete systems and required incremental network/storage infrastructure; use leased, powered colocation. Include operations, maintenance, idle power, commissioning delay, and residual proceeds. No land, power-plant, construction, or project-finance model in MVP.

AWS Capacity Blocks are a distinct, scheduled product, not a generic three-year reservation. Savings Plans and capacity reservations must also be distinguished [S05, S13, S14]. Keep these records in the source catalog; the MVP does not emulate every provider’s commercial contract.

### 2.3 Workload boundary

MVP: one batch inference workload with a fixed model, quality threshold, prompt/output distribution, software configuration, and performance reference. Each demand block must finish inside that block. No backlog carryover or real-time latency claim. Independent workload replicas may scale across identical nodes; no cross-node tensor-parallel speedup is assumed.

Latency-sensitive inference is Phase 2: it requires a measured throughput-versus-latency curve, TTFT/time-per-output-token targets, realistic arrival patterns, and headroom. An Offline result cannot qualify an interactive service. Training is Phase 2: use measured end-to-end job duration, convergence/quality target, parallelism, checkpoint/restart overhead, and cluster topology. Do not infer training time from advertised FLOPS alone.

### 2.4 What belongs in the calculation

| Factor | Treatment | Why |
|---|---|---|
| Offer price, billed unit, GPU count, term | Observed where complete; otherwise explicit assumption | Direct cash-flow and granularity effect |
| Throughput, model, precision, software, benchmark scenario | Observed benchmark or user-supplied measurement; production transfer is assumed | Determines comparable delivered work |
| Demand, availability, commissioning date, spare nodes, capacity limits | User-adjustable assumptions | Determines feasible service and unused capacity |
| Acquisition, installation, network/storage, operating labor, support | Itemized assumptions unless public comparable quote exists | Essential to ownership economics; public precision is weak |
| Wall power, electricity, PUE | Measured when available; otherwise bounded assumptions | Material operating cost; no GPU-TDP substitution |
| Discount rate, residual proceeds, economic service life | User assumptions with sensitivity | Capital allocation and obsolescence |
| Memory/interconnect feasibility | Compatibility gate backed by execution evidence or disclosed assumption | Prevents nonsensical throughput comparisons |
| Financing structure, taxes, accounting depreciation | Financing and tax modules deferred; depreciation explanation only | Avoid double counting and false company specificity |
| Export constraints, site suitability, vendor reliability, portability | Qualitative checklist and hard eligibility overrides | Insufficient public evidence for numeric probabilities |

## 3. Data Source Map

The following sources are the acquisition map, not permission to fill every cell automatically. **O** = observed statement or published number; **A** = analytical/user assumption; **D** = derived. Reliability describes the stated fact, not whether it applies to a particular customer. All automatic refreshes stage proposed changes for review; no live scraping during an app session.

### 3.1 Hardware, offers, performance

| ID and exact public URL | Variables and classification | Acquisition and refresh | Reproducibility, reliability, limitations |
|---|---|---|---|
| S01 — [CoreWeave pricing](https://www.coreweave.com/pricing) | O: node prices, GPU count, region label, advertised memory, included host specifications | Manually transcribe selected North America rows with retrieval timestamp and short evidence extract; weekly review; automation unnecessary in MVP | Official list prices, not negotiated quotes or capacity guarantees. Dynamic spot rows unsuitable as stable defaults. Preserve inference-platform footnotes and node billing units |
| S02 — [Crusoe pricing](https://www.crusoe.ai/cloud/pricing) | O: advertised GPU-hour rates, quote-only status, storage and ancillary prices | Manual source table, weekly review | Exact instance packaging/region and applicable terms require validation. Do not assume a per-GPU headline grants single-GPU purchasing |
| S03 — [DGX B200 user guide](https://docs.nvidia.com/dgx/dgxb200-user-guide/introduction-to-dgxb200.html) | O: GPU count, memory, system topology, electrical specifications | Manual configuration extraction; quarterly and upon revision | DGX specifications do not establish HGX cloud-node wall power or acquisition price. Store document revision |
| S04 — [DGX B300 user guide](https://docs.nvidia.com/dgx/dgxb300-user-guide/introduction-to-dgxb300.html) | O: GPU/system specifications, system maximum power | Same as S03 | Maximum power is a bound, not measured workload consumption; OEM and cloud variants differ |
| S05 — [AWS Capacity Blocks pricing](https://aws.amazon.com/ec2/capacityblocks/pricing/) | O: effective instance-hour prices, region, accelerator count; D: per-accelerator normalization | Manual narrow snapshot weekly; official offer-query API is a Phase 2 option | Public indicative table is not a purchase confirmation. Exact dates, available blocks, OS, and ancillary charges matter |
| S06 — [NVIDIA GB300 NVL72](https://www.nvidia.com/en-us/data-center/gb300-nvl72/) | O: rack architecture, GPU count and aggregate memory; vendor performance claims retained as claims only | Manual quarterly review | Do not insert promotional multipliers into model throughput |
| S07 — [AMD MI355X](https://www.amd.com/en/products/accelerators/instinct/mi350/mi355x.html) | O: memory, bandwidth, board power and form factor | Manual quarterly review | Board power is not system power; peak arithmetic performance is not application throughput |
| S08 — [NVIDIA Vera Rubin platform announcement](https://nvidianews.nvidia.com/news/nvidia-vera-rubin-platform) | O: vendor-announced platform and availability timetable | Dated announcement; review monthly for actual SKU evidence | Roadmap statement, not proof of delivered customer capacity |
| S09a — [Google TPU7x documentation](https://docs.cloud.google.com/tpu/docs/tpu7x) and [TPU catalog](https://cloud.google.com/tpu) | O: supported architecture and system family | Manual quarterly review | Provider-specific software and provisioning; no GPU-equivalence assumption |
| S09b — [AWS Trn3 availability announcement](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-ec2-trn3-ultraservers/) | O: announced GA and system structure | Dated source; quarterly catalog review | GA does not prove inventory, workload portability, or lowest cost |
| S10 — [MLPerf Inference Datacenter](https://mlcommons.org/benchmarks/inference-datacenter/) | O: benchmark rules, category/scenario definitions, power methodology | Review per release; pin corresponding rules commit | Primary comparability authority; measured power applies to accompanying benchmark only |
| S11 — [v6.1 results repository](https://github.com/mlcommons/inference_results_v6.1), [summary CSV](https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/summary.csv) | O: system-level throughput, precision, scenario, division, status, result path | Download selected summary and necessary system/log metadata once; pin commit and SHA-256; update per release | Official downloadable result artifacts make automated narrow ingestion sensible. Submitted systems are not generic GPU measurements; use result-usage guidelines |
| S12 — [v6.1 technical overview](https://mlcommons.org/2026/09/chairs-mlperf-inference-v6-1/) | O: release scope, retained models, preview-category context | Dated article; each release | Useful interpretation, not a substitute for individual result metadata |

### 3.2 Contract, financial, operating and software evidence

| ID and exact public URL | Variables and classification | Acquisition and refresh | Reproducibility, reliability, limitations |
|---|---|---|---|
| S13 — [AWS Capacity Blocks billing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/capacity-blocks-pricing-billing.html) | O: purchase and payment semantics | Manual review before admitting an offer and quarterly | Do not treat prepaid blocks as cancellable on-demand usage |
| S14 — [AWS purchasing options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html) and [EC2 FAQ](https://aws.amazon.com/ec2/faqs/) | O: discount versus capacity-reservation distinction | Manual quarterly | Savings Plans alone do not reserve capacity |
| S15 — [Google GPU pricing](https://cloud.google.com/products/compute/gpus-pricing?hl=en) and [GPU commitments with reservations](https://docs.cloud.google.com/compute/docs/committed-use-discounts/purchase-commitments-with-reservations?hl=en) | O: GPU price components and applicable commitment/reservation rules | Manual exact SKU/region capture; weekly prices, quarterly terms | Machine-series rules vary; accelerator price may not be the full VM price. Catalog/API ingestion is Phase 2 |
| S16 — [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) and [capacity reservations](https://learn.microsoft.com/en-us/azure/virtual-machines/capacity-reservation-overview) | O: retail SKU rates, currency, region, term; O: reservation semantics | Official unauthenticated API suitable for Phase 2; paginate and retain raw response; weekly | Filter exact SKU, OS, meter, region, price type and effective date. Retail rates do not establish inventory or negotiated costs |
| S17 — [Oracle price list](https://www.oracle.com/cloud/price-list/) and [H200 shape guide](https://docs.oracle.com/en-us/iaas/Content/Compute/gpu-quick-start/nvidia/H200/README-H200.htm) | O: configuration and pricing-unit descriptions | Manual monthly; retrieve an official download if live values are not exposed | Inspection exposed configuration rows but not all numeric prices. Mark missing price unavailable. NVIDIA AI Enterprise add-on pricing is not the GPU compute price |
| S18 — [EIA electricity table 5.6.A](https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_6_a) | O: state/sector monthly cents per kWh; D: dollars per kWh | Official download or manual selected row; monthly; preserve release and observation months | Survey-based regional reference, not a data-center tariff. No automatic inference about demand charges, power agreements or colocation pass-through |
| S19 — [Google data-center efficiency](https://www.datacenters.google/efficiency/) | O: reported fleet PUE and measurement context | Manual annual snapshot | Reference only; not representative of the user’s colocation facility. PUE is not an extra markup on an already all-in electricity bill |
| S20 — [CoreWeave 2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000104/crwv-20251231.htm) | O: company accounting policy and capital/contract risk disclosures | Dated filing; annual policy review, quarterly material-risk review | Technology equipment useful life is six years in this filing. This is an accounting estimate, not proof of six-year economic competitiveness or a resale-price forecast |
| S21 — [DuckDB concurrency](https://duckdb.org/docs/current/connect/concurrency) | O: database process/concurrency behavior | Read official docs at dependency lock; recheck on upgrade | Supports the selected read-oriented architecture, not a multi-user transactional service |
| S22 — [SQLite appropriate uses](https://www.sqlite.org/whentouse.html) | O: embedded database tradeoffs | Same as S21 | Credible alternative when persistent transactional edits become central |
| S23 — [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), [resource limits](https://docs.streamlit.io/knowledge-base/deploy/resource-limits) | O: hosting/install requirements | Verify before deployment and on dependency upgrades | No assumed permanent disk, unlimited memory, or uptime guarantee. Local run remains the reproducibility standard |
| S24 — [OpenAI Strategic Finance Compute](https://openai.com/careers/strategic-finance-compute-san-francisco/) | O: publicly described work; analytical calibration only | Dated page note; check at portfolio launch | Job postings can change; not a promise of eligibility or an undergraduate hiring rubric |
| S25 — [OpenAI Compute and Infrastructure FP&A](https://openai.com/careers/director-compute-and-infrastructure-fpanda-san-francisco/) | O: capacity planning, unit economics and scenario-analysis responsibilities | Same as S24 | Senior role used to identify relevant work, not imply experience equivalence |
| S26 — [OpenAI infrastructure sourcing](https://openai.com/careers/strategic-sourcing-manager-compute-infrastructure-san-francisco/) | O: cross-functional commercial/technical sourcing responsibilities | Same as S24 | Calibration only |
| S27 — [Anthropic jobs](https://www.anthropic.com/careers/jobs?p=2) | O: compute finance, capacity and procurement role families | Manual dated review | Research verified role listings, not every role’s detailed duties. Section 12 explicitly identifies judgment-based calibration |
| S28 — [MLPerf inference rules](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc) | O: benchmark scenario and validity constraints | Pin matching-release policy revision; per release | A mutable branch must not substitute for the policies applicable to a frozen submission |
| S29 — [MLPerf Llama 2 benchmark](https://mlcommons.org/2024/03/mlperf-llama2-70b/) | O: benchmark motivation and task context | Fixed dated source | Does not establish that Llama 2 is the preferred current production model |
| S30 — [AWS accelerated instance specifications](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html) | O: instance GPU count, network and storage configuration | Monthly for admitted SKUs | Same accelerator in different instance families may have different host/interconnect constraints |
| S31 — [MLPerf v6.1 release](https://mlcommons.org/2026/09/mlperf-inference-v6-1-results/) | O: current release existence and scope | Fixed dated source | Latest release at research cutoff; later releases must not silently replace frozen results |
| S32 — [Crusoe B200 offering](https://www.crusoe.ai/cloud/gpus/nvidia-b200) | O: advertised availability, system family | Monthly | Contact-sales offering; public acquisition price and exact capacity not established |

### 3.3 Validated reference observations

Use these as starting source rows. Revalidate at build-time ingestion; preserve the research values as a dated snapshot rather than silently overwriting them.

| Observation | Raw public value | Normalized value / interpretation |
|---|---:|---|
| CoreWeave North America HGX H100, 8 GPUs [S01] | $49.24/node-hour | D: $6.155/GPU-hour; retain node billing |
| CoreWeave North America HGX H200, 8 GPUs [S01] | $50.44/node-hour | D: $6.305/GPU-hour |
| CoreWeave North America HGX B200, 8 GPUs [S01] | $68.80/node-hour | D: $8.60/GPU-hour |
| CoreWeave B300 on-demand [S01] | Contact sales | Null, not zero; no on-demand winner calculation without an assumption |
| Crusoe H100 / H200 headline [S02] | $3.90 / $4.29 per GPU-hour | Packaging/inclusions require confirmation before engine admission |
| AWS p5e.48xlarge Ohio Capacity Block [S05] | $47.76/instance-hour, 8 H200 | D: $5.97/GPU-hour; scheduled product, not an equivalent CoreWeave offer |
| AWS p6-b300.48xlarge Oregon Capacity Block [S05] | $112.32/instance-hour, 8 B300 | D: $14.04/GPU-hour; distinct contract and deployment configuration |

Primary workload-performance anchors from S11 are CoreWeave, available category, closed division, datacenter, gpt-oss-120b, Offline: B200-SXM-180GBx8_TRT = 91,487.4 output tokens/s and B300-SXM-270GBx8_TRT = 112,840 output tokens/s. Pin and validate the applicable quality rules, system, software and logs; preserve explicit production transfer assumptions.

Secondary historical validation anchors from S11: CoreWeave, available category, closed division, datacenter, Llama 2 70B 99.9%, Offline: **B200-SXM-180GBx8_TRT = 102,703 output tokens/s**; **B300-SXM-270GBx8_TRT = 115,530 output tokens/s**. Both are eight-GPU, FP4 submission configurations. Identify rows by submitter + system ID + model + scenario + release, then preserve each row’s result path, software metadata and logs. These are whole-system benchmark results, not measured production throughput or proof that every cloud instance matches the submission.

Do not join the B300 CoreWeave result directly to an AWS price and call the resulting estimate observed. A hardware/provider/software transfer is an assumption and must be visible. Do not use 99% quality rows for a 99.9% requirement, mix Offline and Server, divide a rack score into independently rentable slices without evidence, or pick the largest score without documenting the selection.

### 3.4 Inputs without defensible universal public values

Acquisition cost, colocation quote, idle/load wall power for the purchased configuration, labor burden, maintenance, production throughput transfer, delivery delay, uptime, customer demand, usable capacity limits, negotiated commitment rates, terminal resale proceeds and discount rate remain **A/U** by default. No universal “market price” is prescribed. Public listings can inform a range only after checking age, tax, warranty, system completeness, region, condition and purchase quantity. No paywalled index or proprietary data is required.

## 4. Assumption & Provenance Framework

### 4.1 Use two axes rather than conflating editability with evidence

Each numerical input has `evidence_class = observed | derived | analyst_assumption | unavailable` and `user_adjustable = true | false`. A user override creates a separate `user_assumption` record pointing to the original; it never edits the source observation. Unknown numeric values are null with a reason. Zero requires an explicit assertion.

An observed field means that the source published it, not that it has been independently measured or verified in production. Record `measurement_kind = list_price | vendor_spec | benchmark_measurement | financial_disclosure | survey_reference | user_measurement | hypothetical`.

Required provenance fields: `input_id`, `value`, `unit`, `source_id`, `source_url`, `source_locator`, `observed_at_utc`, `effective_at` if known, `published_at` if known, `region`, `currency`, `configuration_id`, `evidence_class`, `measurement_kind`, `user_adjustable`, `confidence_note`, `limitations`, `raw_artifact_sha256`, `parser_version`, `review_status`. For derived inputs add `formula_id`, `parent_input_ids`; for assumptions add rationale and low/base/high bounds. Schema fields irrelevant to a record may be null with a documented reason.

Every run stores `schema_version`, `model_version`, `data_snapshot_id`, source-table checksums, complete input values, override history, scenario IDs, comparison filters, and creation timestamp. Canonical sorted JSON excluding timestamp yields `run_hash`. Same inputs and versions must reproduce the same outputs. No generative-AI interpretation is needed in the application.

### 4.2 Freshness and confidence controls

Offer prices are stale after 30 days, benchmarks require review after 180 days or a known new release, configuration/contract rules after 180 days, and annual reference disclosures after 400 days. These are product-policy thresholds, not statistical confidence intervals. Historical scenarios retain their frozen values and display “historical snapshot”; fresh-mode recommendations cannot treat stale rows as current without an explicit acknowledgement.

Show separately: evidence completeness, data age, comparability status, and sensitivity of the decision. Do not compress these into a fabricated accuracy score. An assumed input may be perfectly reproducible but highly uncertain.

### 4.3 Missing data and eligibility

`eligible`: all required inputs present and compatible. `conditional`: usable only under named assumptions or unresolved live capacity. `ineligible`: incompatible workload, insufficient modeled capacity, invalid units, expired contract, or impossible system. `unavailable`: missing required price/performance/cost input. Missing essential inputs block that policy’s ranking, not the whole app.

The default demonstration is always labeled **illustrative scenario using public reference data and analyst assumptions**. Even complete public data cannot confirm actual delivery, quote acceptance, or production SLO compliance.

## 5. Economic Model

### 5.1 Governing conventions

All policies face the same demand blocks, workload quality requirement, time horizon, currency, and cost boundary. Use USD, calendar UTC hours, kW, kWh, bytes, whole nodes, output tokens, and monthly end-of-period operating cash flows. A user-facing label must say **cost per million output tokens for the specified input/output workload**, not a universal token price. Input-token processing is already represented by the benchmark’s workload and must not be added again as an arbitrary cost multiplier.

Use monthly periods t = 1…T; default T = 36, starting October 1, 2026. H_t is actual hours in month t, including leap-year effects. Demand blocks b partition each month: h_tb > 0 and sum_b h_tb = H_t. Default is two blocks, 80% and 20% of monthly hours, representing a simplified demand-duration profile. They are not a queue simulator or a forecast. Work cannot spill between blocks. Aggregation loses within-block bursts and must be disclosed.

No stochastic simulation in MVP. Evaluate three named deterministic demand paths: downside, base, and upside. The sourcing decision is fixed at time zero and cannot adapt after seeing the realized path. Avoid perfect-foresight optimization disguised as planning.

### 5.2 Variable dictionary

| Symbol / field | Unit and domain | Evidence and meaning |
|---|---|---|
| D_stb | output tokens, >=0 | A/U demand for scenario s, month t, block b |
| q_ref,j | output tokens/s per complete node, >0 | O benchmark or U measured value for exact workload/configuration |
| f_j | dimensionless, (0,1] | A/U transfer factor; q_j = q_ref,j × f_j. Captures performance portability, not demand utilization or uptime |
| a_j,t | fraction, (0,1] | A/U productive availability of allocated service hours; does not certify an SLA |
| K | integer nodes, 0…32 default search | A/U committed fleet or owned fleet, fixed for horizon |
| r_spare | integer, 0…K | A/U owned nodes held out of productive capacity; still paid and powered at idle |
| L | integer months, 0…T | A/U commissioning delay; owned service begins month L+1 |
| M_tb | integer nodes, >=0 | A/U maximum on-demand nodes obtainable concurrently in a block; null is unknown, never silently unlimited |
| p_OD,t | USD/node-hour, >=0 | O list rate plus explicit A/U future price path |
| p_C | USD/committed-node-hour, >=0 | O complete contract or A/U illustrative contract rate |
| F_setup; u_prepaid | USD/node; fraction [0,1] | A/U setup fee and prepaid fraction of total commitment obligation |
| C_node, C_install, C_net, C_storage | USD | A/U owned acquisition and incremental infrastructure; complete node, not bare GPU |
| F_t | USD/month | A/U incremental owned labor, support, colocation space and other fixed costs |
| P_idle, P_load | kW/node, 0<=idle<=load | O measured or A/U; entire IT node wall power excluding facility cooling |
| P_aux,t | kW, >=0 | A/U incremental shared storage/network IT draw outside node measurements |
| e_t; PUE_t | USD/kWh; ratio >=1 | A/U site tariff and efficiency, optionally grounded in O reference data |
| r | annual effective fraction, >=0 | A/U unlevered nominal discount rate matching nominal cash flows |
| R_T; C_exit | USD, >=0 | A/U terminal gross sale proceeds and disposal/exit cash costs |
| ell | integer months >=T-L | A/U usable service life after commissioning; no replacement in MVP |
| delta; h_start | hours, >0; hours >=0 | A/U billing quantum and paid startup time per on-demand node per block |
| X_j,stb; E_j,stb | tokens; productive node-hours | D delivered work and execution time |

Use `_usd`, `_hours`, `_kw`, `_kwh`, `_tokens`, `_fraction` suffixes in code. Canonical memory is bytes only when the source unit convention is unambiguous; retain raw memory text otherwise. Never use “GB” and “GiB” interchangeably. Float64 is sufficient for scenario calculations; round only display/export presentation values, not intermediate arithmetic. Preserve full numeric machine-readable exports.

### 5.3 Calculation order and gates

1. Load a frozen snapshot; validate foreign keys, units, source age and completeness.
2. Validate workload/system match and scenario compatibility. Reject a generic peak-FLOPS-to-token conversion.
3. Generate the common monthly demand blocks once. They cannot change with the candidate hardware.
4. Enumerate the bounded sourcing policies for each eligible configuration. No optimizer is needed.
5. Dispatch committed/owned baseline first, then on-demand overflow; calculate delivered and unmet work.
6. Build separate monthly cash-flow ledgers and cost-category ledgers; apply contract timing and terminal flows.
7. Calculate present-value cost, service coverage, utilization and unit costs.
8. Rank eligible policies; rerun the identical fixed policies under stress cases and sensitivities.
9. Export inputs, results, warnings and provenance together.

**Compatibility gate:** workload ID includes model/revision, benchmark release, quality target, dataset or prompt/output distribution, scenario, precision/runtime and node topology. A published benchmark proves execution only for that configuration. A provider or owned-system transfer must identify differences and use f_j with an explicit assumption warning. Changing model, context length or precision invalidates the default benchmark; the MVP does not estimate new throughput from memory size. A user performance input permits conditional analysis but cannot become “observed benchmark.”

### 5.4 Demand and capacity

For the seeded examples, define an immutable reference scale q_scale = 102,703 × 0.70 tokens/s. The 0.70 factor is a pedagogical assumption, not a validated production haircut. It defines synthetic token demand once; selecting a different hardware candidate must not rescale it.

Default base demand: D_base,tb = 3600 × q_scale × n_base,b × h_tb × (1+g)^(t-1), with n_base,b = 4 and 8 for the two blocks and g = 0.005 monthly. Downside = 0.5 × base and upside = 1.5 × base. These are scenarios, not forecast percentiles. Demand editor accepts monthly/block token values; later versions may import a demand file.

For long-term baseline j:

- Committed service-node count N_t = K during the entire contract horizon.
- Owned service-node count N_t = 0 for t<=L, otherwise K-r_spare.
- Available work capacity Q_j,tb = 3600 × q_j × a_j,t × N_t × h_tb.
- Baseline delivery X_j,stb = min(D_stb, Q_j,tb).
- Productive execution E_j,stb = X_j,stb / (3600 × q_j), in node-hours.
- Overflow demand V_stb = D_stb - X_j,stb.

On-demand uses the same admitted hardware configuration within a policy, with its own q_OD and a_OD. Cross-provider overflow is excluded unless explicitly represented as a separate compatible configuration in Phase 2. For all-on-demand, X_baseline=0 and V=D.

This is aggregate productive availability, not probabilistic failover. Spare nodes are deliberately withheld; a separately entered a captures residual productive downtime after the modeled redundancy. The user must not count the same outage twice. No multi-site uptime guarantee is implied.

### 5.5 On-demand allocation and billing

The billing model is explicit and conservative. Default delta = 1 hour and h_start = 0 are modeling assumptions; they are not asserted provider rules. Each block represents one provisioning window. Billed idle, startup and rounding are paid, while throughput is credited only to productive hours.

For block duration h and max nodes M:

1. Per-node maximum useful allocated hours B_max,node = max(0, floor(h/delta)×delta - h_start).
2. Maximum deliverable overflow Q_OD = 3600 × q_OD × a_OD × M × B_max,node.
3. X_OD = min(V, Q_OD); if X_OD=0, allocated nodes and billed hours are zero.
4. Required productive-adjusted allocated hours B_req = X_OD/(3600×q_OD×a_OD).
5. Choose the smallest integer n in 1…M such that n×B_max,node >= B_req. Split B_req equally over those n nodes for this simplified divisible-batch scheduler.
6. Paid hours B_paid = n × delta × ceil((B_req/n + h_start)/delta).
7. C_OD,tb = p_OD,t × B_paid + c_variable × X_OD/10^6 + C_OD,ancillary,tb.

Numerical tolerances must prevent exact multiples from rounding up because of floating-point noise; use a documented relative tolerance of 1e-10 in ceiling helpers. Check each billed per-node duration <=h. If the quantum is longer than the block, the block cannot admit a node. D=0 never provisions on-demand capacity.

`c_variable` is an optional USD/million-output-token cost only for a specifically justified variable service. Default zero is an explicit exclusion, not evidence that all ancillary services are free. Ancillary costs use mutually exclusive fixed-monthly, per-billed-node-hour, per-GB egress and GB-month storage items. Each item declares whether the base offer already includes it. Do not add electricity, host CPU/RAM, or local storage again when included in the node price. Shared workload overhead appears once per policy, never once per source family.

Unmet tokens U_stb = D_stb - X_baseline,stb - X_OD,stb. No implicit unlimited overflow. Unknown M permits an explicitly assumed-capacity demonstration but blocks an unconditional capacity conclusion. Base-first dispatch values already-paid baseline capacity ahead of overflow; rare cases where owned marginal energy exceeds rental cost are flagged as outside this dispatch policy. They require Phase 2 economic dispatch rather than a claim of global optimality.

### 5.6 Commitment cash flows

MVP supports one fixed contract whose service term equals T months. No early cancellation, renewal, resale, workload pooling, or credits. A missing term is invalid; a term beyond the horizon is rejected rather than hiding a tail liability.

Total nominal usage obligation O_C = K × p_C × sum_t H_t. At time zero: C_C,0 = K×F_setup + u_prepaid×O_C. Month t: C_C,t = (1-u_prepaid)×K×p_C×H_t + incremental commitment fees_t + overflow_t + shared overhead_t.

Any additional usage-based charge is itemized. This is a fixed-node take-or-pay representation; it is not a generic implementation of AWS Savings Plans, GCP CUDs, or AWS Capacity Blocks. p_C is paid for unused and modeled unavailable hours; service credits default to zero, explicitly excluded.

Commitment execution utilization = sum E_C / (K×sum H_t). Available-capacity utilization = sum E_C / sum(K×H_t×a_C,t). Both are ratios of summed quantities, not averages of monthly ratios. The unused-paid share is 1-execution utilization; it includes inactivity and unavailable hours. Label this precisely.

Allocated unused commitment spend = O_C × unused-paid share. This is an explanatory allocation of existing spend, not an additional expense or fully avoidable cost. Show contractual obligations separately from unused-capacity attribution.

### 5.7 Ownership cash flows and power

Upfront incremental investment C_0 = K×C_node + C_install + C_net + C_storage. Fixed infrastructure amounts apply only when K>0. Costs must come from an itemized bill of materials; an all-in system quote and its included components cannot both be charged.

During t<=L, ownership capacity delivers no work; use overflow or report unmet demand. Upfront purchase occurs at time zero in MVP. Pre-commissioning storage/site costs are an explicit monthly input, default zero with exclusion note. Operational F_t and IT power begin in month L+1.

After commissioning, E_t = sum_b E_owned,tb. All K nodes, including spares, idle when not executing. The transparent first-order energy approximation is:

E_IT,t = K×P_idle×H_t + (P_load-P_idle)×E_t + P_aux,t×H_t [kWh].

E_facility,t = E_IT,t×PUE_t. Electricity cash expense = E_facility,t×e_t. Linear power interpolation is an assumption; utilization is workload execution duty cycle, not GPU SM telemetry. P_load must represent whole-node workload power. Never multiply GPU TDP by eight and present it as measured node consumption. Do not use a PSU nameplate sum as average demand.

Two mutually exclusive hosting modes:

- `metered_energy`: electricity above + space/connection fee + explicit demand charge (`contracted_kw × usd_per_kw_month`) + other site fees. PUE applied once.
- `all_in_colo`: total quoted monthly colocation/power charge; separate metered electricity and demand-charge costs disabled. Energy may still be displayed diagnostically.

Owned monthly cost C_O,t = F_t + hosting/energy_t + overflow_t + shared workload overhead_t. Support and labor may be fixed, per-node, or percentage of acquisition, but never simultaneously for the same service. Default use fixed annual USD amounts converted to equal monthly payments. Add one-time shutdown/exit costs C_exit at T and gross sale proceeds R_T at T.

R_T is an independent user estimate, not straight-line book value. Allow zero residual; warn when residual exceeds initial asset purchase cost. Negative resale is represented by C_exit, not a negative asset price. Economic service life ell must cover T-L; otherwise reject the ownership policy in MVP. Phase 2 will model replacement explicitly.

### 5.8 Discounting, cost, and unit economics

Let d=(1+r)^(1/12)-1. Positive costs and negative sale proceeds enter the cash-flow ledger:

PV_cost = C_0 + sum_(t=1)^T C_t/(1+d)^t + (C_exit-R_T)/(1+d)^T.

For rental and commitment, C_exit=R_T=0 unless a supported contract explicitly requires an exit payment. Savings NPV versus all-on-demand = PV_cost,OD - PV_cost,policy. Positive means the policy has lower modeled present-value cost, provided equivalent service is delivered.

Undiscounted TCO = C_0 + sum C_t + C_exit - R_T. Show annual operating spend and annual total cash spend separately; year one includes upfront capex. “Fully loaded” means the declared modeled boundary, not company-wide cost of revenue.

PV_work = sum_t delivered_tokens_t/(1+d)^t. Levelized cost per million output tokens = 10^6 × PV_cost/PV_work. This matched discounting is a planning metric, not a cash invoice price. Also show undiscounted TCO / total delivered millions. If delivered work=0, unit cost is undefined (null), never zero. Do not rank a cheap policy that fails to deliver the same demand.

For a homogeneous g-GPU configuration, delivered effective GPU-hours = g×sum_j,t,b E_j,tb. Undiscounted effective GPU-hour cost = TCO / delivered effective GPU-hours. Also show billed rental GPU-hours and owned calendar GPU-hours as distinct diagnostics. Do not aggregate heterogeneous GPU-hours across hardware families or use them to decide which GPU is fastest per dollar.

Optional informational accounting view: straight-line depreciation = max(0, depreciable_basis-book_residual)/book_life_months after commissioning. It is not part of pretax cash TCO or NPV. Show only in methodology, not required MVP output. Cost of capital already enters discounting; do not also add annual “financing cost” or interest to unlevered cash flows. Debt amortization, tax shields, tax depreciation and leases are Phase 2.

Contribution margin is excluded from the MVP. In Phase 2, compute revenue from input and output volumes with their respective realized selling prices; subtract a complete variable cost boundary. Do not relabel “revenue minus GPU rental” as company gross margin.

### 5.9 Breakeven formulas and decision surfaces

For a deliberately simplified steady state with matched hardware/performance, constant availability folded into productive capacity, divisible rentals, no startup/rounding, no overflow, no delay and no ancillary cost differences:

- Annual productive capacity Q = N×H×a, in productive node-hours.
- Annual fixed ownership burden F includes equivalent annual capital cost, fixed operations and idle-energy cost.
- Variable owned cost v = (P_load-P_idle)×PUE×e, USD/productive node-hour.
- Matched rental marginal cost p = p_OD/a_OD, USD/productive node-hour.
- Own-versus-rent breakeven u* = F/[Q×(p-v)].

F uses capital recovery, not depreciation plus financing. With n annual periods, annual rate r, investment C and terminal R: capital PV = C-R/(1+r)^n; CRF = r/[1-(1+r)^(-n)], or 1/n if r=0; annual capital charge = capital PV×CRF.

If p<=v and F>0, ownership has no cost breakeven under these assumptions. If u*>1, no feasible breakeven; if F=0, examine marginal costs rather than dividing blindly. Commitment breakeven against on-demand under identical availability and no setup/prepayment effects is used-share = p_C/p_OD. These closed forms are educational cross-checks, not the primary answer.

Primary crossover: rerun the actual calendar/billing model over demand multipliers. Report all sign-change intervals, integer capacity jumps, and “no crossing in tested range.” Do not force one root on a discontinuous cost curve. Use demand multipliers from 0.25 to 2.0 in increments of 0.05 for the MVP view; display a bracket rather than spurious decimal precision.

Required sensitivities: demand × acquisition-cost multiplier; one-at-a-time demand, transfer factor, rental price, commitment price, discount rate, electricity price and residual value. Low/high defaults are illustrative: acquisition 0.75×/1.25×, throughput transfer 0.50/0.90, electricity $0.05/$0.15 per kWh, annual discount rate 5%/15%, residual 0%/20% of node acquisition, rental future-price change -20%/0%/+20% from month 13. All are A/U, not observed confidence intervals.

For the default one-at-a-time commitment-price test use $32/$40/$48 per node-hour; for demand use 0.5×/1.0×/1.5× the frozen base schedule. Heatmap uses 20 evenly spaced demand multipliers from 0.25 to 2.0 and 20 acquisition multipliers from 0.75 to 1.25; the separate crossover line retains the finer 0.05 demand step above. Recompute all policy quantities after an input changes. Display the selected bounds and avoid implying that a narrow grid establishes global robustness.

Keep correlated assumptions together in an “obsolescence stress”: lower future rental prices and residual value jointly. Do not independently improve throughput on old hardware merely because a new generation launches. Changing useful life below horizon blocks ownership until the horizon is shortened or replacement modeling exists.

### 5.10 Conditional comparison and uncertainty logic

Enumerate all-on-demand once, committed K=1…32, owned K=max(1,r_spare+1)…32, for each fully specified configuration. K is fixed across demand paths. User-configured search bounds are capped at 128; show a warning if the best policy lands at the upper bound. This is optimal only within the enumerated policy family, bounded fleet sizes and dispatch assumptions.

Default objective: minimize base-case PV_cost subject to meeting all modeled demand (relative unmet tolerance 1e-9) and user upfront cash limit. Report feasibility independently in downside and upside. If no feasible policy exists, return “No modeled policy meets demand,” with shortages and required capacity evidence. Do not monetize shortages without user-supplied economic losses.

The upfront cash limit defaults to null with the visible label “No upfront cash constraint”; a numeric zero forbids upfront spending. Include capex, contract prepayments and setup charges in that constraint. Do not interpret an unknown borrowing capacity as unlimited financing. Comparison baselines and regret are unavailable when the relevant full-service baseline or scenario optimum is infeasible; never subtract a partial-service cheap case from a full-service case.

Show “lowest modeled cost,” not “buy this hardware.” Policies within 1% of lowest feasible PV cost form a practical tie set; 1% is a UX convention. Present upfront cash and contractual obligations to help select among them, without pretending the difference is statistically significant. A candidate is “stable across tested demand paths” only if it belongs to each path’s tie set and is feasible in each. Otherwise state exactly which stress reverses the result.

For each path, regret = PV_cost,fixed_policy - minimum feasible PV_cost in that path, provided the policy is feasible. If infeasible, report unmet demand instead of finite regret. No scenario probabilities or probability of winning in MVP. The sensitivity display must say whether it holds K fixed or reoptimizes K. Default show both: fixed-policy downside exposure and separately the best policy at each grid point.

### 5.11 Required demonstration presets

All are synthetic and labeled as such. Default hardware reference is CoreWeave B200; q_ref and p_OD use the observations in Section 3. Set f=0.70, a=0.98, on-demand M=32, T=36, L=0, r_spare=0, r=10%, delta=1 hour, no startup, nominal price escalation=0. Owned hypothetical node acquisition=$400,000; incremental one-time infrastructure=$50,000 when K>0; fixed owned operations=$24,000/year plus $4,000/node/year; P_idle=2 kW, P_load=10 kW, P_aux=0; PUE=1.25; electricity=$0.10/kWh; residual=0; usable life=36 months. Hosting mode metered; the fixed operations placeholder includes assumed site space/support and labor, with explicit exclusions in the memo. Contract price=$40/node-hour, setup=0, prepayment=0, fixed term=36 months. These amounts are round-number teaching assumptions, not vendor quotes or evidence of market acquisition costs.

1. **Stable demand:** use the base schedule from 5.4; demonstrate capital commitment versus steady volume.
2. **Demand disappointment:** the selected base policy is held fixed; realized demand falls to 50% from month 7; show paid idle capacity and regret. No retroactive fleet resizing.
3. **Delayed capacity:** owned commissioning delay L=6, on-demand M=4, same demand. Show overflow and unmet work; do not let cheap unavailable ownership win.

The released application must include at least one completed example memo with actual engine results after the tests pass. This specification does not assert a winning policy or computed savings for these unimplemented examples.

## 6. Product / UX Design

### 6.1 User journey

Open a worked example, read the workload and evidence banner, inspect demand, choose an admitted configuration, review sourcing assumptions, and run the comparison. The user then tests the two assumptions most likely to change the answer and exports a reproducible decision memo. The first screen should communicate the decision and limitations without requiring knowledge of every formula.

Use four views, not a sprawling dashboard:

| View | Controls and content | Decision it supports |
|---|---|---|
| Decision | Visually prominent decision frontier / breakeven surface; workload/preset; horizon; demand path; selected systems; capacity and upfront-cash limits; result cards for cost, cash, obligations, service coverage | Which modeled sourcing policy is cheapest and feasible? |
| Economics | Editable itemized costs, contract payment terms, owned commissioning, power and residual; monthly cash-flow ledger; annual cost breakdown | Why does the choice win and what must be funded? |
| Risk and capacity | Demand paths, capacity constraints, fixed-policy stress, sensitivity grids, utilization and unserved volume | What could reverse the decision or leave work unserved? |
| Evidence and methodology | Source table, timestamps, benchmark compatibility, observed/assumed values, exclusions, formula explanations | Which conclusions are supportable and what evidence is missing? |

Result headline example template: “Under [named assumptions], [policy and K] has the lowest modeled cost among [number] feasible policies. The choice changes when [tested condition]. [Critical unknown] needs validation.” Generated deterministically from results; no LLM dependency.

### 6.2 Visuals and tables

- Hero decision frontier / breakeven surface on the main Decision view: show the current lowest modeled cost among feasible policies, utilization/demand switch thresholds, acquisition-cost or commitment-price switch thresholds, dominant uncertain assumption, tested reversals, stability across tested demand paths, and material missing evidence. Complement all existing tables, cash-flow, capacity, sensitivity and provenance outputs. Use “Under the selected assumptions, [policy] has the lowest modeled cost” and “The decision changes when [variable] crosses [threshold].” No unconditional procurement recommendations.
- Capacity-versus-demand chart: for the selected scenario, show token demand, baseline served, overflow served and unmet work over time. Shortage must remain visible, never stacked as delivered output.
- Monthly cash-flow chart: upfront outlay at time zero, operating payments, terminal proceeds; reveal liquidity differences hidden by unit cost.
- Cost-component bars: compare capital, operations, energy, contractual spend and overflow on a consistent PV basis. Residual proceeds are a separate negative component.
- Policy comparison table: hardware/configuration, K, PV cost, savings versus baseline, upfront cash, obligation, unused-paid share, unmet tokens, evidence status.
- Heatmap: demand multiplier versus acquisition cost; categorical lowest-cost policy plus hover costs and assumption labels. Infeasible/missing-data cells are visibly distinct.
- Fixed-policy sensitivity chart: dollars of PV impact for transparent low/base/high inputs, not statistical confidence bounds.
- Source/assumption table: value, unit, source/date, status, override and reason. Clickable URLs, downloadable inputs and ledger.

Limit the initial screen to a few result cards, the policy table and the prominent decision-frontier chart. Advanced controls live in expanders with units and definitions. No gauges, GPU stock photography, fabricated live counters, or rankings by peak FLOPS. Display dollars to two decimals only for rates; large costs to nearest $1,000; utilization to one decimal percentage point; full precision remains in JSON/CSV.

### 6.3 State and export rules

Run calculations on form submission, not every slider movement. Invalid settings show field-specific errors without replacing the last valid result. Explicitly separate “saved input scenario” from “computed result.” Two concurrent users must have isolated state.

Exports: one JSON scenario containing all required data references and assumptions; one CSV monthly/block ledger; one Markdown decision memo containing workload, policy, costs, tested reversals, missing evidence and scope exclusions. No PDF generation or cloud persistence is needed in the MVP. Import only the application’s validated versioned JSON schema, maximum 1 MB; reject unknown keys, nonfinite values and incompatible schema versions. Browser downloads must not store other users’ scenarios.

## 7. Technical Architecture

### 7.1 Stack and storage decision

Recommended stack: Python 3.12 as the initial compatibility target; pandas and NumPy for explicit tabular/vector calculations; DuckDB for relational validation, source joins and aggregations; Pydantic strict models for input/output contracts; Streamlit for controls and tables; Plotly for interactive charts; pytest for tests; Ruff for lint/format checks. Pin tested dependency versions and commit the lockfile during implementation. Do not guess the latest patch versions from this specification.

| Storage choice | Fit | Decision |
|---|---|---|
| CSV/JSON only | Most transparent, easy to diff; requires explicit types and joins | Canonical source and scenario interchange formats |
| DuckDB | Embedded analytical SQL over local tables; straightforward reproducibility | Selected analytical layer; derive a small read-only database from validated source files [S21] |
| SQLite | Good embedded transactional database; useful for persistent edits [S22] | Credible alternative, unnecessary when scenarios live in session state/downloads |
| PostgreSQL | Appropriate for concurrent shared writes, accounts and central persistence | Exclude; no MVP need justifies a managed service, migrations and credentials |

Do not maintain two independent sources of truth. Versioned source tables are canonical; `catalog.duckdb` is rebuildable and normally gitignored. On app startup, build it once from the pinned snapshot in a temporary runtime directory, close the writer, then use a separate read-only connection for each query operation. Cache immutable query results rather than a shared mutable connection. User scenarios never write into this database. Local single-command preparation may prebuild the file.

Streamlit is the simplest appropriate frontend. React/FastAPI would add API contracts, deployment surfaces and frontend work without improving the key analytical task. Reconsider only if product requirements expand to collaborative scenario management or sophisticated client-side interaction.

### 7.2 Data contracts

| Table/object | Required business fields beyond common provenance |
|---|---|
| `sources` | source_id, publisher, title, url, retrieval date, effective date, license/reuse note, review date, artifact hash |
| `configurations` | configuration_id, vendor/provider/OEM, SKU, family, GPU count, topology, memory raw value/unit, optional verified bytes, status, CPU/RAM/storage notes |
| `offers` | offer_id, configuration_id, source_id, region, currency, pricing_kind, raw price/unit, normalized node-hour price, minimum node count, inclusion flags, capacity status, term/payment metadata, admission status |
| `benchmarks` | benchmark_id, configuration_id, release/commit, submitter, system ID, model, dataset/quality, scenario, precision, runtime, node count, GPU count, metric/unit/value, result path, availability category |
| `compatibility` | configuration_id, workload_id, benchmark_id, match_level, differences, required transfer assumption, reviewer note |
| `assumptions` | assumption_id, group, value/unit, bounds, rationale, editable, explicit-exclusion flag |
| `demand_blocks` | scenario_id, period, block_id, duration_hours, demand_tokens; unique composite key |
| `RunInput` | versions, selected configuration, frozen offers, own/commit assumptions, horizon/calendar, demand paths, capacity limits, cash limit, sensitivity selections |
| `PolicyResult` | policy_id, status, fixed K, configuration, objective/metrics, warnings, monthly ledger, block service ledger, source dependencies |

`offers` is a source catalog, not a promise that every observed product is engine-supported. AWS block, quote-only and incomplete-packaging rows remain catalog-only. Exactly identify the supported normalized contract before exposing it in controls.

SQL must do real work: deduplicate latest eligible observations as of a snapshot cutoff using a window function; join offers to configurations and sources; expose missing cost/benchmark coverage with left joins; aggregate comparison ledgers by cost category and year. Include at least three readable `.sql` files and tests that detect bad joins. Financial formulas live once in Python, not duplicated in SQL and UI.

### 7.3 Module boundaries and data flow

`ingestion` reads local source artifacts and curated tables; `validation` checks schemas/provenance; `catalog` creates analytical views; `workload` creates immutable demand; `capacity` calculates service and billing; `economics` creates cash flows; `scenarios` enumerates policies and stresses; `reporting` creates tables/memos; `ui` renders them. No module below UI imports Streamlit.

Core function contracts:

- `validate_run(run_input) -> ValidationReport`: field errors, policy exclusions, warnings, source freshness and compatibility; no hidden coercion.
- `build_demand(run_input) -> DemandTable`: independent of evaluated hardware.
- `evaluate_policy(run_input, policy, demand) -> PolicyResult`: deterministic, no I/O, no global state.
- `compare_policies(results, constraints) -> ComparisonResult`: eligibility, tie set and cheapest modeled result.
- `evaluate_stress(run_input, fixed_policy, named_paths) -> StressResult`: never reselects K.
- `render_memo(run_input, comparison, stress) -> str`: deterministic Markdown with explicit assumptions and provenance.

The ledger must contain period/block, demanded/served/unmet tokens, baseline and overflow execution hours, on-demand node count and billed hours, committed/owned capacity, idle hours, energy, each cash cost, residual/exit flow, discount factor and discounted values. Aggregate monthly cash costs without counting a shared monthly fee once per block.

### 7.4 Ingestion, security and reproducibility

MVP ingestion is a documented manual process plus one narrowly scoped MLPerf summary parser. Do not scrape every provider. Use official downloads and APIs only where stable; any network importer writes a staged artifact and manifest, then validates before replacement. Offline app operation is mandatory after installation.

No secrets or credentials required. No arbitrary URL fetch, SQL console, shell invocation, pickle import, macros or executable uploads from the UI. Validate JSON size/depth and numeric bounds; escape user labels in generated Markdown/HTML contexts; protect CSV exports from spreadsheet formula injection in free-text fields. Do not log uploaded scenario payloads on a public host. Cache only public catalog data globally; scenario results remain session-specific unless cached by a complete immutable key without personal text.

Use MIT or Apache-2.0 for original code after author choice; retain upstream license/attribution for reused benchmark facts/artifacts. Do not redistribute model weights, entire provider websites, or company logos. The repository’s original code license does not relicense third-party data. Keep narrow source extracts and metadata sufficient for review, respecting source terms.

### 7.5 Deployment design only

Target later deployment to Streamlit Community Cloud from GitHub [S23]. Use one entry point `app.py`, explicit Python runtime and an exported pinned `requirements.txt` matching the lockfile. Local setup is authoritative if hosted limits or availability change. Provide an optional container only after a concrete deployment need; Docker is not an MVP requirement.

No scheduled scraper, background worker, database server, GPU runtime or paid API. Hosted filesystem is disposable; all required public fixtures ship with the repository. Downloaded user scenarios remain the persistence mechanism. This specification authorizes design only; implementation and publication occur in the subsequent build task.

Engineering targets, to be measured rather than advertised as achieved: <3 seconds warm comparison for one configuration, 65 policies, 36 months, two blocks and three paths on a documented ordinary laptop; <10 seconds for a 20×20 sensitivity grid after precomputation; <512 MB process RSS for the demonstration if feasible. If missed, profile and simplify before adding infrastructure. Record machine and package versions. These are acceptance targets, not current measured performance.

Supplemental implementation references: [Pydantic strict mode](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/), [pytest parameterization](https://docs.pytest.org/en/stable/how-to/parametrize.html), and [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing). Review at build time and pin working versions.

## 8. Validation & Testing Plan

### 8.1 Independent numerical oracles

These hand-checkable cases are deliberately synthetic unless identified as a published source reconciliation. Implement them before UI. They specify exact expected behavior rather than comparing the engine against itself.

| Case | Inputs | Required result |
|---|---|---|
| Node-price normalization | 8 GPUs, $68.80/node-hour | $8.60/GPU-hour, but one hour of a full node still bills $68.80 |
| Productive capacity | q=1,000 tokens/s/node; 2 nodes; 10 h; a=0.9 | 64,800,000 tokens capacity |
| Overflow and conservation | Demand=100,000,000 tokens; baseline as above; unlimited-enough compatible rental | Baseline 64,800,000; overflow 35,200,000; unmet zero |
| Granular rental billing | q=1,000; a=1; demand=18,000,000; block=10 h; delta=1 h; startup=0; price=$10/h | 5 required and billed node-hours; cost $50 |
| Binding rental limit | Same q/a/block; demand=100,000,000; M=2 | Maximum 72,000,000 tokens; unmet 28,000,000; ineligible for full-service ranking |
| Rounding | q=1,000; a=1; demand=18,360,000; block=10 h; delta=1; startup=0 | 5.1 required hours, 6 billed hours; no fractional GPU purchase |
| Commitment zero use | K=2; H=720; p_C=$10; demand=0 | $14,400 contractual expense; zero execution utilization; token unit cost null |
| Ownership energy | K=2; H=720; idle=2 kW; load=10 kW; E=600 node-h; auxiliary=0; PUE=1.25 | IT=7,680 kWh; facility=9,600 kWh; at $0.10/kWh expense=$960 |
| Idle fleet | Same energy case with E=0 | IT=2,880 kWh; facility=3,600 kWh; nonzero idle cost |
| PV timing | $1,200 upfront; $100 end-month for 12 months; $120 sale at month 12; r=10% | PV cost=$2,230.95787384216; TCO=$2,280 |
| Zero discount | Same cash schedule, r=0 | PV cost=TCO=$2,280; no divide-by-zero |
| Simplified own breakeven | F=$100,000/year; Q=10,000 productive node-h/year; p=$20; v=$5 | u*=2/3; no feasible crossing if F rises to $200,000 |
| Simplified commit breakeven | p_C=$4; p_OD=$10; other conditions of 5.9 | 40% used-share |
| Published benchmark arithmetic | S11 B200 102,703 tokens/s; S01 $68.80/h; f=a=1, perfect continuous utilization, no extras | Derived idealized compute-only ~$0.18608133/million output tokens. Not production price, not a fully loaded result |

Cash tolerances: absolute $0.01 for display-level expected values; relative 1e-9 for internal PV checks. Token/service conservation tolerance max(1 token, 1e-9×demand). Rounding helpers have their separate tolerance in 5.5. Do not round upstream source values to force a test to pass.

### 8.2 Unit, invariant and edge tests

- **Dimensions:** seconds-to-hours factor 3,600; W-to-kW factor 1,000; cents-to-dollars factor 100; node-to-GPU multiplication only using matching configuration; annual-to-monthly discount conversion.
- **Calendar:** actual month hours, leap February, no implicit 730-hour month or universal 8,760-hour year. A 36-month horizon includes the actual 2028 leap day for the default start.
- **Capacity conservation:** baseline+overflow+unmet=demand; all nonnegative; execution <=available productive hours; billed rental hours >=required adjusted execution; block allocations cannot exceed max nodes or duration.
- **Zero/bounds:** zero demand; zero rental capacity; zero residual/rate; K=0 all-rental baseline; K<=spares; L=0 and L=T; term mismatch; economic life too short; PUE<1; negative prices; NaN/infinity; f>1; a=0; empty arrays; unsupported currency; duplicated keys. Reject invalid cases explicitly.
- **Cash integrity:** no depreciation or debt interest in unlevered NPV; no energy on top of all-in colocation; no included host resources double-counted; no monthly shared fee duplicated across blocks; residual occurs once at horizon; K=0 creates no owned capex or fixed owned fee.
- **Prepayment:** same nominal obligation regardless of prepayment fraction; positive discount rate makes earlier payment weakly more expensive in PV when nominal rate is unchanged. Setup fee appears once.
- **Monotonicity under fixed policy:** greater price or capex cannot reduce PV; more demand cannot reduce total delivered demand cost under fixed nonnegative terms, although unit cost can decline; larger capacity limit cannot increase unmet work. Test only under fixed controls—optimized fleet switches can create discontinuities.
- **Sensitivity semantics:** stress holds original K fixed; reoptimization is separately labeled; no matching demand regeneration when hardware changes; explicit source overrides propagate into exports.
- **Ranking:** infeasible/unknown-essential policies excluded; practical tie set correct; no feasible results produces an explicit failure state; upper-bound winner warns; identical scenarios reproduce hashes/results.

Use parametrized/property-style tests for these small invariants. Hypothesis is optional only if it adds useful generated boundary cases. Do not inflate coverage with UI pixel tests that mirror rendering code.

### 8.3 Source validation

For each admitted source row: check URL/locator, units, region, date, raw value, GPU/node count, inclusion flags, license note and artifact hash. Manually reconcile every initial offer against its official page. A second reading of source values is an acceptable review step; no claim of independent third-party audit.

MLPerf parser must reject unexpected columns or types rather than silently shift indices. Check composite-key uniqueness, release/commit, closed division, available category, exact workload/quality/scenario, metric units, GPU count and result path. The two selected B200/B300 values must match the frozen official summary. Link system/log metadata. Do not require rerunning MLPerf on paid GPUs; this project reproduces economic calculations from published results, not independent hardware benchmarking.

Adversarial fixtures: GPU-hour mislabeled node-hour; currency missing; price from software add-on; spot price mislabeled on-demand; quote-only parsed as zero; mixed North America/Europe rows; H200+MI350X mixed system labeled H200-only; multi-node score assigned to one node; Server score substituted for Offline; 99% score used for 99.9%; preview Rubin treated as available; identical-looking records from different releases joined; stale result presented as fresh.

Failed refresh must leave the previous validated snapshot unchanged and report the failure. App startup must work offline. Do not fall back from missing B300 pricing to H200 or B200 pricing.

### 8.4 Published cross-checks and boundaries

Reconcile node/GPU unit arithmetic against public pricing [S01, S05]. Reconcile measured-throughput rows against MLPerf, and explain the idealized rate calculation above [S11]. Use NVIDIA electrical limits as sanity bounds only for the exact documented system [S03, S04]. Reconcile the interpretation of accounting life with the CoreWeave filing, without treating that life as the economic forecast [S20].

No publicly audited, apples-to-apples ownership-versus-rental case with identical workload, acquisition terms, power boundary and utilization was established in this research. Therefore do not claim the full economic engine is externally validated against an industry TCO result. Its validity rests on transparent inputs, independent calculation fixtures, dimensional checks and documented limitations. Vendor TCO calculators or promotional savings claims are context, not test oracles unless their complete assumptions can be matched.

### 8.5 Application and release checks

Use Streamlit AppTest for initial render, preset selection, invalid-input feedback, computation and export availability. Add one smoke test importing a valid exported JSON and reproducing the same numerical result. Confirm separate user sessions do not leak inputs; verify exports include versions and assumptions. Manually inspect charts for unit labels, visible shortages and coherent rounding. Run lint/tests in CI on fresh install with no network dependency after setup. Do not publish before source reconciliation and all critical economic tests pass.

## 9. MVP / Phase 2 / Stretch Scope

| Stage | Included | Explicitly excluded |
|---|---|---|
| MVP | One batch inference workload; B200 worked example; B300 performance comparison gated by explicit prices; H100/H200 cost catalog; three sourcing families; fixed fleet, whole nodes, on-demand overflow; 36-month cash flow; demand stresses; energy; NPV/TCO; provenance; DuckDB SQL; four Streamlit views; JSON/CSV/Markdown export; automated tests | Training economics, real-time SLO sizing, combined owned+committed baseline, heterogeneous dispatch, GPUs rented by arbitrary fraction, full provider discount emulation, automatic trading/procurement, accounts, collaboration, live scraping, debt/tax schedule, contribution margin, GPU execution |
| Phase 2 | One validated latency-sensitive workload; explicit training-job costing; additional AMD/TPU/Trainium configurations with evidence; per-provider official API importers; time-dated contract blocks; economic dispatch; replacement and staged purchase; financing/tax view kept separate; actual bill reconciliation; itemized revenue/cost contribution view | No expansion until it changes a documented decision or closes a validation gap |
| Stretch | Calibrated probabilistic demand and correlated availability/price shocks; multi-stage portfolio optimization; measured performance curves; queueing/scheduling simulation; facility power and rack constraints; managed API versus self-host inference with matched quality | No fabricated probabilities or forecast accuracy; no scale infrastructure solely for résumé keywords |

A strong MVP is complete when one reviewer can reproduce a sourcing conclusion, identify its dominant uncertain inputs, and make the conclusion reverse predictably by changing them. Having ten hardware families with incompatible throughput is not a superior MVP.

## 10. Repository Design

Proposed repository: `ai-compute-economics`. Paths below are the intended build structure, not existing application files. The listing is a directory specification, not a system diagram.

```text
ai-compute-economics/
  README.md
  LICENSE
  THIRD_PARTY_NOTICES.md
  pyproject.toml
  uv.lock
  requirements.txt
  app.py
  .gitignore
  .streamlit/config.toml
  .github/workflows/ci.yml
  data/
    sources.csv
    configurations.csv
    offers.csv
    benchmarks.csv
    compatibility.csv
    assumptions.json
    snapshots/2026-09-27/manifest.json
    snapshots/2026-09-27/evidence/
  scenarios/
    stable_demand.json
    demand_disappointment.json
    delayed_capacity.json
  src/compute_economics/
    __init__.py
    schemas.py
    units.py
    validation.py
    catalog.py
    ingestion.py
    workload.py
    capacity.py
    economics.py
    scenarios.py
    reporting.py
    cli.py
    sql/
      eligible_offers.sql
      evidence_coverage.sql
      annual_costs.sql
    ui/
      decision.py
      economics_view.py
      risk.py
      evidence.py
  tests/
    fixtures/
    test_units.py
    test_sources.py
    test_capacity.py
    test_cashflows.py
    test_scenarios.py
    test_exports.py
    test_app.py
  docs/
    build_specification.md
    methodology.md
    data_dictionary.md
    source_collection.md
    assumptions.md
    validation.md
    deployment.md
    decisions.md
  examples/
    decision_memo.md
    monthly_ledger.csv
    scenario.json
```

README starts with the decision question, representative screenshot, one concrete reproducible finding, limitation banner, quick start, data date and links to methodology. Do not open with a tool-logo wall. `decisions.md` records the storage choice, workload boundary, reasons for excluded features and documented model changes. `validation.md` describes actual checks run and unresolved limitations. `examples` contains engine-generated, reproducible outputs. Build caches, secrets, local user scenarios and generated database files remain gitignored.

Use `pyproject.toml` as dependency source of truth, `uv.lock` for deterministic development, and a generated pinned `requirements.txt` for the host. CI must detect inconsistent exports. CLI contract: `uv sync --locked`, `uv run compute-economics validate-data`, `uv run compute-economics run scenarios/stable_demand.json --output examples`, `uv run pytest`, and `uv run streamlit run app.py`. Current commands are documented in the README.

## 11. Engineering verification

Contracts, source provenance, catalog joins, demand and capacity conservation, cash-flow reconciliation, feasibility, practical ties, fixed-fleet risk and discontinuous frontier brackets are tested independently. Exported scenarios must reproduce their outputs. Application tests cover four views, invalid inputs, missing evidence, downloads and session isolation. The [validation record](validation.md) documents executed checks and their limits.

## 12. Open Questions / Risks

### 12.1 Required evidence checks before model admission

| Issue | Current resolution | Implementation action |
|---|---|---|
| Actual ownership purchase and colocation costs | Not established as universal public observations | Use visibly hypothetical itemized defaults; admit a real quote only after checking included hardware/services and dates |
| Benchmark-to-rented-node mapping | Matching family/provider is insufficient | Inspect source system/log metadata; record hardware/runtime differences; retain conditional transfer label |
| B300 memory discrepancy and quote-only price | Unresolved provider/configuration-specific facts | Preserve raw reported memory; leave price null; do not rank financially without a user assumption or complete verified offer |
| Current physical inventory | Public catalog is insufficient | User-supplied capacity limits and availability acknowledgement; no unconditional sourcing recommendation |
| Source snapshots and licenses | Evidence frozen in the 2026-09-27 snapshot | The manifest pins commits and narrow evidence; reuse obligations are documented before admission |
| Within-block burstiness | Two-block approximation | Disclose loss of temporal detail; use batch-only boundary; production SLO analysis deferred |
| Real organizational overhead | Public staffing/support boundary incomplete | Itemize assumptions and exclusions; avoid calling result company gross margin |

These uncertainties limit procurement conclusions. Explicit assumptions and decision thresholds allow conditional analysis while the missing commercial evidence remains visible.

### 12.2 Known model risks

The largest economic uncertainties are workload-transfer performance, acquisition cost, long-term demand, actual contract terms, delivery/capacity and residual value. Electricity may be important but should not distract from larger drivers; let the sensitivity results establish the ordering. The flagship benchmark uses aggressive optimized software/precision and must not be extrapolated to arbitrary models or enterprise deployment stacks.

Published lists can lag negotiations; live page content can change after the research date. No stale snapshot should be called current. New hardware announcements may alter market pricing but are not evidence of usable supply. Supply and demand risks can be correlated, so deterministic stresses should include a named combined adverse case before any future Monte Carlo module is considered.

MVP ownership is an incremental fleet in existing colocation, not a hyperscale-campus investment. The simplified scheduler assumes divisible independent batch work and linear replication of the validated node, subject to the transfer factor. It does not reproduce fabric contention, storage bottlenecks, heterogeneous traffic, regional failover or dynamic autoscaling.

The project is valuable even if the answer is conditional. A reviewer should be able to see exactly which unknown is worth measuring next. Avoid an unsupported claim that this is the definitive model of frontier-company compute economics; it is a tightly specified, extensible decision model with honest boundaries.
