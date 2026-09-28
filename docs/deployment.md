# Deployment readiness and local operation

**Prepared for review; not published or deployed.** Package 10 prepares the existing application for Streamlit Community Cloud. No GitHub repository, remote, public URL, credentials or hosted app has been created. Publication and deployment remain separate approval gates.

## Tested local path

Use Python 3.12 and uv 0.12.19 or a compatible newer uv. From the repository root:

```sh
uv sync --locked --python 3.12
mkdir -p artifacts
uv run --offline compute-economics validate-data
uv run --offline python scripts/verify_reproduction.py
uv run --offline python scripts/review_repository.py
uv run --offline ruff check .
uv run --offline ruff format --check .
uv run --offline pytest -q
uv run --offline streamlit run app.py --server.address 127.0.0.1
```

Open the printed localhost URL. Add `--server.port 8502` if needed. Stop with `Ctrl+C`. Installation may download packages; application and example operation need no network afterward. For an entirely offline install, Python and the locked dependency wheels must already be available and `--offline` must also be passed to `uv sync`.

## Production-only verification

The Package 10 clean environment was first installed with development dependencies excluded. All 42 installed packages were compatible and the initial app rendered with outbound sockets blocked, including seven download controls. This validates the local production dependency set and editable entrypoint; it is not a hosted deployment test. The final regression results are recorded in [validation.md](validation.md#package-10-final-gate--pass).

To repeat the production gate before adding development tools:

```sh
uv sync --locked --no-dev --python 3.12
uv pip check --python .venv/bin/python
.venv/bin/python scripts/smoke_app.py
```

The smoke test uses Streamlit's bundled AppTest and does not require pytest. CI executes this gate before installing the development group for the full suite.

## Host configuration

| Item | Prepared value |
|---|---|
| Repository root | Contents of this project directory, not its parent workspace |
| Entrypoint | `app.py` |
| Branch | `main` after an approved repository is created |
| Python | Explicitly select **3.12**; `.python-version` records the local minor version |
| Primary environment | Root `pyproject.toml` + `uv.lock` |
| Production installation | `uv sync --locked --no-dev --python 3.12` |
| Configuration | `.streamlit/config.toml` at repository root |
| Required bundled files | `src/`, `data/`, `scenarios/`, `app.py`, dependency/configuration files |
| Secrets / external database / GPU | None |
| System packages | No `packages.txt` required by this implementation |
| Persistence | User downloads; filesystem and sessions are disposable |

Community Cloud currently prioritizes `uv.lock` over `requirements.txt`. Keep the lockfile as the primary environment; the requirements file is a synchronized fallback export, not a second independent resolver. [Dependency-file rules](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

The `src/` package must be installed. `uv sync` installs the local project in editable form, which also preserves the existing repository-relative evidence lookup. `requirements.txt` contains third-party production dependencies only. On another host that installs that file directly, run the additional editable-project install:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Do not deploy a detached wheel without its repository evidence. Regenerate the fallback without manually editing versions:

```sh
uv export --locked --no-header --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt
```

CI verifies exact equality with that export. Community Cloud executes from the repository root and reads `.streamlit/config.toml` there; the supplied paths match that layout. [File organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).

## Final publication steps — only after explicit approval

1. Confirm the GitHub owner, repository name and visibility with the author. Run the validation commands above on the exact reviewed files.
2. From this directory, initialize a local repository if needed (`git init -b main`), review `git status --short --ignored`, stage the project files, inspect `git diff --cached --stat`, and commit. Do not add `.venv`, private scenarios, caches or `artifacts/`.
3. Create the approved GitHub repository. Add its approved URL as `origin`, then push `main`. Repository creation, visibility changes and `git push` have **not** been performed by this work.
4. Let the `validate` GitHub Actions job complete successfully on Linux. Local macOS results do not substitute for this first remote run. Fix any platform-specific failure before deploying.
5. Separately obtain approval for deployment and the intended app visibility. In Community Cloud, choose **Create app**, select the approved repository and `main`, enter `app.py`, and explicitly choose Python **3.12** in Advanced settings. Leave secrets empty. Confirm visibility and deploy only after that approval. [Deployment controls](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
6. Inspect build logs for the locked dependency versions and successful local-project import. Smoke-test the three presets, four views, missing B300 pricing, downloads and JSON replay on the actual host. Verify the historical snapshot and conditional language remain visible before sharing the URL.

No domain, account authorization, billing action, GitHub remote or deployment automation is preconfigured. The remaining inputs are the approved owner/repository/visibility and host account—not an economic-model redesign.

## Resource, state and privacy limits

User scenarios/results/downloads live in session state and private temporary export directories; only public catalog query results are cached globally. Restarting the app discards session state. No secrets, arbitrary URL fetcher, SQL/shell console or executable upload is exposed. Downloads are the persistence mechanism.

Local telemetry is disabled in the config. Community Cloud documents host-managed configuration overrides, including usage telemetry, so local settings are not a promise of identical hosted privacy behavior. It also runs on Linux; select the supported Python minor version rather than relying on host defaults. [Host limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status).

The full grid runs synchronously per submission. Local measured memory and runtime are in [validation.md](validation.md); concurrent-user load, hosted memory ceilings, availability and cold starts remain unmeasured. Community Cloud can stop apps that exceed account resource limits. Do not infer unlimited capacity or an SLA from local tests. [Resource-limit guidance](https://docs.streamlit.io/knowledge-base/deploy/resource-limits).

No insecure CORS/XSRF bypasses, Docker image, background service or paid dependency have been introduced. If the first approved deployment fails, inspect its logs and revert the offending code/dependency change; do not silently alter economic assumptions or refresh the frozen source snapshot to make a host build pass.
