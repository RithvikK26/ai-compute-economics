# Validation and reproducibility record

Tests validate arithmetic, contracts, published-source reconciliation and application behavior. They do not independently benchmark hardware, validate forecast accuracy, or establish customer savings. The frozen analytical snapshot is **2026-09-27**. Historical local records below precede the deterministic-reduction correction and public deployment.

## Coverage

The original suite contained 120 tests: 105 engine/source/export checks and 15 application tests. Four focused deterministic-reduction checks brought the published suite to 124. Coverage includes independent arithmetic oracles, calendar/capacity conservation, source hashes, feasibility, practical ties, fixed-fleet regret, threshold brackets, 400-cell surfaces, all four views, presets, invalid inputs, missing B300 prices, import/export and separate sessions.

Historical [engine tests](validation/engine-tests.xml), [engine performance](validation/engine-performance.json), and [UI tests](validation/ui-tests.xml) retain their original measurements. Hostnames were removed from public copies. They are not current hosted-service performance claims.

The reproduction script compares all ten files for three presets against checked-in outputs and a fresh JSON replay: 60 file comparisons. Only the declared creation timestamp is excluded from scenario-envelope equality. Reproduction and AppTests block outbound sockets.

## Fresh environment procedure

A clean source copy and a newly created Python 3.12 virtualenv are used, without reusing the working project's installed packages. uv's downloaded wheel cache is reused and install runs with `--offline`; this is a clean environment test, **not a cold internet-download benchmark**. The first offline attempt could not discover Python on PATH; placing the already installed Python 3.12.14 interpreter's bin directory on PATH resolved that environmental prerequisite without changing dependencies.

From a repository root with Python 3.12 discoverable and uv installed:

```sh
uv sync --locked --python 3.12
mkdir -p artifacts
uv run --offline compute-economics validate-data
uv run --offline compute-economics catalog --output artifacts/catalog.duckdb
uv run --offline compute-economics run scenarios/stable_demand.json --output artifacts/stable
uv run --offline compute-economics run artifacts/stable/scenario.json --output artifacts/replayed
uv run --offline python scripts/verify_reproduction.py
uv run --offline python scripts/review_repository.py
uv run --offline ruff check .
uv run --offline ruff format --check .
uv run --offline pytest -q --junitxml=artifacts/tests.xml
uv run --offline streamlit run app.py --server.address 127.0.0.1
```

For a cache-only install add `--offline` to `uv sync`; Python and dependency wheels must already be available. CI performs the same validations in one Ubuntu job. The public Linux CI and hosted checks are recorded below.

## Performance protocol

Run each measurement in a separate process, without a concurrent test suite:

```sh
uv run --offline python scripts/measure_performance.py engine
uv run --offline python scripts/measure_performance.py app
```

Engine mode warms imports and one baseline evaluation, times three 65-policy demand paths, then times the full analysis including frontiers, stresses, sensitivities and 400 surface cells. App mode measures initial AppTest execution and each view rerun. Peak RSS uses the platform's process high-water mark, with macOS bytes versus Linux KiB handled explicitly. AppTest RSS includes imports, analysis and UI; it is not a browser measurement, multi-user load test or hosted resource limit. Each is one local sample; no percentile or uptime claim is made.

## Visual and integrity review

Four views are inspected at laptop dimensions, including the full Decision header at scroll position zero. Presentation-only corrections provide clearance below Streamlit's toolbar, smaller headings, human-readable cost legend names, comma-separated whole-dollar costs, and one-decimal unused-paid percentages. Large ledgers retain horizontal scrolling and full-precision exports; advanced controls remain in expanders.

Warnings and evidence classifications remain visible. Missing B300 price stays unavailable. The source/licensing audit verifies all 41 manifest entries, pinned upstream licenses and supplementary license hash. Credential-pattern and local-home-path scans, local Markdown link checks, and review of unsupported production/procurement/endorsement claims are included. Frozen third-party files are retained verbatim and attributed. Historical requirements retain their technical content; development-only handoff instructions are omitted from the public copies.

## Historical reproducibility validation

Clean Python 3.12.14 environment, macOS 26.3.1 arm64, uv 0.12.19. **120 passed, zero failures/errors/skips, in 120.39 seconds**. Lint, formatting, 41-artifact source validation, offline catalog rebuild, all 60 export comparisons, final network-blocked four-view AppTest, and the repository-review script passed. All 57 protected engine/data/scenario hashes match. Full [test cases](validation/reproducibility-tests.xml) and [machine-readable measurements](validation/reproducibility-validation.json) are retained.

| Measured operation | Seconds |
|---|---:|
| New virtualenv / locked offline installation from populated cache | 0.848 |
| Source validation (separate CLI process) | 2.619 |
| Catalog build (separate CLI process) | 11.744 |
| Stable-demand CLI export | 4.740 |
| Exported-JSON CLI replay | 4.579 |
| All three presets: fixture comparison and replay | 24.102 |
| Warm three-path / 65-policy comparison | 0.0233 |
| Full analysis including 400-cell surface | 3.945 |

| Final initial AppTest render | 5.559 |

Engine peak RSS: **66.8 MiB**. Final AppTest-process peak RSS: **233.4 MiB**. Final view reruns ranged from **0.065 to 0.102 seconds**. The engine sample meets the specification's local <3-second comparison, <10-second full-grid analysis and <512 MiB analytical-process targets on this host. This does not guarantee hosted latency or capacity.

A real Streamlit server from the clean virtualenv was opened locally and all four views inspected. AppTest emits its normal bare-mode `missing ScriptRunContext` startup warning; no app exception occurred. No network access is needed after install; source hyperlinks and later package installation are separate. The first offline interpreter-discovery failure and its PATH resolution are disclosed above.


## Production validation

A separate clean source copy matched all 143 working project files before the final validation records were added. Its new Python 3.12.14 virtualenv was installed from the locked, populated offline cache with `--no-dev`. All **42 production packages were compatible**. `scripts/smoke_app.py` rendered the editable `app.py` entrypoint with sockets blocked, no app exception and all seven download controls. No development dependency was needed for this production smoke test.

The development group was then installed in that clean environment for final regression: **120 passed in 265.65 seconds, zero failures/errors/skips** (15 UI and 105 engine/source/export tests). Lint and formatting passed. All 41 frozen source artifacts and 57 protected engine/data/scenario hashes passed. The catalog rebuilt offline. The generated pinned production requirements matched the checked-in file byte for byte. All three presets matched their fixtures and exported-JSON replays with network blocked: **60 file comparisons in 63.218 seconds**. Separate sessions, unavailable inputs, invalid edits, source visibility and the decision frontier remain covered by the passing AppTests. Existing source-age and historical-snapshot labels remain intact.

Full [test cases](validation/production-tests.xml) and [machine-readable results](validation/production-validation.json) are retained. The final documentation and repository review passed. No analytical code, methodology, economic assumptions, source data, policy logic or UI changed during this production-only check; dependency versions and the requirements export are unchanged. MIT licensing and third-party notices from the prior review are preserved.

The interrupted dependency check initially used an unwritable default uv cache; pointing it to the existing writable task cache resolved that execution setup issue. AppTest's normal bare-mode `missing ScriptRunContext` warning remains non-failing. The full-suite timing is a validation runtime, not a new isolated product-performance benchmark; the earlier measured performance record remains unchanged.

## Linux reproducibility and hosted verification

[Main validation](https://github.com/RithvikK26/ai-compute-economics/actions/runs/36474909100) passed on Linux after the deterministic PV reduction correction: **124 tests and five complete reproduction runs**. The fix addresses 1–4 ULP platform-dependent reductions, with a maximum observed analysis difference of $0.000000008. Winners, ties, thresholds and all decision-surface winners were unchanged. The integrity record identifies the one corrected engine file; all other 56 original protected hashes remain unchanged. Reproduction failures now retain generated files and comparison diagnostics as CI artifacts.

The [public application](https://ai-compute-economics-ln4kzm3c2kn74qbpntdomz.streamlit.app) passed hosted smoke testing on October 2, 2026: three presets, all four views, unavailable B300 pricing, JSON replay, seven downloads, historical-snapshot disclosure, conditional language and source visibility. Replayed results were byte-identical across all nine non-envelope files; input and output hashes also matched. Laptop rendering was inspected. Private host build logs were not inspected in that public-app review. Hosted concurrency, resource ceilings and telemetry remain outside this test.

## Presentation regression validation

October 3, 2026, local Python 3.12: **126 tests passed, zero failures/errors/skips**, including 17 application tests. Formatting, lint, dependency consistency, frozen source integrity, offline catalog construction, repository review, all 60 fixture/replay comparisons, deterministic-reduction decision equivalence and the network-blocked production entrypoint smoke test passed. All 96 protected engine, data, scenario, example, fixture and dependency files were byte-identical to the pre-polish baseline.

The four views and three presets were inspected at 1440 × 1000. Missing B300 pricing, invalid-input retention, JSON import/replay and all seven downloads passed. The downloaded audit ZIP matched all nine non-envelope example files byte for byte; the scenario envelope matched apart from its declared creation timestamp. Copy and table formatting changed only presentation. An earlier isolated application-test run encountered three timeouts; those cases and the subsequent complete suite passed without changing application code or timeout limits.
