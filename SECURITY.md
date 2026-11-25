# Security Policy

We take the security of `template-backend-python` seriously. Thank you for
helping keep it and its users safe.

## Supported versions

| Version            | Supported          |
| ------------------ | ------------------ |
| Latest `main`      | :white_check_mark: |
| Latest release tag | :white_check_mark: |
| Older releases     | :x:                |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Report privately via **GitHub Security Advisories**:

> <https://github.com/lkolo-prez/template-backend-python/security/advisories/new>

If you cannot use GitHub advisories, email **office@aircloud.com.pl** with the
subject `SECURITY: template-backend-python` and, if possible, encrypt sensitive
details using the key referenced in our [`security.txt`](#securitytxt).

Please include:

- A description of the issue and its impact.
- Steps to reproduce (a minimal PoC, request, or failing test is ideal).
- Affected version / commit SHA and environment.
- Any suggested remediation.

## Our commitment (SLA)

| Stage                         | Target                          |
| ----------------------------- | ------------------------------- |
| Acknowledge receipt           | within **2 business days**      |
| Initial triage & severity     | within **5 business days**      |
| Fix or mitigation for Critical| within **14 days** of triage    |
| Fix for High                  | within **30 days** of triage    |
| Coordinated public disclosure | by mutual agreement after a fix |

We follow **coordinated disclosure**. We will keep you updated on progress and
credit you in the advisory unless you prefer to remain anonymous.

## Safe harbor

We will not pursue or support legal action against researchers who:

- Act in good faith and avoid privacy violations, data destruction, and service
  degradation.
- Do not access or modify data that is not their own.
- Give us reasonable time to remediate before public disclosure.

## Scope

In scope: this repository's source, container image, and CI/CD configuration.
Out of scope: third-party dependencies (report upstream), and infrastructure not
owned by this repository.

## security.txt

Our machine-readable security contact follows
[RFC 9116](https://www.rfc-editor.org/rfc/rfc9116) and is published at:

> <https://aircloud.com.pl/.well-known/security.txt>

That file is the canonical source for the current security contact, encryption
key, and policy URL.
