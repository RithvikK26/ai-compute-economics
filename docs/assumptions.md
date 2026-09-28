# Assumptions and missing evidence

Defaults remain the synthetic values in specification 5.11: 36 months from October 2026; 70% throughput transfer, 98% productive availability; 32 assumed obtainable rental nodes; 1-hour billing quantum and no startup; $400,000 complete owned node; $50,000 incremental installation/infrastructure; $24,000/year fixed plus $4,000/node/year operations; 2/10 kW idle/load whole-node power; PUE 1.25 and $0.10/kWh; no delay/spares/residual; $40/node-hour hypothetical commitment with no setup/prepayment. These are teaching assumptions, not quotes or industry standards.

The $50,000 infrastructure placeholder is assigned to installation; separate network/storage additions default to explicitly excluded zero. Fixed operations include assumed site space, support and labor. Additional colocation space is therefore zero by default to avoid charging twice. Ancillary items must declare whether included in the base offer; included items are not charged again. A user specifying a real quote must verify component scope.

Missing real purchase/colocation/commitment quotes, measured production performance/power, inventory, deployment schedule, demand and resale evidence prevent procurement conclusions. B300 on-demand remains null. Llama 2's numerical oracle is secondary; its historical demand-scale origin is preserved as a synthetic design choice and never attributed to gpt-oss throughput.

Sensitivity bounds are illustrative: demand .5/1/1.5, acquisition .75/1/1.25, throughput .5/.7/.9, future rental .8/1/1.2 from month 13, commitment $32/$40/$48, discount 5%/10%/15%, electricity $.05/$.10/$.15 and residual 0%/20% of node acquisition. They are not confidence intervals. Combined adverse stresses preserve correlations as named scenarios, with no probabilities.

Pure numerical engine calls support testing synthetic controls. Public CLI admission additionally checks frozen source identities, metadata and checksums; arbitrary benchmark or evidence edits cannot enter as observed inputs. User measurements require the explicit measurement-kind/transfer treatment, and this MVP still admits only the two documented batch workload identities.

## Editing and disclosure

Sidebar controls cover preset, configuration, workload, horizon, demand multiplier, cash/rental limits and service assumptions. Economics expanders expose itemized costs, payment terms, power and residual assumptions. The advanced saved-input editor accepts the existing JSON contract, including custom month/block demand. Source observations remain immutable; overrides carry user-assumption provenance. B300 financial analysis requires an explicit price and rationale.

Do not interpret a missing source value as zero. Default zero ancillary charges are explicitly excluded or included costs, not observed free services. Historical source ages are evaluated against each run's stated review date; the UI exposes that date rather than fabricating live freshness.
