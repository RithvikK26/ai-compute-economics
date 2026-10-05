# Workload and decision-frontier design amendment

Research date: September 27, 2026. These requirements supersede the corresponding language in the original design.

1. **Primary workload:** gpt-oss-120b / MLPerf Inference v6.1 / Offline, anchored to the published CoreWeave B200 and B300 results. Llama 2 70B 99.9 Offline remains a secondary historical reference. Compatibility, quality, configuration, provenance and explicit benchmark-transfer safeguards remain mandatory.
2. **Primary output:** the decision frontier / breakeven surface, with conditional lowest modeled cost, practical ties, demand/utilization and pricing thresholds, tested reversals, demand-path stability and missing evidence. Policy comparison, cash-flow, capacity, sensitivity and provenance outputs remain available.
3. **Unchanged analytical scope:** the architecture, economic formulas, deterministic scenarios and validation requirements remain as specified. Section 5.4's synthetic demand scale and Section 8.1's Llama arithmetic oracle are not relabeled as gpt-oss throughput. Production throughput uses a separate explicit transfer assumption.

The [current specification](build_specification.md) incorporates these requirements. The [original design](original_build_specification.md) retains the prior technical requirements for comparison; both public copies retain the technical requirements. Git history preserves the earlier drafts.
