# Troikauge Issue #81 — Protected GitHub Actions Execution Plan
Status: PROPOSAL ONLY. Not deployed, not ratified, not verified.

## Human decisions
- Private records: separate private repo, `warrenrutledge64/troikauge-seat4-private`.
- Dedicated execution identity: `Troikauge-Seat4` GitHub App.
- Authorization evidence: authenticated protected GitHub approval/review event.
- Execution platform: GitHub Actions using protected environments.
- Do not merge or activate PR #87 until tests AND dependencies verified.

## Observed access boundary
ChatGPT Codex Connector was switched from 'All repositories' to selected working repositories, excluding Seat 4 private. Subsequent read attempt from this connection returned 404. This demonstrates only this one connection's current inability to retrieve it, NOT comprehensive Gemini/Kiro/Copilot denial tests, and NOT dedicated App authentication.

## Separation requirements
- GitHub Actions YAML and private approval receipts belong inside `troikauge-seat4-private`, never in production-seat-readable PDE.
- Do not grant existing Codex Connector private repo access merely to populate the repository. Human may create private workflow files via protected GitHub UI or a separately authenticated and audited Seat 4 service once available.
- A GitHub App installation with read-only Contents cannot write records or push branches. Any later write privilege requires a narrow, independently reviewed escalation and test; avoid Administration/Workflows unless a demonstrated requirement.
- Actions `GITHUB_TOKEN` is distinct from the GitHub App installation token. Restrict default token to `contents: read`. Explicitly allow only necessary operations per job.
- Place secrets in GitHub Actions environment secrets, restricted by verified approvals. Never place PEMs or installation tokens in repository, issue, PR, chat, logs or artifacts.
- Treat GitHub-hosted runners as code execution with potential secret exfiltration. Never execute untrusted PR heads with elevated permissions/secrets; pin third-party Actions to immutable commit SHAs; prevent injection from user-controlled event fields.

## Required environments
1. `seat4-staging`: no secrets, used for structural checks and dry-run evidence. No private payload uploads.
2. `seat4-production`: only when available/verified under the account's private-repository plan; requires Human review by a specifically authorized reviewer, prevention of self-review where available, controlled deployment branch/tag allowlist, and an independent approval ledger. If required reviewer protections are unsupported, DO NOT store App credentials or issue production tokens; use an external protection mechanism selected by Human.

## Workflow phases (future private repo)
1. Human requests a specific execution with pinned commit SHA, nonce, purpose, recipient and expiry. Avoid free-form untrusted script path or command.
2. Preflight checks validate source record classification, runner ref, allowed actor, file manifest and source hash; all invalid fields fail closed.
3. Environment gate obtains Human approval before secrets are exposed; check available GitHub plan enforcement. Environments alone do not guarantee reviewers.
4. Auth job exchanges App ID and securely scoped private key for a short-lived installation token restricted to the selected private repository. Do not request a user token.
5. Verify token identity/scopes and repository selection against allowlist; do not confuse workflow actor with App actor. Never print tokens.
6. Execute only pre-approved deterministic operations; prohibit release of cross-eval packets until Issue #80 integration, proof and separate Human activation.
7. Emit scrubbed execution receipt: workflow run URL, run attempt, approver event URL/ID, target SHA, app identity, recipient/scope and digest; independently retain append-only audit material.
8. Destroy token on completion; avoid persistence in caches or artifacts.

## Approval architecture warning
A deployment reviewer approving a GitHub Actions environment is not automatically an independently protected GitHub PR review, and a PR review is not necessarily authorization for a different workflow run. Define explicit correspondence and validate Human actor, run/commit scope, freshness, and non-self-approval. A mutable YAML boolean or markdown approval marker is insufficient. Require Human-driven authorization for release separately from code approval.

## Test gates
- [ ] Available GitHub plan actually supports environment required reviewers for this private repo.
- [ ] Branch/ruleset or equivalent protects workflow definitions from automation edits and Human-approval bypass.
- [ ] Codex Connector cannot read private repository after saved settings; record 404 as scoped evidence.
- [ ] Each real production seat principal denied clone, API read, write, PR/issue and Actions where applicable.
- [ ] Dedicated App token can read exactly its private repo and cannot access PDE, SDD-repo-kit, BOM, ZTIE-Issues.
- [ ] Unapproved run cannot access production environment secrets.
- [ ] Actor impersonation, stale approval, changed commit, replay, wrong audience and untrusted payload tests deny.
- [ ] Retention and audit replay tests verified independently.
- [ ] Issue #80 offline checker and negative tests executed in a trusted environment.
- [ ] Human ratification recorded with authentic protected evidence; distinct merge/release authorization obtained.

## Current stop condition
No credentials generated; no private workflow or environment created by this PR; no production packets authorized. PR #87 remains draft and unmerged.
