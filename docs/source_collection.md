# Source collection

The admitted snapshot contains four CoreWeave North America on-demand catalog entries and four exact MLPerf anchors: B200/B300 × primary gpt-oss-120b / secondary Llama 2 70B 99.9 Offline. The source catalog also preserves Crusoe H100/H200 headlines ($3.90/$4.29 per GPU-hour, packaging unconfirmed) and AWS Capacity Blocks p5e.48xlarge Ohio ($47.76/instance-hour) and p6-b300.48xlarge Oregon ($112.32/instance-hour). These four rows are catalog-only, never generic on-demand or fixed three-year contract inputs. Other acquisition-map sources remain research context.

Official summary: https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/10ecdffda3bb94d71f0203a6ca8e20c17943f27c/summary.csv . Its full download hash is in summary_origin.json. Selected records preserve the original schema. System JSON, measurements, configuration files, accuracy and performance logs share the same commit. Manifest checks cover all curated tables and artifacts. stage_summary validates a proposed refresh without replacing the prior snapshot.

CoreWeave https://www.coreweave.com/pricing was read twice through web access. Direct HTTP returned 403; the saved artifact is a manual factual extract with section/column labels. H100 $49.24, H200 $50.44, B200 $68.80 per complete eight-GPU node-hour; B300 is null/contact-sales. Spot and inference single-GPU columns are distinct. Host, electricity and local storage belong to the node boundary; ancillary services are not established.

Primary scores: B200 91487.4, B300 112840 tokens/s. Secondary: 102703, 115530. Primary quality is 99% of 83.13% exact match with benchmark-defined datasets/repeat weighting, not Llama's 99.9% FP32 ROUGE/output-length threshold.

Submission hardware uses NVSwitch, optimized FP4 software, particular host/driver settings and Vast NFS. Advertised cloud nodes and purchased OEM systems are conditional transfers. B300 memory remains raw (270 GB catalog label and distinct system metadata); no speculative reconciliation to vendor 288 GB. TGP is not wall power.

Offers expire for freshness purposes after 30 days; benchmarks/configurations/contracts after 180; annual references after 400. Historical mode preserves values with warnings. Catalog presence is not inventory. Runtime operation is offline.

## Audit and refresh boundary

The [manifest](../data/snapshots/2026-09-27/manifest.json) hashes 41 artifacts: six curated tables plus 35 evidence files. Source rows and the download map retain URLs and locators. The full-summary download hash identifies the original upstream object; only the four selected rows are redistributed. Missing download attempts in the map are acquisition diagnostics, not successful evidence files.

The rules license is retained separately under `docs/licenses/` with its pinned URL and SHA-256. It supplements attribution without changing a source checksum. See [third-party notices](../THIRD_PARTY_NOTICES.md). No logos, model weights, datasets or provider HTML dumps are included.

For a future refresh, save a new staged artifact, record URL/date/revision/hash and units, run the strict summary parser and source reconciliation, then review the changed observation before admitting it. Do not edit the frozen snapshot in place or replace missing quotes with proxy prices. Runtime and CI do not scrape or refresh sources. Integrity checks verify the retained snapshot; they do not revalidate historical offers as live prices.
