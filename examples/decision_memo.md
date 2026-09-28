# Conditional sourcing decision frontier

Under the selected assumptions, own:6 has the lowest modeled cost.

**Illustrative scenario using public reference data and analyst assumptions.**
Run `bfee7bf3a4969c69e1eefc61844a35db6d3590315276d52052a5ab7a76fc9110` · model 0.1.0 · snapshot 2026-09-27 · evidence review as of 2026-09-27.

Workload: **gpt-oss-120b / MLPerf v6.1 / Offline**. Quality: 99% of 83.13% exact\_match. Dataset: AIME25; GPQA Diamond; LiveCodeBench v6; accuracy repeats 8/5/3; max output 32768 accuracy / 10000 performance.
Published reference: 91487.4 output tokens/s per complete node. Baseline transfer 70%; rental transfer 70%; productive availability 98%/98%. These are distinct assumptions, not production measurements.

## Decision frontier and reversals

Current lowest modeled present-value cost: **$3,973,887** across 65 feasible policies. Practical tie set (within 1%): own:6, own:5.

| Benchmark reference | System | Output tokens/s per submitted node | Role |
|---|---|---:|---|
| gpt-oss-120b / v6.1 Offline | B200 × 8 GPUs | 91,487.4 | Primary |
| llama2-70b-99.9 / v6.1 Offline | B200 × 8 GPUs | 102,703.0 | Secondary historical validation |
| gpt-oss-120b / v6.1 Offline | B300 × 8 GPUs | 112,840.0 | Primary |
| llama2-70b-99.9 / v6.1 Offline | B300 × 8 GPUs | 115,530.0 | Secondary historical validation |

These are published system benchmarks with distinct workload quality requirements. B300 lacks a rental price; no financial ranking or cloud/owned equivalence is inferred from this table.

**demand** — Crossings found.
Tested range: 0.25 to 2; K is reoptimized at each point.
- The modeled decision changes between **0.4 and 0.45**: `own:2` → `own:3`. Selected fixed-policy utilization: 39.3%–44.2%.
- The modeled decision changes between **0.6 and 0.65**: `own:3` → `own:4`. Selected fixed-policy utilization: 58.4%–62.1%.
- The modeled decision changes between **0.8 and 0.85**: `own:4` → `own:5`. Selected fixed-policy utilization: 71.9%–75.2%.
- The modeled decision changes between **0.95 and 1**: `own:5` → `own:6`. Selected fixed-policy utilization: 81.7%–85.0%.
- The modeled decision changes between **1.15 and 1.2**: `own:6` → `own:7`. Selected fixed-policy utilization: 94.3%–96.3%.
- The modeled decision changes between **1.35 and 1.4**: `own:7` → `own:8`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.55 and 1.6**: `own:8` → `own:9`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.7 and 1.75**: `own:9` → `own:10`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.9 and 1.95**: `own:10` → `own:11`. Selected fixed-policy utilization: 98.0%–98.0%.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

**acquisition cost multiplier** — Crossings found.
Tested range: 0.75 to 1.25; K is reoptimized at each point.
- The modeled decision changes between **1.05 and 1.075** ($420,000–$430,000 per node): `own:6` → `own:5`. Selected fixed-policy utilization: 85.0%–85.0%.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

**commitment price usd node hour** — No crossing in tested range.
Tested range: 32 to 48; K is reoptimized at each point.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

Most influential tested assumption: **demand**. Range of fixed selected-policy cost advantage over the best feasible alternative at the disclosed endpoints; not a probability or statistical interval.

Stable across tested downside/base/upside demand paths: **no**.
- downside: fixed `own:6`, scenario optimum `own:3`, regret $632,033, unmet 0 tokens; outside practical tie set.
- base: fixed `own:6`, scenario optimum `own:6`, regret $0, unmet 0 tokens; in practical tie set.
- upside: fixed `own:6`, scenario optimum `own:8`, regret $1,601,100, unmet 0 tokens; outside practical tie set.

**Tested reversals:**
- demand = 0.5: reoptimized policy `own:3`; selected policy unmet 0 tokens.
- demand = 1.5: reoptimized policy `own:8`; selected policy unmet 0 tokens.
- acquisition_cost = 1.25: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- transfer_factor = 0.5: reoptimized policy `own:8`; selected policy unmet 0 tokens.
- transfer_factor = 0.9: reoptimized policy `own:4`; selected policy unmet 0 tokens.
- rental_future_price = 0.8: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- demand_disappointment (from_month_7): selected K stays 6; scenario optimum `own:5`; regret $325,552; unmet 0; leaves tie set.
- obsolescence_stress (lower_future_rental_and_zero_residual): selected K stays 6; scenario optimum `own:5`; regret $42,028; unmet 0; leaves tie set.
- combined_adverse (delay_limited_overflow_lower_rent_and_zero_residual): selected K stays 6; scenario optimum `commit:7`; regret unavailable; unmet 1,833,416,123,341; leaves tie set.

## Policy comparison

| Policy | Status | PV cost | Upfront | Contract obligation | Unmet tokens | Savings vs full-service OD |
|---|---|---:|---:|---:|---:|---:|
| on_demand:0 | conditional | $9,394,474 | $0 | $0 | 0 | $0 |
| commit:1 | conditional | $8,736,753 | $0 | $1,052,160 | 0 | $657,721 |
| commit:2 | conditional | $8,079,404 | $0 | $2,104,320 | 0 | $1,315,070 |
| commit:3 | conditional | $7,420,759 | $0 | $3,156,480 | 0 | $1,973,715 |
| commit:4 | conditional | $6,762,985 | $0 | $4,208,640 | 0 | $2,631,489 |
| commit:5 | conditional | $6,253,396 | $0 | $5,260,800 | 0 | $3,141,078 |
| commit:6 | conditional | $6,717,952 | $0 | $6,312,960 | 0 | $2,676,522 |
| commit:7 | conditional | $7,315,434 | $0 | $7,365,120 | 0 | $2,079,040 |
| commit:8 | conditional | $7,911,884 | $0 | $8,417,280 | 0 | $1,482,590 |
| commit:9 | conditional | $8,509,368 | $0 | $9,469,440 | 0 | $885,106 |
| commit:10 | conditional | $9,180,988 | $0 | $10,521,600 | 0 | $213,486 |
| commit:11 | conditional | $10,026,225 | $0 | $11,573,760 | 0 | $-631,751 |
| commit:12 | conditional | $10,937,700 | $0 | $12,625,920 | 0 | $-1,543,226 |
| commit:13 | conditional | $11,849,175 | $0 | $13,678,080 | 0 | $-2,454,701 |
| commit:14 | conditional | $12,760,650 | $0 | $14,730,240 | 0 | $-3,366,176 |
| commit:15 | conditional | $13,672,125 | $0 | $15,782,400 | 0 | $-4,277,651 |
| commit:16 | conditional | $14,583,600 | $0 | $16,834,560 | 0 | $-5,189,126 |
| commit:17 | conditional | $15,495,075 | $0 | $17,886,720 | 0 | $-6,100,601 |
| commit:18 | conditional | $16,406,550 | $0 | $18,938,880 | 0 | $-7,012,076 |
| commit:19 | conditional | $17,318,025 | $0 | $19,991,040 | 0 | $-7,923,551 |
| commit:20 | conditional | $18,229,500 | $0 | $21,043,200 | 0 | $-8,835,026 |
| commit:21 | conditional | $19,140,975 | $0 | $22,095,360 | 0 | $-9,746,501 |
| commit:22 | conditional | $20,052,450 | $0 | $23,147,520 | 0 | $-10,657,976 |
| commit:23 | conditional | $20,963,925 | $0 | $24,199,680 | 0 | $-11,569,451 |
| commit:24 | conditional | $21,875,400 | $0 | $25,251,840 | 0 | $-12,480,926 |
| commit:25 | conditional | $22,786,875 | $0 | $26,304,000 | 0 | $-13,392,401 |
| commit:26 | conditional | $23,698,350 | $0 | $27,356,160 | 0 | $-14,303,876 |
| commit:27 | conditional | $24,609,825 | $0 | $28,408,320 | 0 | $-15,215,351 |
| commit:28 | conditional | $25,521,300 | $0 | $29,460,480 | 0 | $-16,126,826 |
| commit:29 | conditional | $26,432,775 | $0 | $30,512,640 | 0 | $-17,038,301 |
| commit:30 | conditional | $27,344,250 | $0 | $31,564,800 | 0 | $-17,949,776 |
| commit:31 | conditional | $28,255,725 | $0 | $32,616,960 | 0 | $-18,861,251 |
| commit:32 | conditional | $29,167,200 | $0 | $33,669,120 | 0 | $-19,772,726 |
| own:1 | conditional | $8,376,074 | $450,000 | $0 | 0 | $1,018,400 |
| own:2 | conditional | $7,245,674 | $850,000 | $0 | 0 | $2,148,800 |
| own:3 | conditional | $6,113,977 | $1,250,000 | $0 | 0 | $3,280,497 |
| own:4 | conditional | $4,983,152 | $1,650,000 | $0 | 0 | $4,411,322 |
| own:5 | conditional | $3,998,377 | $2,050,000 | $0 | 0 | $5,396,097 |
| own:6 | conditional | $3,973,887 | $2,450,000 | $0 | 0 | $5,420,587 |
| own:7 | conditional | $4,080,453 | $2,850,000 | $0 | 0 | $5,314,021 |
| own:8 | conditional | $4,185,986 | $3,250,000 | $0 | 0 | $5,208,488 |
| own:9 | conditional | $4,292,553 | $3,650,000 | $0 | 0 | $5,101,921 |
| own:10 | conditional | $4,472,190 | $4,050,000 | $0 | 0 | $4,922,284 |
| own:11 | conditional | $4,822,980 | $4,450,000 | $0 | 0 | $4,571,494 |
| own:12 | conditional | $5,239,072 | $4,850,000 | $0 | 0 | $4,155,402 |
| own:13 | conditional | $5,655,164 | $5,250,000 | $0 | 0 | $3,739,310 |
| own:14 | conditional | $6,071,256 | $5,650,000 | $0 | 0 | $3,323,218 |
| own:15 | conditional | $6,487,348 | $6,050,000 | $0 | 0 | $2,907,126 |
| own:16 | conditional | $6,903,441 | $6,450,000 | $0 | 0 | $2,491,033 |
| own:17 | conditional | $7,319,533 | $6,850,000 | $0 | 0 | $2,074,941 |
| own:18 | conditional | $7,735,625 | $7,250,000 | $0 | 0 | $1,658,849 |
| own:19 | conditional | $8,151,717 | $7,650,000 | $0 | 0 | $1,242,757 |
| own:20 | conditional | $8,567,809 | $8,050,000 | $0 | 0 | $826,665 |
| own:21 | conditional | $8,983,902 | $8,450,000 | $0 | 0 | $410,572 |
| own:22 | conditional | $9,399,994 | $8,850,000 | $0 | 0 | $-5,520 |
| own:23 | conditional | $9,816,086 | $9,250,000 | $0 | 0 | $-421,612 |
| own:24 | conditional | $10,232,178 | $9,650,000 | $0 | 0 | $-837,704 |
| own:25 | conditional | $10,648,270 | $10,050,000 | $0 | 0 | $-1,253,797 |
| own:26 | conditional | $11,064,363 | $10,450,000 | $0 | 0 | $-1,669,889 |
| own:27 | conditional | $11,480,455 | $10,850,000 | $0 | 0 | $-2,085,981 |
| own:28 | conditional | $11,896,547 | $11,250,000 | $0 | 0 | $-2,502,073 |
| own:29 | conditional | $12,312,639 | $11,650,000 | $0 | 0 | $-2,918,165 |
| own:30 | conditional | $12,728,731 | $12,050,000 | $0 | 0 | $-3,334,258 |
| own:31 | conditional | $13,144,824 | $12,450,000 | $0 | 0 | $-3,750,350 |
| own:32 | conditional | $13,560,916 | $12,850,000 | $0 | 0 | $-4,166,442 |

## Cash flow and capacity

Selected-policy undiscounted TCO: $4,224,959; upfront $2,450,000; obligation $0.
Levelized cost per million output tokens for the specified input/output workload: $0.129024. Zero-work costs are null.
Baseline execution utilization: 0.8501979781300971; available-capacity utilization: 0.8675489572756093. Unused commitment allocation unavailable is part of existing spend, not an extra expense.

| Cost category | Present value |
|---|---:|
| on\_demand | $1,249,102 |
| variable\_service | $0 |
| node\_acquisition | $2,400,000 |
| installation | $50,000 |
| network | $0 |
| storage | $0 |
| operations | $124,746 |
| precommission | $0 |
| electricity | $150,039 |
| hosting | $0 |
| exit | $0 |
| residual | $0 |

Monthly cash, block capacity, cost-category and annual operating/total cash ledgers accompany this memo. Positive values are costs; sale proceeds are negative once at the horizon.

## Material missing evidence

- Measured production throughput, wall power and workload quality on the exact rented/purchased system are unavailable; the transfer factor is assumed.
- Complete purchase, colocation and commitment quotes, deployment dates and actual inventory are unavailable. Cost and capacity defaults are hypothetical.
- B300 on-demand price is unavailable (contact sales). Its benchmark is a performance reference, not an eligible zero-priced alternative.
- B300 memory descriptions differ by configuration/provider; preserve raw values until exact-SKU memory is verified.
- Real demand distribution, usable life and residual proceeds need validation. No publicly audited matching ownership-versus-rental case validates the full TCO model.

## Assumptions, provenance and scope

Batch inference only; no latency SLO, backlog, cross-provider overflow, mixed fleet, training, replacement, taxes, debt interest, depreciation expense, company margin, facility construction or supply guarantee. Fixed owned operations include assumed site space/support/labor; workload-specific additional storage, egress and service overhead default to explicitly excluded zero. The 80%/20% blocks omit within-block bursts.

Synthetic demand scale stays 71892.1 tokens/s regardless of hardware. This is the preserved teaching scale; it is not the primary benchmark throughput.

Source/runtime: TensorRT-LLM feat/1.2-mlpinf, NVIDIA Dynamo mlperf-v6.0-dynamo-v0.8.0. Precision: fp4. Topology: All-to-all via NVSwitch, 18 NVLink connections between every GPU pair.
Submission NVSwitch system uses optimized FP4 runtime and shared Vast NFS; advertised node has different storage/host description. Purchased OEM/runtime/power unverified.

No upfront cash constraint.

Original observations and assumptions: 49; separately preserved overrides: 0. Full values, bounds, timestamps, locators, versions and artifact checksums are in scenario.json and provenance.csv.

- Illustrative scenario using public reference data and analyst assumptions.
- Benchmark-to-production and purchased-system transfer is assumed.
- Batch blocks omit within-block bursts; no interactive SLO claim.
- Historical snapshot; not a live quote.

[CoreWeave prices](https://www.coreweave.com/pricing) · [Pinned MLPerf results](https://github.com/mlcommons/inference_results_v6.1/tree/10ecdffda3bb94d71f0203a6ca8e20c17943f27c) · [Pinned quality rules](https://github.com/mlcommons/inference_policies/blob/d3eba2f21026d868ad65cdcad2bb81e4a17ce3d3/inference_rules.adoc).
