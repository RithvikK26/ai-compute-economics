# Validation and reproducibility record

Tests validate arithmetic, contracts, published-source reconciliation and application behavior. They do not independently benchmark hardware, validate forecast accuracy, or establish customer savings. The frozen analytical snapshot is **2026-09-27**. No analytical methodology changed during the Package 9 review.

## Gates already completed

| Package | Gate evidence |
|---|---|
| 1–4 | Strict contracts, source hashes, DuckDB joins, independent whole-node capacity/billing fixtures, calendar and conservation checks |
| 5 | Independent cash/energy/PV fixtures; idle power, prepayment, terminal flows and category reconciliation |
| 6 | Feasibility, practical ties, fixed-fleet regret, discontinuous frontier brackets and 400-cell surface |
| 7 | 105 tests; complete CLI/memo/ledger exports and exact JSON reproduction |
| 8 | 120 tests: 105 engine/source/export tests plus 15 UI tests; four views, all presets, invalid edits, missing B300 price, downloads/import, isolation and label escaping |

Historical [Package 7 test results](validation/package7-tests.xml), [performance](validation/package7-performance.json), and [Package 8 test results](validation/package8-tests.xml) retain the original measurements; machine hostnames were removed from public review copies. They are historical gates, not claims about current hosted service performance.

## Package 9 review scope

The review updates documentation, original-code MIT licensing, upstream attribution, CI, offline verification, repository hygiene and presentation. The 57 pre-UI engine/data/scenario hashes remain unchanged. No source prices, benchmark scores, assumptions, formulas, feasibility rules or policy selection logic were modified.

The full test matrix contains 120 cases: UI 15, capacity 22, cash flows 20, catalog 10, exports 17, scenarios 9, sources 15, and units 12. The four-view AppTest now explicitly blocks outbound socket connections. `scripts/verify_reproduction.py` blocks network and compares all 10 files for each of three presets against checked-in fixtures and a fresh JSON replay: 60 file comparisons. Only `created_at_utc` is excluded from envelope equality, as defined by the existing hash contract.

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

For a cache-only install add `--offline` to `uv sync`; Python and dependency wheels must already be available. CI performs the same validations in one Ubuntu job. Local checks are executed; remote GitHub Actions and hosted startup are not claimed because nothing has been published.

## Performance protocol

Run each measurement in a separate process, without a concurrent test suite:

```sh
uv run --offline python scripts/measure_performance.py engine
uv run --offline python scripts/measure_performance.py app
```

Engine mode warms imports and one baseline evaluation, times three 65-policy demand paths, then times the full analysis including frontiers, stresses, sensitivities and 400 surface cells. App mode measures initial AppTest execution and each view rerun. Peak RSS uses the platform's process high-water mark, with macOS bytes versus Linux KiB handled explicitly. AppTest RSS includes imports, analysis and UI; it is not a browser measurement, multi-user load test or hosted resource limit. Each is one local sample; no percentile or uptime claim is made.

## Visual and integrity review

Four views are inspected at laptop dimensions, including the full Decision header at scroll position zero. Presentation-only corrections provide clearance below Streamlit's toolbar, smaller headings, human-readable cost legend names, comma-separated whole-dollar costs, and one-decimal unused-paid percentages. Large ledgers retain horizontal scrolling and full-precision exports; advanced controls remain in expanders.

Warnings and evidence classifications remain visible. Missing B300 price stays unavailable. The source/licensing audit verifies all 41 manifest entries, pinned upstream licenses and supplementary license hash. Credential-pattern and local-home-path scans, local Markdown link checks, and review of unsupported production/procurement/endorsement claims are included. Frozen third-party files and historical specification prose are retained verbatim and attributed, rather than rewritten as current project claims.

## Package 9 final gate — PASS

Clean Python 3.12.14 environment, macOS 26.3.1 arm64, uv 0.12.19. **120 passed, zero failures/errors/skips, in 120.39 seconds**. Lint, formatting, 41-artifact source validation, offline catalog rebuild, all 60 export comparisons, final network-blocked four-view AppTest, and the repository-review script passed. All 57 protected engine/data/scenario hashes match. Full [test cases](validation/package9-tests.xml) and [machine-readable measurements](validation/package9.json) are retained.

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


## Package 10 final gate — PASS

Resumed the existing deployment-readiness work after Package 9 passed; Package 9 was not repeated or revised. A separate clean source copy matched all 143 working project files before the final validation records were added. Its new Python 3.12.14 virtualenv was installed from the locked, populated offline cache with `--no-dev`. All **42 production packages were compatible**. `scripts/smoke_app.py` rendered the editable `app.py` entrypoint with sockets blocked, no app exception and all seven download controls. No development dependency was needed for this production smoke test.

The development group was then installed in that clean environment for final regression: **120 passed in 265.65 seconds, zero failures/errors/skips** (15 UI and 105 engine/source/export tests). Lint and formatting passed. All 41 frozen source artifacts and 57 protected engine/data/scenario hashes passed. The catalog rebuilt offline. The generated pinned production requirements matched the checked-in file byte for byte. All three presets matched their fixtures and exported-JSON replays with network blocked: **60 file comparisons in 63.218 seconds**. Separate sessions, unavailable inputs, invalid edits, source visibility and the decision frontier remain covered by the passing AppTests. Existing source-age and historical-snapshot labels remain intact.

Full [test cases](validation/package10-tests.xml) and [machine-readable results](validation/package10.json) are retained. The final documentation and repository review passed. No analytical code, methodology, economic assumptions, source data, policy logic or UI changed in Package 10; dependency versions and the requirements export are unchanged. MIT licensing and third-party notices from Package 9 are preserved.

The interrupted dependency check initially used an unwritable default uv cache; pointing it to the existing writable task cache resolved that execution setup issue. AppTest's normal bare-mode `missing ScriptRunContext` warning remains non-failing. The full-suite timing is a validation runtime, not a new isolated product-performance benchmark; Package 9's measured performance record remains unchanged.

The deployment guide and CI production smoke gate are prepared for Python 3.12 and the root `app.py` entrypoint. **No repository was published, no visibility was changed, and no application was deployed.** The first Linux CI run and actual hosted build/smoke test necessarily remain pending explicit publication/deployment approval. Hosted concurrency, resource limits and host-managed telemetry have not been validated by local tests. The original source-transfer, quote, power, delivery and demand uncertainties remain limitations on economic conclusions.
