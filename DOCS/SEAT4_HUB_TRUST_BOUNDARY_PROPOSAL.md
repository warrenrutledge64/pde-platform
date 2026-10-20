# Troikauge 3.0 Issue #81 — Pipeline-Hub trust boundary proposal

**STATUS: DRAFT DESIGN ONLY.** No AWS access, IAM changes, deployments, secrets, release authorization, governance ratification or merge have occurred. PR #87 must remain open/draft/unmerged until its tests and dependencies are verified and Human separately authorizes the change.

## Human-supplied topology (authoritative project context)
- **Pipeline-Hub (641628980935):** ZTIE brains/control plane, orchestration, DynamoDB tracking, dashboard, Human accept/reject gate; receives only derived/sanitized material through Hub-owned data-contract gate and NEVER stores/receives/executes raw untrusted payloads. PDE control plane too, with reporting/tracking and `pdlv-` namespaced orchestration, CodeBuild, promotion and manual-approval Step Functions.
- **Pipeline-Forensics (360999005254):** ZTIE self-contained blast-radius containment; intake/preprocessing/scanners, endpoint-only isolated VPC, ephemeral EC2 host-native SSM detonation, no durable store. Not a PDE account. Forensics is controlled by Hub, so not independent administrative authority.
- **Pipeline-Sandbox (586917955591):** ZTIE→PDE Human-ACCEPT and hash-verified one-way Forensics→Sandbox handoff; then PDE member/ownership begins.
- **Pipeline-Dev (946509368326), Pipeline-Prod (466494951534):** PDE members only; no direct ZTIE role.
- **Management (467866449172):** zero-touch; outside this five-account service topology. Do not place Seat 4 resources in Management.

## Candidate Seat 4 deployment
Propose AWS `us-east-1`, Pipeline-Hub account, with an independent `seat4-` namespace for a Lambda authorization gate, future Secrets Manager + KMS custody, DynamoDB one-time authorization/replay ledger, and independent audit. This is **a candidate location**, not approval to deploy. The gate must not ingest raw ZTIE payloads or assume access to Forensics, Sandbox, Dev, or Prod.

### Control plane collision risk
Hub already controls ZTIE and PDE orchestration. Merely adding `seat4-` prefixes or IAM roles does NOT isolate Seat 4 from existing Hub account admins, CI deployers, `pdlv-` operators, ZTIE orchestrator, incident-response roles, IAM policy editors, Lambda update identities, KMS administrators, or CloudTrail administrators. All effective privilege-escalation chains must be inventoried before claiming a separate gate. If these rights are inseparable, stop and reconsider an external account/authority despite the current preference for existing-account deployment.

### Proposed least privilege (not applied)
- Human security owner: separately authenticated MFA principal with authority over gate approval policy and changes; verify who can impersonate/control that principal.
- Gate runtime: exact allowlisted read-only private GitHub operation at first, never a free-form API proxy; deny IAM mutation, secret/resource policy alteration, CI deployment, audit deletion, KMS grant creation, and approval forgery.
- Gate deployer: separately Human-approved, cannot issue or consume its own Human approvals, and cannot modify protected audit retention.
- GitHub Actions: untrusted request-originator only; no AWS secrets, App key/token, direct privileged IAM trust, gate deployment privilege, or production-seat private data.
- Kiro/Gemini/Copilot and their actual tool identities: deny private Seat 4 repository and AWS gate controls. Test live actor credentials, not just proposed policy.
- Other Hub workflows: `pdlv-`, ZTIE scanner/orchestrator and shared CI cannot edit gate policy, Lambda code, secrets, key policy, ledger, or approvals.

## Gate constraints
- External Human MFA approval must bind to immutable request digest, purpose, operation, source hash, target commit SHA, recipient, repository, nonce and expiry.
- Gate owns short-lived `Troikauge-Seat4` GitHub App token internally and never returns key/token to Actions or other production seats.
- DynamoDB conditional consumption for nonces/approvals; TTL not sufficient for replay or expiry.
- Independent durable audit: receipt must survive repo history rewrite and unauthorized workflow execution.
- Deny on uncertainty, unsupported enforcement, changed content or unavailable audit/identity controls.
- Existing private personal GitHub repository branch protection is observed **not enforced**; `seat4-production` GitHub environment is not a secret custody gate.

## Isolation invariants
1. **ZTIE raw payload never enters Hub**, including Seat 4 logs, analytics, Lambda events or authorization requests.
2. **Forensics→Sandbox** remains only the Human-ACCEPT/hash-verified ownership handoff; Seat 4 does not modify it.
3. No production-seat raw evaluations/provenance enter live Gemini Validator context or readable production-seat repos.
4. Hub's existing Human accept/reject gate for ZTIE is **not equivalent** to a Troikauge Seat 4 approval. Must separately verify Human actor, transaction scope, and context.
5. Human alone ratifies Troikauge methodology, releases, and merges; ChatGPT may draft only as authorized.

## Required independent evidence
Account-context STS identity; IAM role and permission boundary inventory; trust policies; explicit policies and admin escalation; KMS grants/key policies; Lambda deployment mutation grants; Secrets Manager policies; GitHub OIDC/CI identities; `pdlv-` and ZTIE orchestrator identity control; DynamoDB table write/admin access; CloudTrail and log retention alteration rights; proof of denial for each production-seat principal; independent Human MFA event validation and audit survival.

**STOP** if any shared Hub automation or production-seat identity can bypass Human approval, update Lambda policy/code, read App keys, rewrite approval ledger, or delete audit without independent Human control. Do not proceed to secrets/release.
