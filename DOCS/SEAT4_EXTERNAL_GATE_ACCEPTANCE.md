# Issue #81 Option B — Execution checklist and acceptance evidence

State: **BLOCKED pending independent authorization service**.

## Phase 0 — Safe now
- [x] Human selected Option B: private repository retained; external Human authorization gate.
- [x] Document why current private repo branch protection and environment controls are not enforced.
- [ ] Human selects externally hosted gate platform and independent identity/MFA option.
- [ ] Identify exact authorized Human principal and recovery procedure; do not publish secrets.
- [ ] Approve gate service trust model and costs before provisioning.

## Phase 1 — Build without credentials
- [ ] Define versioned request/approval/receipt JSON schemas; reject unknown fields.
- [ ] Implement gate allowlist, digest binding, expiry, nonce ledger, idempotency and failure auditing.
- [ ] Mock GitHub App token service; write adversarial negative tests.
- [ ] Isolate API and build pipeline from all GitHub Actions workflow editors.
- [ ] Require Human-approved gate policy changes and independent logs.

## Phase 2 — Configure and test
- [ ] Human configures an independent cloud project/account and security principal with MFA.
- [ ] Protect gate deployment and managed secret access from CI/repository writers.
- [ ] Prove request initiator cannot read secret or alter authorization policy.
- [ ] Verify `Troikauge-Seat4` App read-only, single-private-repo installation via authenticated App-token inspection.
- [ ] Denial tests executed for every identified Gemini, Kiro and Copilot principal; record actor IDs and API results privately.
- [ ] Test Human approval live with a **read-only** harmless request; record receipt.
- [ ] Independently attest audit log retention/alerting.

## Phase 3 — Any future release
- [ ] No privileged token ever returned to Actions or production seats.
- [ ] No unreviewed broad App permissions or production secret stored in `seat4-production`.
- [ ] Scope-bound Human approval and explicit source/content hashes.
- [ ] Cross-eval private material and redaction reviews complete.
- [ ] PR #87 tests verified, Issue #80 and #81 dependencies independently evidenced, and Human separately authorizes merge/activation.

## Human input needed
Select **Google Cloud** or **AWS** (or specify another trusted independent host) for the external gate. A separate identity provider / MFA decision follows. No need to disclose keys, passwords, personal identity factors or secrets here.

## Evidence record (not yet populated)
Gate endpoint / cloud project ref: TBD; IAM policy evidence: TBD; Human approval event references: TBD; test reports: TBD; verified production seat principals: TBD; App installation token and repository permission proof: TBD; Human ratification: TBD.
