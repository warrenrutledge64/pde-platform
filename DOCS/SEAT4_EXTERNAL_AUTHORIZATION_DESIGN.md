# Troikauge 3.0 — Issue #81 Option B: External Human Authorization Gate

**Status: design proposal only; not an active security control.** Human decision: retain private `warrenrutledge64/troikauge-seat4-private` repository; use an external Human authorization gate. PR #87 must stay draft; do not provision production secrets before controls are independently verified.

## Why
Private personal repository branch protection is shown by GitHub as **not enforced**. Therefore `seat4-production` / `Protected branches only` does not establish protected execution. A GitHub Actions job must never receive the GitHub App private key, an installation token, approval signing key or privileged cloud credentials under this arrangement. A proposed approval field or a GitHub comment alone does not constitute Human authorization.

## Trust boundaries
1. Human: authorizes scoped operations through a separately authenticated channel using strong MFA; no self-approval by automation. Human alone ratifies governance, releases, and merges.
2. External gate (independent cloud service): holds the `Troikauge-Seat4` private key in managed secret storage/KMS inaccessible to GitHub Actions and production-seat credentials. Verifies Human identity, consent, and exact requested action against an allowlist. Mints short-lived installation tokens internally and executes limited GitHub API calls server-side; **does not return credentials or broad write tokens to the caller**.
3. Private repository: stores sensitive Seat 4 records with separate access control. Existing Codex Connector installation excludes it. This restriction is not proof against all OAuth or production-seat credentials.
4. GitHub Actions: **untrusted request initiator** only. Its `GITHUB_TOKEN` stays read-only and no privilege-bearing secrets are attached. Actions status does not authorize release.
5. Production seats: never read raw assessments, provenance keys, internal synthesis, or Human approval evidence; only sanitized, authorized audience-specific release packets go to an approved channel. Active Gemini Validator contexts never receive retrospective inputs.

## Recommended hosting
Use a small managed cloud service with protected secret storage, service identity, tamper-evident/independently retained audit logs and external Human identity verification. GCP Cloud Run + Secret Manager + Cloud KMS + Cloud Audit Logs **or** AWS Lambda + Secrets Manager + KMS + CloudTrail are candidates, **not chosen or provisioned**. Ensure an automation-controlled repository or GitHub Actions cannot modify the service, its authorization policy, secret ACL, or deployment. The Human must control gate administration from a separate principal.

## Request and authorization protocol
1. GitHub Actions may submit a **non-sensitive** request for one predefined operation. Include unique `request_id`, immutable target commit SHA, repository ID, operation, purpose, recipient/context, payload digest, source references/hashes, issue/cycle ID, expires_at and nonce. No private raw payloads in workflow logs.
2. Gate authenticates the caller, validates audience, explicit operation allowlist, exact target repo, immutable requested refs, expiry, nonce/replay ledger, expected source classification, and idempotency.
3. Human authenticates **directly to the gate** using a separate identity and MFA, reviews precise operation, destination and content digest, and approves or rejects. A GitHub PR review may be retained as additional evidence only if independently verified against GitHub's authenticated event API and explicitly bound to the same request. Do not rely on a self-entered `verified_human` flag or mutable markdown.
4. Gate re-checks unchanged request content and scope after approval; approvals are one-time, time-limited and never portable across SHA, recipient, repository or payload.
5. Gate executes exactly the approved GitHub API operation using short-lived App installation credentials internally. It never exposes keys/tokens to GitHub Actions, ChatGPT or production seats.
6. Gate writes an audit receipt independently of GitHub (request digest, actor verified ID, approval event ID, execution identity, API response, timestamp and immutable SHA). Return only status/receipt identifier to workflow.
7. On any failure: deny with generic error and record reasons privately. Never fall back to GitHub environment approval alone or human-readable chat approval.

## GitHub App evolution
Currently `Troikauge-Seat4` is configured for Contents read-only on the selected private repository. Preserve that permission. Initial gate proof should attempt only read-only metadata/content operations. Any write action requires a separate Human-approved minimal App permission amendment and installation re-approval; verify actual expanded permissions, without granting repository administration or workflow modification by default.

## Non-negotiable tests
- Existing ChatGPT Codex Connector denied private repository API content; review effective access after configuration changes.
- Gemini/Kiro/Copilot **actual principals** denied clone, read, write and token use, including via inherited Apps.
- Invalid caller, spoofed Human, replay, stale approval, modified payload, wrong target SHA, wrong recipient, unknown purpose, expired authorization all denied.
- Actions job cannot access gate private key, installation token, or deploy new gate policy.
- Gate cannot execute unapproved write; audit event remains independently retained even when repository history changes.
- Failure and rollback do not promote draft PR #87, change statuses to Done, or authorize packets.
- Issue #80 12 tests executed and independent moderator + Validator gates recorded before any activation.

## Rollout stages
A. Review/ratify this architecture as a design. B. Choose cloud host and independent Human identity provider; document owner, budget, IAM and log retention. C. Build a read-only gate prototype with mock credentials and contract/negative tests. D. Human provisions separate cloud project/account and managed secrets only after policies and deployment controls are verified. E. Conduct independent seat-denial and adversarial authorization tests; obtain explicit Human approval for carefully scoped write operations. F. Integrate Issue #80; do not enable production transfer until release-specific ratification.

## Current status
No external gate exists yet; no credentials, environments with effective mandatory review, or private records were created by this proposal. `seat4-production` environment exists but **is not a security boundary** under observed unenforced rules. PR #87 remains draft/unmerged by Human instruction.
