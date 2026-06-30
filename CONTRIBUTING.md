# Contributing

Thanks for contributing to `template-backend-python`. This guide covers the
local workflow, commit conventions, and the quality bar enforced in CI.

## Code of Conduct

This project is governed by our [Code of Conduct](./CODE_OF_CONDUCT.md). By
participating you agree to uphold it.

## Getting started

Prerequisites: [`uv`](https://docs.astral.sh/uv/),
[`Task`](https://taskfile.dev/), Docker (for container work). A
[dev container](./.devcontainer/devcontainer.json) is provided with everything
preinstalled.

```bash
task setup   # uv sync --frozen --all-groups + install pre-commit hooks
task run     # start the service locally
```

## Branching & workflow

1. Create a topic branch from `main` (e.g. `feat/widgets-bulk-create`).
   Direct pushes to `main` are blocked by the ruleset.
2. Make focused changes; keep PRs small and reviewable.
3. Ensure the full local gate passes: `task all`.
4. Open a PR. CI must be green and CODEOWNERS must approve (2 reviews).

## Conventional Commits

Every commit **and** PR title must follow
[Conventional Commits](https://www.conventionalcommits.org/). The PR title
becomes the squash-merge commit and drives **release-please**.

```
feat(widgets): add bulk create endpoint
fix(health): return 503 when a dependency is down
docs: clarify OTel configuration
deps: bump fastapi to 0.115.4
```

Common types: `feat`, `fix`, `perf`, `docs`, `refactor`, `test`, `build`, `ci`,
`chore`, `deps`. Breaking changes use `!` (e.g. `feat!:`) or a
`BREAKING CHANGE:` footer.

The `conventional-pre-commit` hook validates commit messages locally.

## Signed (verified) commits — required

All commits to `main` must be **signed and show as "Verified"** on GitHub.
SSH signing is the simplest:

```bash
# Generate a signing key (or reuse an existing SSH key)
ssh-keygen -t ed25519 -C "you@aircloud.com.pl" -f ~/.ssh/id_ed25519_sign

# Configure git to sign with it
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519_sign.pub
git config --global commit.gpgsign true

# Add the *public* key to GitHub as a "Signing Key"
#   GitHub → Settings → SSH and GPG keys → New SSH key → type: Signing Key
```

GPG signing is also supported (`git config gpg.format openpgp`). Unsigned commits
are rejected by the branch ruleset.

## Quality gate (matches CI)

| Step          | Command             | Tool                |
| ------------- | ------------------- | ------------------- |
| Lint          | `task lint`         | ruff                |
| Format check  | `task format-check` | ruff format         |
| Type check    | `task typecheck`    | mypy (strict)       |
| Tests         | `task test`         | pytest + coverage   |
| Security      | `task security`     | bandit + pip-audit  |
| Everything    | `task all`          | all of the above    |

The coverage gate is `--cov-fail-under=85`; do not lower it to pass CI.

## Tests

- Unit tests in `tests/unit/`, integration tests in `tests/integration/`.
- Integration tests use the async `client` fixture (`tests/conftest.py`) wired to
  the in-process ASGI app — no network required.
- New endpoints require both unit and integration coverage.

## Dependencies

- Managed by uv. To add a dependency: edit `pyproject.toml`, then run
  `uv lock` and commit the updated `uv.lock`. **Never hand-edit `uv.lock`.**
- Dev tools go in the `dev` dependency group.

## Reporting security issues

Do **not** open a public issue for vulnerabilities. Follow
[`SECURITY.md`](./SECURITY.md).
