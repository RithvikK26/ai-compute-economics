# Design decisions and remaining limitations

The public application uses a frozen analytical engine and evidence snapshot. Presentation code consumes engine outputs; it does not duplicate financial formulas. Historical requirements remain in the design specifications, with development instructions removed from their public copies.

- Preserved Section 5.4's immutable demand scale and Section 8.1's Llama arithmetic oracle as synthetic/historical controls. Primary gpt-oss anchors are 91,487.4/112,840 tokens/s; secondary Llama anchors 102,703/115,530.
- The direct pricing HTTP fetch returned 403. The manual acquisition path was used: a narrow factual transcription from the official page, reconciled by a second reading. No entire provider page was redistributed.
- Catalog scope is four CoreWeave GPU families, four selected benchmark rows and four catalog-only Crusoe/AWS reference offers required by the specification. Unconfirmed packaging and scheduled Capacity Block terms explicitly exclude these reference offers from engine economics; other acquisition-map sources remain research context.
- Filled in routine unspecified frontier sampling choices: acquisition line uses 21 points over .75–1.25; commitment line uses $1 increments over $32–$48. Specification demand and 20×20 grids are unchanged. All bounds and lack of crossings are explicit.
- The influence statistic is the range of fixed-policy advantage versus best feasible alternatives across tested sensitivity endpoints. Both fixed K and reoptimized outcomes are exported. It is not a probability.
- Reports add block/category/annual/provenance CSVs and results.json alongside the required memo, scenario and monthly ledger, to make existing audit requirements reviewable; no additional product scope is introduced.
- The author selected MIT for original project code. Third-party evidence retains upstream rights; both MLCommons results and policy Apache-2.0 license texts and attribution are retained.
- Remaining economic uncertainties: exact rental/purchased-system transfer, wall power, purchase/colo/contract quotes, delivery and actual capacity, realistic demand, economic life and residual. B300's quote-only price and memory discrepancy remain unresolved. Those issues block stronger conclusions, not conditional analysis.

- Final acceptance review caught a preset semantics issue: disappointment exposure must retain the fleet selected on the unshocked base demand. The report now separates that time-zero policy from the retrospective scenario optimum used only for regret. A regression test proves the default own:6 fleet is retained even when own:5 is the hindsight minimum.

## Cross-platform numerical reproducibility

Linux exposed 1–4 ULP differences in platform-dependent present-value dot products. Four affected reductions now use explicit float64 products and deterministic compensated summation. The largest observed analysis difference was $0.000000008. Policy winners, practical tie sets, threshold brackets and decision-surface winners were unchanged. Focused tests, integrity hashes and repeated Linux reproduction checks document the correction. Annual aggregation was not changed. See [validation](validation.md).

## Application and hosting

- The four views share one reporting adapter and preserve session-local scenarios. Only immutable public catalog results are cached globally.
- The lockfile is the primary environment. Hosts using the requirements export must also install the local project in editable mode.
- Large audit tables scroll horizontally. Downloads preserve complete machine-readable fields and full precision.
- Hosted smoke tests establish functional operation, not concurrent-user capacity, availability guarantees or production throughput.
