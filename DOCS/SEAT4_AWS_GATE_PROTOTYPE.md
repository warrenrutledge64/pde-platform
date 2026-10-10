# Troikauge 3.0 — Issue #81 AWS External Authorization Gate (Option B)
**Status: proposed credential-free prototype ONLY. Do not deploy, provision secrets, or enable release.**

## Approved platform decision
Human chose AWS Lambda, AWS Secrets Manager, AWS KMS for an externally controlled authorization service while retaining the private `troikauge-seat4-private` repository. The existing `seat4-production` GitHub environment and `main` branch protections are not enforced and must never be trusted to hold credentials or mint privileged tokens. PR #87 stays draft/unmerged.

## Proposed AWS control plane (not provisioned)
- API Gateway: optional authenticated request ingress with strict size/schema limits, throttling and WAF where appropriate; not an authority provider.
- Lambda: validate immutable request, approved purpose, source classification, repository, audience, context, SHA, nonce, and expiry; challenge independent Human approval. Secure Lambda deployment through separate Human-owned AWS account/principal, not a GitHub Actions role.
- Human approval: use a separate identity provider with MFA and verified issuer/audience/subject, operation-specific consent bound to full canonical request digest and short expiry. An ordinary GitHub issue comment, PR approval, or chat affirmation never replaces independently verified approval. Protected GitHub review events may serve as additional evidence once authenticated and scoped to a specific action.
- DynamoDB: use **conditional writes** for one-time approval/nonce consumption and request state transitions; TTL is for cleanup only, **not** replay protection or instantaneous expiry enforcement.
- Secrets Manager: hold GitHub App private key, but **no secret is to be created or populated until independent IAM and Human controls are tested**.
- KMS: protect secret/key use with explicit key policies and separate gate-execution role; encryption alone does not constrain an overprivileged caller.
- CloudTrail and immutable/locked log destination as feasible: independently retained event receipts; never log raw sensitive assessments, credentials or full payloads.
- GitHub App: initially **Contents read-only**, single selected private repository. Gate executes scoped read-only GitHub operations server-side using short-lived installation token. Never return the App key or installation token to GitHub Actions.
- GitHub Actions: untrusted requester, read-only `GITHUB_TOKEN`, no AWS deployment permissions, no App credentials and no private assessment material. Do not treat workflow `actor` or environment status as Human approval.

## Two-party release protocol
1. Request is canonicalized, cryptographically digested and validated. Reject unknown fields, unrecognized operation, wrong audience, source, target SHA, and expired request.
2. Gate authenticates request origin; demands independently authenticated Human consent tied to request digest and intended destination. No approved Human identity/authenticator selected yet.
3. After approval, perform second pre-execution content/scope/revision check; atomically consume approval and replay nonce; deny on mismatch or reuse.
4. Gate gets short-lived installation token **internally**, checks actual repo permissions, executes only predefined allowlisted operation, and returns a non-secret receipt.
5. Independently retain evidence including verified Human principal, consent event, SHA and digest, token App installation identity, execution event and outcome. No credentials in receipt.
6. Fail closed when identity provider, approval, ledger, GitHub, clock, or audit sink is unavailable. No fallback to GitHub Actions self-approval.

## Offline artifact
- `scripts/seat4_aws_gate.py` validates a narrow *syntactic* v0 read-boundary-check request and returns 403 even when structurally valid.
- `scripts/test_seat4_aws_gate.py` exercises 15 schema/negative/denial cases.
- Run: `python3 -m unittest discover -s scripts -p test_seat4_aws_gate.py`.
- This prototype does NOT verify callers, signatures, MFA, approval receipts, JWT claims, GitHub installation tokens, repository access, actual expiry, replay state, source contents or log retention. A digest is NOT authentication. **No real request may be authorized on the basis of passing tests.**

## Human prerequisites
1. Select AWS account/project custody distinct from production-seat automation; record administrators and AWS region.
2. Select independent Human identity provider/MFA and authentication transport; require explicit consent bound to canonical request hash.
3. Approve an IAM and KMS policy that prevents repository editors, CI principals and production-seat identities from reading secrets or deploying new Lambda code/policy.
4. Select independent immutable audit retention and a break-glass/credential rotation policy.
5. Review integration with Issue #80, including sanitized packets, classification rules and active Validator context segregation.
6. Only after negative tests demonstrate actual controls may the Human separately authorize credential provisioning, scope expansion or release activation.

## Testing and evidence
Test production-seat principals, existing Codex Connector, a real read-only Seat 4 installation token, IAM explicit deny, cross-account assume-role denial, replayed approvals, changed SHA/digest, wrong recipient, expired approval, disabled audit sink and Lambda code tampering. Store detailed security results in the **private** repository or external audit store, never accessible PDE. Issue #81 remains blocked until authentic access and approval controls are verified.
