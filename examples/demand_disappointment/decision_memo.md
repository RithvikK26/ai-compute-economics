# Conditional sourcing decision frontier

Under the selected assumptions, own:5 has the lowest modeled cost. This is the retrospective optimum; the time-zero base policy own:6 remains fixed for disappointment exposure.

**Illustrative scenario using public reference data and analyst assumptions.**
Run `6f977a8eb0862f437d3174d0eba4d2481cbcb6d49bfe930b9fadad4c1fd6096c` · model 0.1.0 · snapshot 2026-09-27 · evidence review as of 2026-09-27.

Workload: **gpt-oss-120b / MLPerf v6.1 / Offline**. Quality: 99% of 83.13% exact\_match. Dataset: AIME25; GPQA Diamond; LiveCodeBench v6; accuracy repeats 8/5/3; max output 32768 accuracy / 10000 performance.
Published reference: 91487.4 output tokens/s per complete node. Baseline transfer 70%; rental transfer 70%; productive availability 98%/98%. These are distinct assumptions, not production measurements.

## Decision frontier and reversals

Current lowest modeled present-value cost: **$2,551,454** across 65 feasible policies. Practical tie set (within 1%): own:5.

| Benchmark reference | System | Output tokens/s per submitted node | Role |
|---|---|---:|---|
| gpt-oss-120b / v6.1 Offline | B200 × 8 GPUs | 91,487.4 | Primary |
| llama2-70b-99.9 / v6.1 Offline | B200 × 8 GPUs | 102,703.0 | Secondary historical validation |
| gpt-oss-120b / v6.1 Offline | B300 × 8 GPUs | 112,840.0 | Primary |
| llama2-70b-99.9 / v6.1 Offline | B300 × 8 GPUs | 115,530.0 | Secondary historical validation |

These are published system benchmarks with distinct workload quality requirements. B300 lacks a rental price; no financial ranking or cloud/owned equivalence is inferred from this table.

**demand** — Crossings found.
Tested range: 0.25 to 2; K is reoptimized at each point.
- The modeled decision changes between **0.35 and 0.4**: `own:1` → `own:2`. Selected fixed-policy utilization: 19.8%–22.6%.
- The modeled decision changes between **0.55 and 0.6**: `own:2` → `own:3`. Selected fixed-policy utilization: 31.1%–34.0%.
- The modeled decision changes between **0.75 and 0.8**: `own:3` → `own:4`. Selected fixed-policy utilization: 41.9%–44.5%.
- The modeled decision changes between **0.95 and 1**: `own:4` → `own:5`. Selected fixed-policy utilization: 52.3%–54.8%.
- The modeled decision changes between **1.15 and 1.2**: `own:5` → `own:6`. Selected fixed-policy utilization: 62.5%–64.7%.
- The modeled decision changes between **1.4 and 1.45**: `own:6` → `own:7`. Selected fixed-policy utilization: 71.4%–72.8%.
- The modeled decision changes between **1.6 and 1.65**: `own:7` → `own:8`. Selected fixed-policy utilization: 76.9%–78.3%.
- The modeled decision changes between **1.8 and 1.85**: `own:8` → `own:9`. Selected fixed-policy utilization: 82.4%–83.8%.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

**acquisition cost multiplier** — Crossings found.
Tested range: 0.75 to 1.25; K is reoptimized at each point.
- The modeled decision changes between **1.05 and 1.075** ($420,000–$430,000 per node): `own:5` → `own:4`. Selected fixed-policy utilization: 54.8%–54.8%.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

**commitment price usd node hour** — No crossing in tested range.
Tested range: 32 to 48; K is reoptimized at each point.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

Most influential tested assumption: **demand**. Range of fixed selected-policy cost advantage over the best feasible alternative at the disclosed endpoints; not a probability or statistical interval.

Stable across tested downside/base/upside demand paths: **no**.
- downside: fixed `own:6`, scenario optimum `own:2`, regret $1,303,120, unmet 0 tokens; outside practical tie set.
- base: fixed `own:6`, scenario optimum `own:5`, regret $325,552, unmet 0 tokens; outside practical tie set.
- upside: fixed `own:6`, scenario optimum `own:7`, regret $112,332, unmet 0 tokens; outside practical tie set.

**Tested reversals:**
- demand = 0.5: reoptimized policy `own:2`; selected policy unmet 0 tokens.
- demand = 1: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- demand = 1.5: reoptimized policy `own:7`; selected policy unmet 0 tokens.
- acquisition_cost = 0.75: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- acquisition_cost = 1: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- acquisition_cost = 1.25: reoptimized policy `own:4`; selected policy unmet 0 tokens.
- transfer_factor = 0.7: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- transfer_factor = 0.9: reoptimized policy `own:4`; selected policy unmet 0 tokens.
- rental_future_price = 0.8: reoptimized policy `own:4`; selected policy unmet 0 tokens.
- rental_future_price = 1: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- rental_future_price = 1.2: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- commitment_price = 32: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- commitment_price = 40: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- commitment_price = 48: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- discount_rate = 0.05: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- discount_rate = 0.1: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- discount_rate = 0.15: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- electricity = 0.05: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- electricity = 0.1: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- electricity = 0.15: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- residual = 0: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- residual = 0.2: reoptimized policy `own:5`; selected policy unmet 0 tokens.
- demand_disappointment (from_month_7): selected K stays 6; scenario optimum `own:5`; regret $325,552; unmet 0; leaves tie set.
- obsolescence_stress (lower_future_rental_and_zero_residual): selected K stays 6; scenario optimum `own:4`; regret $345,685; unmet 0; leaves tie set.
- combined_adverse (delay_limited_overflow_lower_rent_and_zero_residual): selected K stays 6; scenario optimum `commit:6`; regret unavailable; unmet 1,551,121,744,062; leaves tie set.

## Policy comparison

| Policy | Status | PV cost | Upfront | Contract obligation | Unmet tokens | Savings vs full-service OD |
|---|---|---:|---:|---:|---:|---:|
| on_demand:0 | conditional | $5,512,783 | $0 | $0 | 0 | $0 |
| commit:1 | conditional | $4,854,888 | $0 | $1,052,160 | 0 | $657,895 |
| commit:2 | conditional | $4,196,148 | $0 | $2,104,320 | 0 | $1,316,635 |
| commit:3 | conditional | $4,014,819 | $0 | $3,156,480 | 0 | $1,497,964 |
| commit:4 | conditional | $4,378,275 | $0 | $4,208,640 | 0 | $1,134,508 |
| commit:5 | conditional | $4,841,639 | $0 | $5,260,800 | 0 | $671,144 |
| commit:6 | conditional | $5,661,272 | $0 | $6,312,960 | 0 | $-148,489 |
| commit:7 | conditional | $6,514,188 | $0 | $7,365,120 | 0 | $-1,001,405 |
| commit:8 | conditional | $7,366,833 | $0 | $8,417,280 | 0 | $-1,854,050 |
| commit:9 | conditional | $8,219,678 | $0 | $9,469,440 | 0 | $-2,706,895 |
| commit:10 | conditional | $9,114,750 | $0 | $10,521,600 | 0 | $-3,601,967 |
| commit:11 | conditional | $10,026,225 | $0 | $11,573,760 | 0 | $-4,513,442 |
| commit:12 | conditional | $10,937,700 | $0 | $12,625,920 | 0 | $-5,424,917 |
| commit:13 | conditional | $11,849,175 | $0 | $13,678,080 | 0 | $-6,336,392 |
| commit:14 | conditional | $12,760,650 | $0 | $14,730,240 | 0 | $-7,247,867 |
| commit:15 | conditional | $13,672,125 | $0 | $15,782,400 | 0 | $-8,159,342 |
| commit:16 | conditional | $14,583,600 | $0 | $16,834,560 | 0 | $-9,070,817 |
| commit:17 | conditional | $15,495,075 | $0 | $17,886,720 | 0 | $-9,982,292 |
| commit:18 | conditional | $16,406,550 | $0 | $18,938,880 | 0 | $-10,893,767 |
| commit:19 | conditional | $17,318,025 | $0 | $19,991,040 | 0 | $-11,805,242 |
| commit:20 | conditional | $18,229,500 | $0 | $21,043,200 | 0 | $-12,716,717 |
| commit:21 | conditional | $19,140,975 | $0 | $22,095,360 | 0 | $-13,628,192 |
| commit:22 | conditional | $20,052,450 | $0 | $23,147,520 | 0 | $-14,539,667 |
| commit:23 | conditional | $20,963,925 | $0 | $24,199,680 | 0 | $-15,451,142 |
| commit:24 | conditional | $21,875,400 | $0 | $25,251,840 | 0 | $-16,362,617 |
| commit:25 | conditional | $22,786,875 | $0 | $26,304,000 | 0 | $-17,274,092 |
| commit:26 | conditional | $23,698,350 | $0 | $27,356,160 | 0 | $-18,185,567 |
| commit:27 | conditional | $24,609,825 | $0 | $28,408,320 | 0 | $-19,097,042 |
| commit:28 | conditional | $25,521,300 | $0 | $29,460,480 | 0 | $-20,008,517 |
| commit:29 | conditional | $26,432,775 | $0 | $30,512,640 | 0 | $-20,919,992 |
| commit:30 | conditional | $27,344,250 | $0 | $31,564,800 | 0 | $-21,831,467 |
| commit:31 | conditional | $28,255,725 | $0 | $32,616,960 | 0 | $-22,742,942 |
| commit:32 | conditional | $29,167,200 | $0 | $33,669,120 | 0 | $-23,654,417 |
| own:1 | conditional | $4,494,209 | $450,000 | $0 | 0 | $1,018,574 |
| own:2 | conditional | $3,362,418 | $850,000 | $0 | 0 | $2,150,365 |
| own:3 | conditional | $2,701,240 | $1,250,000 | $0 | 0 | $2,811,543 |
| own:4 | conditional | $2,577,112 | $1,650,000 | $0 | 0 | $2,935,671 |
| own:5 | conditional | $2,551,454 | $2,050,000 | $0 | 0 | $2,961,329 |
| own:6 | conditional | $2,877,005 | $2,450,000 | $0 | 0 | $2,635,778 |
| own:7 | conditional | $3,235,371 | $2,850,000 | $0 | 0 | $2,277,412 |
| own:8 | conditional | $3,593,465 | $3,250,000 | $0 | 0 | $1,919,318 |
| own:9 | conditional | $3,951,761 | $3,650,000 | $0 | 0 | $1,561,022 |
| own:10 | conditional | $4,351,681 | $4,050,000 | $0 | 0 | $1,161,102 |
| own:11 | conditional | $4,767,773 | $4,450,000 | $0 | 0 | $745,010 |
| own:12 | conditional | $5,183,866 | $4,850,000 | $0 | 0 | $328,917 |
| own:13 | conditional | $5,599,958 | $5,250,000 | $0 | 0 | $-87,175 |
| own:14 | conditional | $6,016,050 | $5,650,000 | $0 | 0 | $-503,267 |
| own:15 | conditional | $6,432,142 | $6,050,000 | $0 | 0 | $-919,359 |
| own:16 | conditional | $6,848,234 | $6,450,000 | $0 | 0 | $-1,335,451 |
| own:17 | conditional | $7,264,327 | $6,850,000 | $0 | 0 | $-1,751,544 |
| own:18 | conditional | $7,680,419 | $7,250,000 | $0 | 0 | $-2,167,636 |
| own:19 | conditional | $8,096,511 | $7,650,000 | $0 | 0 | $-2,583,728 |
| own:20 | conditional | $8,512,603 | $8,050,000 | $0 | 0 | $-2,999,820 |
| own:21 | conditional | $8,928,695 | $8,450,000 | $0 | 0 | $-3,415,912 |
| own:22 | conditional | $9,344,788 | $8,850,000 | $0 | 0 | $-3,832,005 |
| own:23 | conditional | $9,760,880 | $9,250,000 | $0 | 0 | $-4,248,097 |
| own:24 | conditional | $10,176,972 | $9,650,000 | $0 | 0 | $-4,664,189 |
| own:25 | conditional | $10,593,064 | $10,050,000 | $0 | 0 | $-5,080,281 |
| own:26 | conditional | $11,009,156 | $10,450,000 | $0 | 0 | $-5,496,373 |
| own:27 | conditional | $11,425,249 | $10,850,000 | $0 | 0 | $-5,912,466 |
| own:28 | conditional | $11,841,341 | $11,250,000 | $0 | 0 | $-6,328,558 |
| own:29 | conditional | $12,257,433 | $11,650,000 | $0 | 0 | $-6,744,650 |
| own:30 | conditional | $12,673,525 | $12,050,000 | $0 | 0 | $-7,160,742 |
| own:31 | conditional | $13,089,618 | $12,450,000 | $0 | 0 | $-7,576,834 |
| own:32 | conditional | $13,505,710 | $12,850,000 | $0 | 0 | $-7,992,927 |

## Cash flow and capacity

Selected-policy undiscounted TCO: $2,917,869; upfront $2,450,000; obligation $0.
Levelized cost per million output tokens for the specified input/output workload: $0.159199. Zero-work costs are null.
Baseline execution utilization: 0.5483620740612635; available-capacity utilization: 0.5595531367972076. Unused commitment allocation unavailable is part of existing spend, not an extra expense.

| Cost category | Present value |
|---|---:|
| on\_demand | $192,422 |
| variable\_service | $0 |
| node\_acquisition | $2,400,000 |
| installation | $50,000 |
| network | $0 |
| storage | $0 |
| operations | $124,746 |
| precommission | $0 |
| electricity | $109,837 |
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
