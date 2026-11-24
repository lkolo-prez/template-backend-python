# syntax=docker/dockerfile:1.10
# ---------------------------------------------------------------------------
# Multi-stage build:
#   1) builder  – uv resolves & installs the locked venv (no dev deps).
#   2) runtime  – distroless nonroot image carrying only the venv + source.
# The final image runs as a non-root user, is read-only-rootfs friendly, and
# carries a HEALTHCHECK. hadolint-clean.
# ---------------------------------------------------------------------------

# Pin the uv tooling image to a digest in production; tag shown for clarity.
ARG UV_VERSION=0.13.9
ARG PYTHON_VERSION=3.12

# --------------------------------------------------------------------------- #
# Stage 1: builder                                                            #
# --------------------------------------------------------------------------- #
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM debian:bookworm-slim AS builder
ARG PYTHON_VERSION

# uv configuration: copy mode (works across the layer boundary into runtime),
# compile bytecode for faster cold starts, and a uv-managed (standalone) CPython
# installed under /opt/python. The distroless python3-debian12 image ships
# Python 3.11, so the interpreter travels with the venv instead.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_PREFERENCE=only-managed \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PYTHON=${PYTHON_VERSION} \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=uv /uv /usr/local/bin/uv
# The runtime never installs packages, so drop the interpreter's bundled pip
# (its vendored SBOM otherwise surfaces stale CVEs in image scans).
RUN uv python install "${PYTHON_VERSION}" \
    && rm -rf /opt/python/cpython-*/lib/python*/site-packages/pip \
              /opt/python/cpython-*/lib/python*/site-packages/pip-*.dist-info

WORKDIR /app

# Install dependencies first (cached) using only the lock + project metadata.
# --no-install-project keeps this layer independent of source changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Now add the source and install the project itself into the venv.
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# --------------------------------------------------------------------------- #
# Stage 2: runtime (distroless, non-root)                                     #
# --------------------------------------------------------------------------- #
# cc (glibc + libgcc) is what the uv-managed CPython needs; debian13 tracks
# current OpenSSL fixes (debian12's libssl3 lags behind in distroless).
FROM gcr.io/distroless/cc-debian13:nonroot AS runtime

# OCI labels for provenance & discoverability.
LABEL org.opencontainers.image.title="template-backend-python" \
      org.opencontainers.image.description="aircloud FastAPI microservice template" \
      org.opencontainers.image.source="https://github.com/aircloud/template-backend-python" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.vendor="aircloud"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

WORKDIR /app

# Copy the fully-built virtualenv and the application source.
COPY --from=builder /opt/python /opt/python
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src

# The distroless :nonroot tag already runs as uid 65532. Make it explicit.
USER 65532:65532

EXPOSE 8000

# Liveness probe baked into the image. Uses the venv python (no curl/wget in
# distroless). Fails the container if the liveness endpoint is unhealthy.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status==200 else 1)"]

# uvicorn is the ASGI server; a single worker per container is the cloud-native
# default (scale horizontally via replicas). PYTHONPATH points at /app/src.
ENV PYTHONPATH=/app/src
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
