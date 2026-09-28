# Scope decisions and unresolved issues

- Packages 1–8 are implemented. Package 9 reviews documentation, licensing, reproducibility and presentation; it does not revise the analytical methodology. The latest user authorization permits Package 10 only after the Package 9 gate. No external publication or deployment is authorized.
- Created the specified project as a separate subdirectory of the existing workspace, preserving unrelated files. No Git remote or public repository was created.
- Preserved the original specification byte-for-byte and applied only corresponding amendments in build_specification.md. Added a separate amendment record. No economic formulas or MVP boundaries were redesigned.
- Preserved Section 5.4's immutable demand scale and Section 8.1's Llama arithmetic oracle as synthetic/historical controls. Primary gpt-oss anchors are 91,487.4/112,840 tokens/s; secondary Llama anchors 102,703/115,530.
- The direct pricing HTTP fetch returned 403. The approved manual acquisition path was used: a narrow factual transcription from the official page, reconciled by a second reading. No entire provider page was redistributed.
- Catalog scope is four CoreWeave GPU families, four selected benchmark rows and four catalog-only Crusoe/AWS reference offers required by the specification. Unconfirmed packaging and scheduled Capacity Block terms explicitly exclude these reference offers from engine economics; other acquisition-map sources remain research context.
- Filled in routine unspecified frontier sampling choices: acquisition line uses 21 points over .75–1.25; commitment line uses $1 increments over $32–$48. Specification demand and 20×20 grids are unchanged. All bounds and lack of crossings are explicit.
- The influence statistic is the range of fixed-policy advantage versus best feasible alternatives across tested sensitivity endpoints. Both fixed K and reoptimized outcomes are exported. It is not a probability.
- Reports add block/category/annual/provenance CSVs and results.json alongside the required memo, scenario and monthly ledger, to make existing audit requirements reviewable; no additional product scope is introduced.
- The author selected MIT for original project code. Third-party evidence retains upstream rights; both MLCommons results and policy Apache-2.0 license texts and attribution are retained.
- Remaining economic uncertainties: exact rental/purchased-system transfer, wall power, purchase/colo/contract quotes, delivery and actual capacity, realistic demand, economic life and residual. B300's quote-only price and memory discrepancy remain unresolved. Those issues block stronger conclusions, not the clearly labeled prototype.

- Final acceptance review caught a preset semantics issue: disappointment exposure must retain the fleet selected on the unshocked base demand. The report now separates that time-zero policy from the retrospective scenario optimum used only for regret. A regression test proves the default own:6 fleet is retained even when own:5 is the hindsight minimum.

## Package 9 review decisions

- Increased main-content top clearance and reduced oversized headings to keep the full Decision header below Streamlit's toolbar at laptop widths. Formatted unused-paid shares as one-decimal percentages. These are display changes only.
- Retained the original and amended specifications as historical requirements, not current status pages. README and current documentation describe implemented functionality.
- Added a network-blocked reproduction check for all three presets and every export, and a socket-blocked four-view AppTest. CI has one validation job; no publishing credentials or deployment automation.
- Kept one intentional README screenshot. Historical validation results are consolidated; local caches, redundant debug reports and development screenshots are excluded from review copies. Frozen evidence and the three distinct example output sets remain.

## Package 10 readiness boundary

- Preparation follows the passing Package 9 gate. Added an explicit Python 3.12 selector and a reviewed local/host procedure. The existing root entrypoint, source layout and Streamlit config remain the deployment inputs.
- `uv.lock` is the primary Community Cloud environment. The pinned requirements export is retained as required by the specification; hosts using it must additionally install the local editable project. No duplicate independent dependency set is maintained.
- Hosting instructions distinguish local telemetry settings from host overrides and local memory measurements from untested hosted concurrency. Linux CI and actual hosted smoke tests must still run after the author authorizes publication/deployment.
- No GitHub repository, Git remote, public URL, deployment, domain or credentials were created.
