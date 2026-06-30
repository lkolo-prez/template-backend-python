# Branch protection (GitHub Rulesets)

`main` is protected by a GitHub **Ruleset** (the modern replacement for classic branch
protection). Configure it under **Settings → Rules → Rulesets → New branch ruleset**, or
apply it as code with the GitHub API / Terraform. These settings are required for the repo to
score well on OpenSSF Scorecard and to keep the supply chain trustworthy.

## Target

- **Ruleset name**: `protect-main`
- **Enforcement status**: Active
- **Target branches**: include the default branch (`main`).
- **Bypass list**: empty (no roles or apps bypass — not even admins).

## Required rules

| Rule | Setting |
| --- | --- |
| Restrict deletions | ✅ on |
| Restrict force pushes (non-fast-forward) | ✅ on |
| Require linear history | ✅ on |
| Require signed commits | ✅ on |
| Require a pull request before merging | ✅ on |
| — Required approvals | **2** |
| — Dismiss stale approvals on new commits | ✅ on |
| — Require review from Code Owners | ✅ on (see [`.github/CODEOWNERS`](../.github/CODEOWNERS)) |
| — Require approval of the most recent push | ✅ on |
| — Require conversation resolution before merging | ✅ on |
| Require status checks to pass | ✅ on |
| — Require branches to be up to date before merging | ✅ on |
| Block force pushes | ✅ on |

## Required status checks

Add these checks (the job `name:` values from the workflows) as **required**:

- `Lint, type-check, test` — from [`ci.yml`](../.github/workflows/ci.yml)
- `SAST and dependency audit` — from [`ci.yml`](../.github/workflows/ci.yml)
- `Analyze (python)` — from [`codeql.yml`](../.github/workflows/codeql.yml)
- `Build, scan, sign, attest` — from [`container.yml`](../.github/workflows/container.yml)
- `Review dependency changes` — from [`dependency-review.yml`](../.github/workflows/dependency-review.yml)
- `Semgrep SAST` — from [`semgrep.yml`](../.github/workflows/semgrep.yml)
- `Scorecard analysis` — from [`scorecard.yml`](../.github/workflows/scorecard.yml)

> Status-check names must match the job `name:` exactly. If you rename a job, update the
> ruleset. A new required check only takes effect after it has reported at least once.

## Signed commits

Verified commits are required. Contributors configure signing once (SSH signing is simplest):

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
# Add the key under GitHub → Settings → SSH and GPG keys → "Signing Key".
```

## Tag protection

Protect release tags (`v*`) with a separate **tag ruleset**: restrict creation/deletion to the
release automation and require signed tags. `release-please` creates the tags from `main`, so the
same identity/signing rules apply.

## Apply as code (optional)

Apply the ruleset with the GitHub CLI so it is reproducible:

```bash
gh api -X POST repos/aircloud/template-backend-python/rulesets \
  --input .github/rulesets/protect-main.json
```

or manage it with the `integrations/github` Terraform provider
(`github_repository_ruleset`). Keep the JSON/HCL in version control and review changes like any
other code.
