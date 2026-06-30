# GitHub Copilot — repository custom instructions

These instructions apply to Copilot Chat and code completion in this repository.

## Project

Production-grade HTTP microservice. Python 3.12, FastAPI, async-first. Package
and environment management is via **uv** (never `pip install` directly; never
edit `uv.lock` by hand). Source lives under `src/app/`; tests under `tests/`.

## Hard rules

- Always add type annotations; the codebase passes `mypy --strict`. No `Any`
  unless unavoidable and justified with a comment.
- Use Pydantic v2 models for all request/response bodies; set
  `model_config = ConfigDict(extra="forbid")` on input models.
- Log via `structlog` (`get_logger(__name__)`), structured key-value events.
  Never use `print` or the stdlib `logging` module directly.
- Read configuration only through `app.config.get_settings()`.
- Raise the domain exceptions in `app.exceptions` (`NotFoundError`, etc.); they
  are rendered as RFC 9457 `problem+json`. Never return raw 500s with details.
- Async I/O only — use `httpx.AsyncClient`, `async def` handlers, and
  `pytest.mark.asyncio` tests.
- Never introduce long-lived secrets. Cloud auth uses GitHub OIDC; image signing
  is keyless cosign.

## Conventions

- Conventional Commits for every commit and PR title (e.g. `feat(widgets): ...`).
- New endpoints go under a versioned router (`src/app/api/v1/`), with models,
  a router, and both unit and integration tests.
- Run `task all` before pushing (lint, format-check, typecheck, test, security).

## Tooling commands

- Format: `task format` (ruff). Lint: `task lint`. Types: `task typecheck`.
- Test with coverage gate: `task test`. Security: `task security`.
