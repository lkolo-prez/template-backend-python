<p align="center">
  <a href="https://aircloud.com.pl"><img src=".github/assets/banner.png" alt="AIRCLOUD: DevOps, cloud and AI engineering" width="100%"></a>
</p>

# template-backend-python

**Production-grade FastAPI microservice template with a hardened distroless image and supply-chain CI.**

[![CI](https://github.com/lkolo-prez/template-backend-python/actions/workflows/ci.yml/badge.svg)](https://github.com/lkolo-prez/template-backend-python/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)

A production-grade **FastAPI HTTP microservice** template for the `aircloud`
organisation. It ships an opinionated, secure-by-default baseline so a new
service can go from `Use this template` to a signed, attested container image in
minutes.

> This is a **template repository**. The org (`aircloud`), container registry
> (`ghcr.io/aircloud`), and Azure naming prefix (`aircloud`) are examples — see
> [Customising](#customising-the-template) to replace them.

## What's inside

- **FastAPI + Python 3.12**, async-first, typed end to end (`mypy --strict`).
- **uv** for fast, reproducible dependency management (`uv.lock`).
- **Pydantic v2** models and **pydantic-settings** typed config (`APP_*` env).
- **structlog** JSON logging with per-request correlation IDs.
- **OpenTelemetry** tracing (opt-in via `otel` extra).
- **httpx** async HTTP client.
- Security middleware (CSP, HSTS, frame/sniff protection) + RFC 9457
  `problem+json` error contract.
- Liveness/readiness probes (`/health/live`, `/health/ready`).
- Hardened **multi-stage Dockerfile** → distroless `nonroot`, read-only friendly,
  `HEALTHCHECK`, hadolint-clean.
- Full supply-chain CI: SBOM (syft → CycloneDX), keyless **cosign** signing,
  **SLSA build provenance**, **Trivy**, **CodeQL**, **Semgrep**, **gitleaks**,
  **OpenSSF Scorecard**, dependency review, **bandit**, **pip-audit**.
- Conventional Commits + **release-please** automated releases.
- AI-assistant configs: `CLAUDE.md`, `AGENTS.md`, Copilot, Cursor, dev container.

### Architecture

```text
src/app/
  main.py                  # create_app() factory + ASGI `app`
  config.py                # pydantic-settings (APP_* env), get_settings()
  logging.py               # structlog JSON logging
  telemetry.py             # optional OpenTelemetry tracing
  exceptions.py            # domain errors + problem+json handlers
  middleware/
    request_id.py          # X-Request-ID correlation
    security_headers.py    # baseline HTTP security headers
  api/
    health.py              # /health/live, /health/ready
    v1/widgets.py          # example resource (models + router)
```

See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for diagrams and runbooks.

## Usage

Create a new repository from this template (or use **Use this template** on GitHub):

```bash
gh repo create <your-org>/<name> --template lkolo-prez/template-backend-python --private --clone
```

Prerequisites: [`uv`](https://docs.astral.sh/uv/),
[`Task`](https://taskfile.dev/), Docker (for container targets).

```bash
# 1. Install locked dependencies + pre-commit hooks
task setup

# 2. Run the service with hot reload (http://127.0.0.1:8000)
task run

# 3. Explore the API (non-production only)
open http://127.0.0.1:8000/docs

# 4. Run the full local quality gate
task all
```

Without Task, use the underlying tools, e.g. `uv run uvicorn app.main:app
--reload`, `uv run pytest`, `uv run ruff check .`.

### Example requests

```bash
curl -s http://127.0.0.1:8000/health/ready | jq

curl -s -X POST http://127.0.0.1:8000/v1/widgets \
  -H 'content-type: application/json' \
  -d '{"name":"Flux Capacitor","quantity":88}' | jq
```

## Configuration

All settings are environment variables prefixed `APP_` (see
[`.env.example`](./.env.example)). Highlights:

| Variable                          | Default                   | Description                          |
| --------------------------------- | ------------------------- | ------------------------------------ |
| `APP_ENVIRONMENT`                 | `local`                   | `local`/`dev`/`staging`/`production` |
| `APP_PORT`                        | `8000`                    | HTTP bind port                       |
| `APP_LOG_JSON`                    | `true`                    | JSON vs console logs                 |
| `APP_OTEL_ENABLED`                | `false`                   | Enable OTLP tracing export           |
| `APP_OTEL_EXPORTER_OTLP_ENDPOINT` | _none_                    | OTLP collector endpoint              |
| `APP_CORS_ALLOW_ORIGINS`          | _empty_                   | Comma-separated CORS origins         |

## Container

```bash
task build          # docker build -t ghcr.io/aircloud/template-backend-python:local
task run-container   # runs read-only, cap-drop ALL
```

The image runs as non-root uid `65532` on `gcr.io/distroless/python3-debian12`,
exposes `8000`, and includes a `HEALTHCHECK` hitting `/health/live`.

## CI / CD & supply chain

| Workflow                  | Purpose                                                          |
| ------------------------- | --------------------------------------------------------------- |
| `ci.yml`                  | ruff (lint+format), mypy, pytest+coverage, bandit, pip-audit, gitleaks |
| `codeql.yml`              | CodeQL static analysis (Python)                                 |
| `semgrep.yml`             | Semgrep SAST                                                     |
| `container.yml`           | Build, Trivy scan, SBOM, cosign sign, SLSA provenance (reusable) |
| `release.yml`             | release-please + signed release image                           |
| `scorecard.yml`           | OpenSSF Scorecard                                               |
| `dependency-review.yml`   | PR dependency/license review                                    |

All GitHub Actions are **pinned to full commit SHAs**, every workflow declares
**least-privilege permissions**, uses **step-security/harden-runner**, and cloud
auth uses **GitHub OIDC** (no long-lived secrets). Image signing is **keyless
cosign**.

> Verify a published image:
>
> ```bash
> cosign verify ghcr.io/aircloud/template-backend-python:<tag> \
>   --certificate-identity-regexp '^https://github.com/aircloud/template-backend-python/.github/workflows/.+' \
>   --certificate-oidc-issuer https://token.actions.githubusercontent.com
> ```

## Dependency updates

Both **Dependabot** (`.github/dependabot.yml`) and **Renovate**
(`.github/renovate.json`) configs are provided. **Enable only one** for the live
repo to avoid duplicate PRs — Renovate is recommended for digest-pinning Actions
and Docker images; delete the other config.

## Releasing

Merging Conventional Commits to `main` lets **release-please** open/maintain a
release PR. Merging that PR tags `vX.Y.Z`, updates `CHANGELOG.md`, and publishes
a signed, attested image. See [`docs/BRANCH-PROTECTION.md`](./docs/BRANCH-PROTECTION.md)
for the required ruleset (2 reviews, CODEOWNERS, signed commits, linear history).

## Customising the template

1. Replace `aircloud` (org), `ghcr.io/aircloud` (registry), and `template-backend-python`
   (service/image name) across `pyproject.toml`, workflows, `Dockerfile`,
   `CODEOWNERS`, and docs.
2. Update `CODEOWNERS` teams to ones that exist in your org.
3. Confirm the org reusable workflow ref
   (`aircloud/.github/.github/workflows/reusable-container.yml@<sha>`) exists, or
   enable the inline fallback job in `container.yml`.
4. Run `uv lock` to generate a real lockfile, then `task all`.

## Contributing & security

- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — workflow, commits, signed commits.
- [`SECURITY.md`](./SECURITY.md) — private reporting, SLAs, `security.txt`.
- [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).

## License

[Apache-2.0](./LICENSE) © 2026 aircloud.

---

## Part of the AIRCLOUD golden path

| Repository | What it is |
| --- | --- |
| [00-engineering-standards](https://github.com/lkolo-prez/00-engineering-standards) | Golden paths, security baseline, AI-assistant policy (handbook) |
| [template-terraform-azure](https://github.com/lkolo-prez/template-terraform-azure) | Terraform on Azure: private AKS, Key Vault, ACR, OIDC, policy-as-code |
| [template-gitops-argocd](https://github.com/lkolo-prez/template-gitops-argocd) | Argo CD, Kustomize, Argo Rollouts, Kyverno, External Secrets |
| **template-backend-python** (this repo) | FastAPI, Python 3.12, uv, ruff, pytest |
| [template-backend-go](https://github.com/lkolo-prez/template-backend-go) | Go 1.23, chi, slog, OpenTelemetry, golangci-lint |
| [template-backend-typescript](https://github.com/lkolo-prez/template-backend-typescript) | Node 22, TypeScript, Fastify 5, Zod, Vitest, pnpm |
| [template-frontend-nextjs](https://github.com/lkolo-prez/template-frontend-nextjs) | Next.js 15, React 19, Tailwind v4, Playwright, Lighthouse CI |
| [.github](https://github.com/lkolo-prez/.github) | Reusable CI/CD workflows and community-health defaults |

Terraform modules for Azure: [AIRCLOUD-PL](https://github.com/AIRCLOUD-PL).

Built and maintained by [AIRCLOUD](https://aircloud.com.pl): DevOps, cloud and AI engineering. Need help adopting the golden path? See [aircloud.com.pl/consulting](https://aircloud.com.pl/consulting).
