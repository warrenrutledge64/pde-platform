# Troikauge 3.0 / Issue #81 — Existing AWS Account Isolation Plan

**Status: unimplemented design, no secrets or deployment.** Human selected an existing AWS account with strictly isolated IAM for the external Seat 4 authorization gate. Prior designs: PRs #90–#91. PR #87 stays draft and unmerged.

## Threat boundary
Existing-account isolation is weaker than account-level separation: root, administrators, Organizations delegates, IAM policy editors, KMS key administrators, and deployment principals can potentially bypass resource-role separation. **Do not claim full independence until their actual effective permissions and escalation paths are assessed.** No proof of AWS account identity, region, available IAM policies or production-seat AWS principals has been collected.

## Proposed principals, none provisioned
- **Human-security-admin**: separate MFA-protected Human identity managing gate IAM/KMS and change approval, not controlled by any AI seat or CI workflow.
- **seat4-gate-execution-role**: Lambda runtime role limited to exact DynamoDB approval table operations, narrowly scoped CloudWatch logging, and eventually a single versioned Secrets Manager secret/KMS key after authorization. No IAM mutation, Lambda code/config update, STS role assumption, broad repository access, or policy modification.
- **seat4-gate-deployment-role**: distinct Human-gated deployment principal, not assumable by GitHub Actions or production seats. May change only named gate resources after independent review; may not self-approve requests.
- **seat4-gate-audit-role**: read-only evidence access, no deletion or policy changes.
- **GitHub Actions requester**: no AWS deployment role, no key, no Lambda invocation privilege until an authenticated low-privilege request channel is reviewed. Even a request may only propose, never approve.
- **Gemini/Kiro/Copilot principals**: explicitly inventoried across IAM roles, IAM Identity Center permission sets, federation/OIDC trust and any inherited groups or chained assume-role permissions. Prove denied gate secret, key use, execution, update, policy change and audit deletion using effective policies and live tests.

## Account-level hardening review
Inventory root access, account admins, Organization SCPs (if available), permission boundaries, service-linked roles, IAM trust policy conditions, access keys, role chaining and resource policies. An SCP or permissions boundary is supplementary, not sufficient alone. Confirm whether CI principal could update Lambda, its execution role, KMS grant, DynamoDB ledger, Secrets Manager resource policy, CloudTrail retention or audit bucket. If so, the gate does NOT satisfy separation of duties. Explicit denies must not accidentally lock out legitimate Human recovery; design and test controlled break-glass.

## AWS resources: proposal only
- API Gateway + authenticated request path with rate limiting; never accept caller-provided 'approved' flag as authority.
- Lambda function with deny-by-default allowlisted operation routing; deploy package and configuration under Human-controlled change gate; no generic command execution.
- DynamoDB request/nonce table using conditional writes and strongly consistent reads when appropriate. TTL only cleans up; do not rely on TTL for expiry or replay.
- External Human login with independently operated MFA/identity provider, approval bound to request digest, exact immutable target SHA, expiry, recipient, repo and action. Authenticate issuer/audience/subject and nonce; independently verify GitHub review events only as additional bound evidence.
- Future GitHub App key in a narrowly scoped Secrets Manager secret encrypted under a dedicated KMS key, accessible ONLY after effective controls verified. No production secret provision in this phase.
- CloudTrail/CloudWatch plus independent write-protected retention; reject requests if audit integrity cannot be maintained. Keep private payloads out of logs.
- GitHub App remains Contents read-only, scoped to one private repository; Gate owns tokens and never returns them to GitHub Actions.

## Credentials and permission gates
No GitHub App private key in GitHub Actions environments, Actions secrets, repository, PR text, chat, Lambda plaintext environment variables, or artifacts. Verify policy on both identity and resource sides; secrets and encryption are not sufficient protection if administrators or code-deployers can read or alter them. STS session credentials for the gate are scoped and short-lived.

## Human authorization and audit
Human login is independently authenticated with MFA outside Actions. Every approval is one-use, transaction-specific and expires. Execution must revalidate inputs, atomically consume nonce/approval, generate App installation token internally, perform a single allowlisted read-only operation in initial phase, and persist an independent audit receipt. Missing records, unavailable IAM identity provider, audit failure or changed payload => deny. A protected GitHub approval/review record is only acceptable if issuer identity and exact request scope are independently authenticated; an unenforced branch rule cannot establish protected approval.

## Stop conditions
STOP and propose migration to a separate AWS account/external provider if a production-seat principal or CI controls IAM/KMS administration, Lambda deployment, authorization records, or audit retention, and those privileges cannot be effectively segregated. No cutover, secrets or release activation under unresolved escalation paths.
