# Licensing and third-party notices

The root [MIT License](LICENSE) applies to original project code and documentation. It does **not** relicense the third-party material in `data/snapshots/2026-09-27/evidence/`, quoted source facts, trademarks, or installed dependencies.

## MLCommons / CoreWeave submissions

Selected records and supporting system metadata, configuration files, accuracy summaries and performance logs come from [MLPerf Inference v6.1](https://github.com/mlcommons/inference_results_v6.1/tree/10ecdffda3bb94d71f0203a6ca8e20c17943f27c), commit `10ecdffda3bb94d71f0203a6ca8e20c17943f27c`, submitted by CoreWeave. The upstream [Apache-2.0 license](data/snapshots/2026-09-27/evidence/LICENSE.md) is retained verbatim. Original notices in the artifacts are preserved. The upstream root contains no separate NOTICE file at that commit.

`selected_summary.csv` is a subset of four unmodified records from the official summary. Selection is the project's modification; it is not the complete release. `summary_origin.json` records the full download hash. The download map and source catalog identify upstream locations; the manifest hashes every frozen artifact. Results are published submissions, **not measurements independently performed by this project**.

The retained [inference rules](https://github.com/mlcommons/inference_policies/blob/d3eba2f21026d868ad65cdcad2bb81e4a17ce3d3/inference_rules.adoc) use revision `d3eba2f21026d868ad65cdcad2bb81e4a17ce3d3`. Its separate [Apache-2.0 license](docs/licenses/mlcommons-inference-policies-Apache-2.0.txt) and [license provenance/hash](docs/licenses/provenance.json) accompany the original rules. That upstream root also contains no separate NOTICE file. This licensing supplement does not change the analytical snapshot.

MLPerf is a registered trademark of MLCommons. Company and product names identify sources only. No endorsement, certification of this economic model, employment, client relationship, or affiliation is implied.

## Provider pricing facts

CoreWeave, Crusoe and AWS pricing/billing extracts are narrow factual transcriptions from their official pages. They retain exact URLs, retrieval dates, source sections, units and limitations. Provider websites and their contents remain subject to their owners' rights; the project's MIT license grants no rights over them. No provider website copies, logos, marketing images or proprietary price quotes are included.

The Crusoe/AWS offers are catalog-only references; they do not establish matched performance, current inventory or an eligible three-year contract. No model weights, model datasets, GPU software binaries or private customer data are redistributed. Raw benchmark logs and rules are retained only for the selected results' reproducibility and compatibility audit.

## Dependencies

Dependencies are installed from the versions/hashes in `uv.lock` and `requirements.txt`, not vendored into this repository. Their own distribution licenses apply. The application requires no GPU runtime or model license grant because it never executes the models. Preserve these notices and the evidence licenses when redistributing the project.
