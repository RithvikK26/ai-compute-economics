# Conditional sourcing decision frontier

Under the selected assumptions, commit:7 has the lowest modeled cost.

**Illustrative scenario using public reference data and analyst assumptions.**
Run `cf06baea668d9a4a42cf10d03f8a5f398e7b301e9596b48880973bba89deb44a` · model 0.1.0 · snapshot 2026-09-27 · evidence review as of 2026-09-27.

Workload: **gpt-oss-120b / MLPerf v6.1 / Offline**. Quality: 99% of 83.13% exact\_match. Dataset: AIME25; GPQA Diamond; LiveCodeBench v6; accuracy repeats 8/5/3; max output 32768 accuracy / 10000 performance.
Published reference: 91487.4 output tokens/s per complete node. Baseline transfer 70%; rental transfer 70%; productive availability 98%/98%. These are distinct assumptions, not production measurements.

## Decision frontier and reversals

Current lowest modeled present-value cost: **$7,315,434** across 26 feasible policies. Practical tie set (within 1%): commit:7.

| Benchmark reference | System | Output tokens/s per submitted node | Role |
|---|---|---:|---|
| gpt-oss-120b / v6.1 Offline | B200 × 8 GPUs | 91,487.4 | Primary |
| llama2-70b-99.9 / v6.1 Offline | B200 × 8 GPUs | 102,703.0 | Secondary historical validation |
| gpt-oss-120b / v6.1 Offline | B300 × 8 GPUs | 112,840.0 | Primary |
| llama2-70b-99.9 / v6.1 Offline | B300 × 8 GPUs | 115,530.0 | Secondary historical validation |

These are published system benchmarks with distinct workload quality requirements. B300 lacks a rental price; no financial ranking or cloud/owned equivalence is inferred from this table.

**demand** — Crossings found.
Tested range: 0.25 to 2; K is reoptimized at each point.
- The modeled decision changes between **0.4 and 0.45**: `own:2` → `commit:2`. Selected fixed-policy utilization: 33.6%–37.9%.
- The modeled decision changes between **0.45 and 0.5**: `commit:2` → `commit:3`. Selected fixed-policy utilization: 37.9%–42.1%.
- The modeled decision changes between **0.6 and 0.65**: `commit:3` → `commit:4`. Selected fixed-policy utilization: 50.5%–54.7%.
- The modeled decision changes between **0.7 and 0.75**: `commit:4` → `commit:5`. Selected fixed-policy utilization: 58.4%–61.6%.
- The modeled decision changes between **0.8 and 0.85**: `commit:5` → `commit:6`. Selected fixed-policy utilization: 64.5%–67.3%.
- The modeled decision changes between **0.9 and 0.95**: `commit:6` → `commit:7`. Selected fixed-policy utilization: 70.1%–72.9%.
- The modeled decision changes between **1 and 1.05**: `commit:7` → `commit:8`. Selected fixed-policy utilization: 75.7%–78.5%.
- The modeled decision changes between **1.05 and 1.1**: `commit:8` → `commit:9`. Selected fixed-policy utilization: 78.5%–81.3%.
- The modeled decision changes between **1.15 and 1.2**: `commit:9` → `commit:10`. Selected fixed-policy utilization: 84.1%–86.9%.
- The modeled decision changes between **1.25 and 1.3**: `commit:10` → `commit:11`. Selected fixed-policy utilization: 89.7%–92.4%.
- The modeled decision changes between **1.35 and 1.4**: `commit:11` → `commit:12`. Selected fixed-policy utilization: 94.7%–96.3%.
- The modeled decision changes between **1.45 and 1.5**: `commit:12` → `commit:13`. Selected fixed-policy utilization: 97.4%–97.9%.
- The modeled decision changes between **1.55 and 1.6**: `commit:13` → `commit:14`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.6 and 1.65**: `commit:14` → `commit:15`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.7 and 1.75**: `commit:15` → `commit:16`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.8 and 1.85**: `commit:16` → `commit:17`. Selected fixed-policy utilization: 98.0%–98.0%.
- The modeled decision changes between **1.9 and 1.95**: `commit:17` → `commit:18`. Selected fixed-policy utilization: 98.0%–98.0%.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

**acquisition cost multiplier** — No crossing in tested range.
Tested range: 0.75 to 1.25; K is reoptimized at each point.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

**commitment price usd node hour** — No crossing in tested range.
Tested range: 32 to 48; K is reoptimized at each point.
All tested fixed-policy sign-change brackets and full costs are retained in results.json. Brackets preserve whole-node and billing jumps; they are not interpolated roots.

Most influential tested assumption: **demand**. Range of fixed selected-policy cost advantage over the best feasible alternative at the disclosed endpoints; not a probability or statistical interval.

Stable across tested downside/base/upside demand paths: **no**.
- downside: fixed `commit:7`, scenario optimum `commit:3`, regret $3,020,790, unmet 0 tokens; outside practical tie set.
- base: fixed `commit:7`, scenario optimum `commit:7`, regret $0, unmet 0 tokens; in practical tie set.
- upside: fixed `commit:7`, scenario optimum `commit:13`, regret unavailable, unmet 4,794,125,923,480 tokens; outside practical tie set.

**Tested reversals:**
- demand = 0.5: reoptimized policy `commit:3`; selected policy unmet 0 tokens.
- demand = 1.5: reoptimized policy `commit:13`; selected policy unmet 4,794,125,923,480 tokens.
- transfer_factor = 0.5: reoptimized policy `commit:12`; selected policy unmet 2,574,244,296,119 tokens.
- transfer_factor = 0.9: reoptimized policy `commit:5`; selected policy unmet 0 tokens.
- demand_disappointment (from_month_7): selected K stays 7; scenario optimum `commit:6`; regret $852,916; unmet 0; leaves tie set.
- obsolescence_stress (lower_future_rental_and_zero_residual): selected K stays 7; scenario optimum `commit:7`; regret $0; unmet 0; remains in tie set.
- combined_adverse (delay_limited_overflow_lower_rent_and_zero_residual): selected K stays 7; scenario optimum `commit:7`; regret $0; unmet 0; remains in tie set.

## Policy comparison

| Policy | Status | PV cost | Upfront | Contract obligation | Unmet tokens | Savings vs full-service OD |
|---|---|---:|---:|---:|---:|---:|
| on_demand:0 | ineligible | $6,265,204 | $0 | $0 | 11,954,990,074,261 | unavailable |
| commit:1 | ineligible | $7,030,478 | $0 | $1,052,160 | 6,526,627,051,491 | unavailable |
| commit:2 | ineligible | $6,821,013 | $0 | $2,104,320 | 4,786,260,671,993 | unavailable |
| commit:3 | ineligible | $6,476,989 | $0 | $3,156,480 | 3,597,649,813,377 | unavailable |
| commit:4 | ineligible | $6,133,270 | $0 | $4,208,640 | 2,409,038,954,760 | unavailable |
| commit:5 | ineligible | $5,939,278 | $0 | $5,260,800 | 1,220,428,096,143 | unavailable |
| commit:6 | ineligible | $6,648,613 | $0 | $6,312,960 | 282,294,379,279 | unavailable |
| commit:7 | conditional | $7,315,434 | $0 | $7,365,120 | 0 | unavailable |
| commit:8 | conditional | $7,911,884 | $0 | $8,417,280 | 0 | unavailable |
| commit:9 | conditional | $8,509,368 | $0 | $9,469,440 | 0 | unavailable |
| commit:10 | conditional | $9,180,988 | $0 | $10,521,600 | 0 | unavailable |
| commit:11 | conditional | $10,026,225 | $0 | $11,573,760 | 0 | unavailable |
| commit:12 | conditional | $10,937,700 | $0 | $12,625,920 | 0 | unavailable |
| commit:13 | conditional | $11,849,175 | $0 | $13,678,080 | 0 | unavailable |
| commit:14 | conditional | $12,760,650 | $0 | $14,730,240 | 0 | unavailable |
| commit:15 | conditional | $13,672,125 | $0 | $15,782,400 | 0 | unavailable |
| commit:16 | conditional | $14,583,600 | $0 | $16,834,560 | 0 | unavailable |
| commit:17 | conditional | $15,495,075 | $0 | $17,886,720 | 0 | unavailable |
| commit:18 | conditional | $16,406,550 | $0 | $18,938,880 | 0 | unavailable |
| commit:19 | conditional | $17,318,025 | $0 | $19,991,040 | 0 | unavailable |
| commit:20 | conditional | $18,229,500 | $0 | $21,043,200 | 0 | unavailable |
| commit:21 | conditional | $19,140,975 | $0 | $22,095,360 | 0 | unavailable |
| commit:22 | conditional | $20,052,450 | $0 | $23,147,520 | 0 | unavailable |
| commit:23 | conditional | $20,963,925 | $0 | $24,199,680 | 0 | unavailable |
| commit:24 | conditional | $21,875,400 | $0 | $25,251,840 | 0 | unavailable |
| commit:25 | conditional | $22,786,875 | $0 | $26,304,000 | 0 | unavailable |
| commit:26 | conditional | $23,698,350 | $0 | $27,356,160 | 0 | unavailable |
| commit:27 | conditional | $24,609,825 | $0 | $28,408,320 | 0 | unavailable |
| commit:28 | conditional | $25,521,300 | $0 | $29,460,480 | 0 | unavailable |
| commit:29 | conditional | $26,432,775 | $0 | $30,512,640 | 0 | unavailable |
| commit:30 | conditional | $27,344,250 | $0 | $31,564,800 | 0 | unavailable |
| commit:31 | conditional | $28,255,725 | $0 | $32,616,960 | 0 | unavailable |
| commit:32 | conditional | $29,167,200 | $0 | $33,669,120 | 0 | unavailable |
| own:1 | ineligible | $6,734,072 | $450,000 | $0 | 7,229,996,281,771 | unavailable |
| own:2 | ineligible | $6,278,502 | $850,000 | $0 | 5,687,008,712,737 | unavailable |
| own:3 | ineligible | $5,688,374 | $1,250,000 | $0 | 4,695,776,664,584 | unavailable |
| own:4 | ineligible | $5,098,613 | $1,650,000 | $0 | 3,704,544,616,431 | unavailable |
| own:5 | ineligible | $4,573,061 | $2,050,000 | $0 | 2,713,312,568,277 | unavailable |
| own:6 | ineligible | $4,830,001 | $2,450,000 | $0 | 1,833,416,123,341 | unavailable |
| own:7 | ineligible | $5,060,624 | $2,850,000 | $0 | 1,551,121,744,062 | unavailable |
| own:8 | ineligible | $5,221,148 | $3,250,000 | $0 | 1,551,121,744,062 | unavailable |
| own:9 | ineligible | $5,382,504 | $3,650,000 | $0 | 1,551,121,744,062 | unavailable |
| own:10 | ineligible | $5,575,305 | $4,050,000 | $0 | 1,551,121,744,062 | unavailable |
| own:11 | ineligible | $5,923,087 | $4,450,000 | $0 | 1,551,121,744,062 | unavailable |
| own:12 | ineligible | $6,336,171 | $4,850,000 | $0 | 1,551,121,744,062 | unavailable |
| own:13 | ineligible | $6,749,256 | $5,250,000 | $0 | 1,551,121,744,062 | unavailable |
| own:14 | ineligible | $7,162,341 | $5,650,000 | $0 | 1,551,121,744,062 | unavailable |
| own:15 | ineligible | $7,575,425 | $6,050,000 | $0 | 1,551,121,744,062 | unavailable |
| own:16 | ineligible | $7,988,510 | $6,450,000 | $0 | 1,551,121,744,062 | unavailable |
| own:17 | ineligible | $8,401,594 | $6,850,000 | $0 | 1,551,121,744,062 | unavailable |
| own:18 | ineligible | $8,814,679 | $7,250,000 | $0 | 1,551,121,744,062 | unavailable |
| own:19 | ineligible | $9,227,763 | $7,650,000 | $0 | 1,551,121,744,062 | unavailable |
| own:20 | ineligible | $9,640,848 | $8,050,000 | $0 | 1,551,121,744,062 | unavailable |
| own:21 | ineligible | $10,053,932 | $8,450,000 | $0 | 1,551,121,744,062 | unavailable |
| own:22 | ineligible | $10,467,017 | $8,850,000 | $0 | 1,551,121,744,062 | unavailable |
| own:23 | ineligible | $10,880,102 | $9,250,000 | $0 | 1,551,121,744,062 | unavailable |
| own:24 | ineligible | $11,293,186 | $9,650,000 | $0 | 1,551,121,744,062 | unavailable |
| own:25 | ineligible | $11,706,271 | $10,050,000 | $0 | 1,551,121,744,062 | unavailable |
| own:26 | ineligible | $12,119,355 | $10,450,000 | $0 | 1,551,121,744,062 | unavailable |
| own:27 | ineligible | $12,532,440 | $10,850,000 | $0 | 1,551,121,744,062 | unavailable |
| own:28 | ineligible | $12,945,524 | $11,250,000 | $0 | 1,551,121,744,062 | unavailable |
| own:29 | ineligible | $13,358,609 | $11,650,000 | $0 | 1,551,121,744,062 | unavailable |
| own:30 | ineligible | $13,771,693 | $12,050,000 | $0 | 1,551,121,744,062 | unavailable |
| own:31 | ineligible | $14,184,778 | $12,450,000 | $0 | 1,551,121,744,062 | unavailable |
| own:32 | ineligible | $14,597,863 | $12,850,000 | $0 | 1,551,121,744,062 | unavailable |

## Cash flow and capacity

Selected-policy undiscounted TCO: $8,460,003; upfront $0; obligation $7,365,120.
Levelized cost per million output tokens for the specified input/output workload: $0.237518. Zero-work costs are null.
Baseline execution utilization: 0.7567411241115118; available-capacity utilization: 0.7721848205219508. Unused commitment allocation $1,791,631 is part of existing spend, not an extra expense.

| Cost category | Present value |
|---|---:|
| on\_demand | $935,109 |
| variable\_service | $0 |
| commitment | $6,380,325 |
| commit\_setup | $0 |
| commit\_fees | $0 |

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

Original observations and assumptions: 49; separately preserved overrides: 2. Full values, bounds, timestamps, locators, versions and artifact checksums are in scenario.json and provenance.csv.

- Illustrative scenario using public reference data and analyst assumptions.
- Benchmark-to-production and purchased-system transfer is assumed.
- Batch blocks omit within-block bursts; no interactive SLO claim.
- Historical snapshot; not a live quote.

[CoreWeave prices](https://www.coreweave.com/pricing) · [Pinned MLPerf results](https://github.com/mlcommons/inference_results_v6.1/tree/10ecdffda3bb94d71f0203a6ca8e20c17943f27c) · [Pinned quality rules](https://github.com/mlcommons/inference_policies/blob/d3eba2f21026d868ad65cdcad2bb81e4a17ce3d3/inference_rules.adoc).
