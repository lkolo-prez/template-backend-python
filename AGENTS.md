# AGENTS.md

Instructions for AI coding agents (Codex, and any tool implementing the
[agents.md](https://agents.md) open standard) working in this repository. Human
contributors should read `CONTRIBUTING.md`.

## Project overview

Production-grade FastAPI HTTP microservice template. Python 3.12, async-first,
managed with **uv**. Source: `src/app/`. Tests: `tests/`.

## Setup commands

```bash
task setup    # install locked deps (uv sync --frozen --all-groups) + pre-commit
# or, without Task:
uv sync --frozen --all-groups
```

## Development commands

| Task            | Command                  |
| --------------- | ------------------------ |
| Run service     | `task run`               |
| Lint            | `task lint`              |
| Format          | `task format`            |
| Format check    | `task format-check`      |
| Type check      | `task typecheck`         |
| Tests + coverage| `task test`              |
| Security scans  | `task security`          |
| Full gate       | `task all`               |

Underlying tools: `uv run ruff`, `uv run mypy`, `uv run pytest`,
`uv run bandit`, `uv run pip-audit`.

## Code style & conventions

- Python 3.12, full type annotations; `mypy --strict` must pass.
- Pydantic v2 models; input models use `ConfigDict(extra="forbid")`.
- structlog for logging (`get_logger(__name__)`); never `print`.
- Configuration only via `app.config.get_settings()` (env prefix `APP_`).
- Raise domain exceptions from `app.exceptions`; errors render as
  RFC 9457 `problem+json`. Do not leak stack traces to clients.
- Async everywhere: `async def`, `httpx.AsyncClient`, async tests.

## Testing instructions

- Run `task test`; the coverage gate is enforced (`--cov-fail-under=85`).
- Add unit tests under `tests/unit/`, integration tests under
  `tests/integration/` (use the `client` fixture from `tests/conftest.py`).
- `asyncio_mode = "auto"` is set; async tests need no extra decorator beyond
  the module-level `pytestmark` where used.

## Security & supply chain

- Never add long-lived secrets. Cloud auth is GitHub OIDC; signing is keyless
  cosign. Do not unpin GitHub Actions (pinned to full commit SHAs).
- Do not edit `uv.lock` by hand; update `pyproject.toml` then run `uv lock`.

## PR / commit instructions

- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, ...).
- Commits must be signed (verified). Run `task all` before opening a PR.
- PR titles also follow Conventional Commits (they drive release-please).
