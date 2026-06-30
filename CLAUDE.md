# CLAUDE.md

Guidance for Claude Code (and compatible agents) working in this repository.

## What this is

A production-grade FastAPI HTTP microservice template. Python 3.12, async-first,
managed with **uv**. Application code is in `src/app/`; tests in `tests/`.

## Environment & commands

This repo uses [`uv`](https://docs.astral.sh/uv/) and
[`Task`](https://taskfile.dev/). Prefer Task targets; they wrap the real tools.

```bash
task setup         # uv sync --frozen --all-groups + install pre-commit hooks
task run           # uvicorn with reload on 127.0.0.1:8000
task lint          # ruff check
task format        # ruff format + ruff check --fix
task format-check  # ruff format --check + ruff check  (CI gate)
task typecheck     # mypy --strict
task test          # pytest with coverage gate (>= 85%)
task security      # bandit + pip-audit
task sbom          # syft -> CycloneDX SBOM
task build         # docker build
task all           # full local gate: format-check, typecheck, test, security
```

If `task` is unavailable, run the underlying command, e.g.
`uv run pytest`, `uv run ruff check .`, `uv run mypy`.

## Architecture (where things live)

- `src/app/main.py` — `create_app()` factory + ASGI `app`. Wires middleware,
  routers, exception handlers, telemetry.
- `src/app/config.py` — `Settings` (pydantic-settings); access via
  `get_settings()`. Env vars are prefixed `APP_`.
- `src/app/logging.py` — structlog JSON logging. Use `get_logger(__name__)`.
- `src/app/telemetry.py` — optional OpenTelemetry (extras: `otel`).
- `src/app/exceptions.py` — domain errors + RFC 9457 `problem+json` handlers.
- `src/app/middleware/` — `request_id.py`, `security_headers.py`.
- `src/app/api/health.py` — `/health/live`, `/health/ready`.
- `src/app/api/v1/widgets.py` — example versioned resource (models + router).

## Conventions (must follow)

- **Types**: code must pass `mypy --strict`. Annotate everything; avoid `Any`.
- **Models**: Pydantic v2; input models use `ConfigDict(extra="forbid")`.
- **Errors**: raise `app.exceptions` types; never leak internals in responses.
- **Logging**: structlog only, structured events. No `print`.
- **Async**: `async def` handlers, `httpx.AsyncClient`, async tests.
- **Config**: only via `get_settings()`. No reading `os.environ` ad hoc.
- **Commits**: Conventional Commits; commits must be signed/verified.
- **No secrets**: cloud auth is GitHub OIDC; signing is keyless cosign.

## Adding a feature (typical flow)

1. Add/extend models + router under `src/app/api/v1/`.
2. Add unit tests (`tests/unit/`) and integration tests (`tests/integration/`).
3. `task all` until green; keep coverage at/above the gate.
4. Conventional-commit, open a PR; CI must pass and CODEOWNERS must approve.

## Guardrails

- Do not hand-edit `uv.lock`; change `pyproject.toml` and run `uv lock`.
- Do not unpin GitHub Actions (all are pinned to a full commit SHA).
- Do not weaken security middleware or the coverage gate to make CI pass.
