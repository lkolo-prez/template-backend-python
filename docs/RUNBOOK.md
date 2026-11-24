# Operational runbook

Operational reference for running **template-backend-python** (FastAPI) in
production. It is consistent with `src/app/`, `Dockerfile`, `Taskfile.yml`, and
`.env.example`. Replace the example org/registry/service names when you adopt
the template.

## Service at a glance

| Property            | Value                                                      |
| ------------------- | ---------------------------------------------------------- |
| Runtime             | Python 3.12, FastAPI, ASGI via `uvicorn app.main:app`      |
| Container           | `gcr.io/distroless/cc-debian13:nonroot` + bundled CPython 3.12 (uid `65532`) |
| Image               | `ghcr.io/aircloud/template-backend-python`                 |
| Listen port         | `8000` (container `APP_HOST=0.0.0.0`)                       |
| Workers             | 1 per container; scale horizontally via replicas           |
| Logs                | structlog JSON to stdout                                    |
| Config              | environment variables prefixed `APP_` (see `config.py`)    |

## Endpoints

### Health probes (`src/app/api/health.py`)

| Endpoint         | Purpose   | Success           | Failure                          |
| ---------------- | --------- | ----------------- | -------------------------------- |
| `GET /health/live`  | Liveness  | `200` `{"status":"alive",...}` | process down → orchestrator restarts |
| `GET /health/ready` | Readiness | `200` `{"status":"ready","checks":{...}}` | `503` `{"status":"not_ready",...}` when any check is false |

```bash
curl -s http://127.0.0.1:8000/health/live  | jq
curl -si http://127.0.0.1:8000/health/ready          # inspect status code
```

- **Liveness** is dependency-free; a failure means the process is wedged — let
  the orchestrator restart it. It is also the container `HEALTHCHECK` target
  (`Dockerfile`: 30s interval, 3s timeout, 10s start period, 3 retries).
- **Readiness** is where dependency checks belong (DB, cache, upstreams). The
  template ships only a `self: True` check — extend the `checks` dict in
  `health.py`. A `503` removes the instance from the load balancer without
  killing it.

### Application API

| Endpoint                | Notes                                            |
| ----------------------- | ------------------------------------------------ |
| `GET /v1/widgets`       | List (query: `limit` 1–100 default 20, `offset`) |
| `POST /v1/widgets`      | Create (`201`)                                   |
| `GET /v1/widgets/{id}`  | Fetch one (`404` if missing)                     |
| `PATCH /v1/widgets/{id}`| Partial update                                   |
| `DELETE /v1/widgets/{id}`| Delete (`204`)                                  |
| `GET /docs`, `/redoc`, `/openapi.json` | **Non-production only** (disabled when `APP_ENVIRONMENT=production`) |

> The example `widgets` resource uses an **in-memory** repository — state is per
> process and lost on restart, and not shared across replicas. Replace
> `WidgetRepository` with a real datastore before relying on it.

Errors are returned as RFC 9457 `application/problem+json`
(`type`, `title`, `status`, `detail`, `instance`).

## Configuration / environment variables

All config is read once at startup via `get_settings()` (pydantic-settings),
prefixed `APP_`, case-insensitive. Never read `os.environ` ad hoc. See
`.env.example`.

| Variable                          | Default                  | Notes                                                  |
| --------------------------------- | ------------------------ | ------------------------------------------------------ |
| `APP_SERVICE_NAME`                | `template-backend-python`| Logical name in logs/traces.                           |
| `APP_ENVIRONMENT`                 | `local`                  | `local` / `dev` / `staging` / `production`. Drives docs exposure and HSTS. |
| `APP_HOST`                        | `0.0.0.0`                | Bind address (container default; `127.0.0.1` locally). |
| `APP_PORT`                        | `8000`                   | Bind port (1–65535).                                   |
| `APP_ROOT_PATH`                   | _empty_                  | ASGI `root_path` when behind a path-prefixing proxy.   |
| `APP_LOG_LEVEL`                   | `INFO`                   | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`.           |
| `APP_LOG_JSON`                    | `true`                   | JSON logs (prod) vs console (local).                   |
| `APP_OTEL_ENABLED`                | `false`                  | Enable OTLP tracing (requires the `otel` extra).       |
| `APP_OTEL_EXPORTER_OTLP_ENDPOINT` | _none_                   | e.g. `http://collector:4317`.                          |
| `APP_REQUEST_TIMEOUT_SECONDS`     | `10`                     | Default outbound httpx timeout (> 0).                  |
| `APP_CORS_ALLOW_ORIGINS`          | _empty_                  | Comma-separated origins; empty disables CORS.          |

Changing config requires a restart (settings are frozen and cached for the
process lifetime).

## Run / build

```bash
# Local (hot reload)
task run                 # uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Container
task build               # docker build -t ghcr.io/aircloud/template-backend-python:local
task run-container        # runs --read-only --cap-drop ALL on :8000
```

Production entrypoint (baked into the image):
`python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.

## Observability

- **Logs** — structlog JSON on stdout; ship via the platform log pipeline.
  Every line for a request carries `request_id`, `method`, `path`. Correlate an
  incident by the `request_id` (also returned in the `X-Request-ID` response
  header). Raise verbosity temporarily with `APP_LOG_LEVEL=DEBUG` (requires
  restart).
- **Tracing** — set `APP_OTEL_ENABLED=true` + `APP_OTEL_EXPORTER_OTLP_ENDPOINT`
  and deploy the `otel` extra. Health probes are excluded from traces. A bad
  endpoint logs `telemetry.dependencies_missing` / a warning and the app keeps
  serving.
- **Key startup events**: `app.startup` (service, environment, version),
  `app.shutdown`, `telemetry.enabled` / `telemetry.disabled`.

## Common incidents

### Readiness flapping (`/health/ready` → 503)

1. Check logs for `request.unhandled_error` or dependency errors around the
   readiness handler.
2. Identify the failing entry in the `checks` map (DB/cache/upstream).
3. If a dependency is down, the 503 is correct (traffic drains). Restore the
   dependency; readiness recovers automatically. Do **not** mask the check.

### Pod restart loop (liveness failing)

1. `/health/live` is dependency-free, so a failure means the process can't
   serve — inspect stdout for a startup crash (often invalid config raising in
   `Settings`/`get_settings()`).
2. Validate env vars against the table above; fix and redeploy.
3. Check the container `HEALTHCHECK` timing if startup is genuinely slow
   (`--start-period`).

### Elevated 5xx

1. Filter logs for `request.unhandled_error` (full `exc_info`) and group by
   `path`. Clients see a generic `500` problem+json; the cause is server-side.
2. Filter `request.domain_error` for expected 4xx (`NotFoundError`,
   `ConflictError`) — usually client-driven, not an outage.
3. If a recent deploy correlates, **roll back** (below).

### High latency / upstream slowness

1. Check `APP_REQUEST_TIMEOUT_SECONDS`; outbound httpx calls time out at this
   bound.
2. With tracing on, inspect spans for the slow upstream. Scale replicas if the
   service itself is saturated (CPU-bound, 1 worker/container).

### CORS errors from a browser client

1. Confirm the origin is in `APP_CORS_ALLOW_ORIGINS` (comma-separated). Empty
   disables CORS entirely.
2. Update the env var and restart.

### Config rejected at startup

`Settings` validation (pydantic) raises on invalid values (e.g. bad
`APP_PORT`, unknown `APP_ENVIRONMENT`). The process exits immediately — read the
validation error in stdout, correct the env, redeploy.

## Rollback

Images are immutable, signed (keyless cosign), and carry SLSA provenance, so
rolling back is redeploying a previous good tag/digest.

1. Identify the last-good image tag/digest (release-please tags `vX.Y.Z`; see
   the registry / deployment history).
2. (Optional) Verify the signature before promoting:

   ```bash
   cosign verify ghcr.io/aircloud/template-backend-python:<tag> \
     --certificate-identity-regexp '^https://github.com/aircloud/template-backend-python/.github/workflows/.+' \
     --certificate-oidc-issuer https://token.actions.githubusercontent.com
   ```

3. Update the deployment to the previous tag/digest and roll out. Health probes
   gate the rollout: readiness must report `ready` before traffic shifts.
4. Confirm recovery: `/health/ready` is `200`, 5xx rate normal, no
   `request.unhandled_error` spikes.
5. Open an incident note; revert the offending change via a new PR (don't leave
   `main` ahead of what's deployed).

> No config rollback step is usually needed since config is external env, but if
> a config change caused the incident, revert the env var change in the same
> action.

## Related

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — app assembly, request, and
  observability diagrams.
- [`../README.md`](../README.md) — quick start, CI/CD, customising.
- [`../SECURITY.md`](../SECURITY.md) — vulnerability reporting.
