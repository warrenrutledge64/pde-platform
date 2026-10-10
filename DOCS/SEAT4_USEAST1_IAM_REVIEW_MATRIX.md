# Issue #81 — Credential-free isolation review matrix

**Template, not a completed attestation.** Store filled-in principal names, account IDs and evidentiary URLs only in the properly isolated private evidence store when verified; do not publish them in PDE.

| Principal class | Read private records | Mint GitHub App token | Change gate code | Change key/secret policy | Approve operation | Edit approval ledger | Delete audit |
|---|---|---|---|---|---|---|---|
| Human security admin | Policy-defined | Controlled setup only | Via independent reviewed change | Via independent reviewed change | Human-only with MFA | No silent mutation | Controlled recovery only |
| Seat 4 gate execution role (future) | Narrow approved reads | Internally for allowlisted operations | DENY | DENY | DENY | Atomic scoped transitions | DENY |
| Gate deployer (future) | DENY by default | DENY | Human-controlled change only | DENY by default | DENY | DENY | DENY |
| GitHub Actions requester | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| Gemini Planner/Validator principals | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| Kiro Builder principal | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| Copilot Moderator principal | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| Audit reader (future) | Evidence metadata only | DENY | DENY | DENY | DENY | DENY | DENY |

These are **target authorization requirements**, not facts about deployed principals. Require effective permission evaluation of identity/resource policies, explicit denies, boundaries, session policies, KMS key policy and grants, trust chains, SCPs if used, and administrator override capabilities. Verify on real principals and record the results outside production-seat-readable repos.

## AWS read-only API surfaces for review
- IAM: `GetAccountAuthorizationDetails`, `GetRole`, `ListAttachedRolePolicies`, `ListRolePolicies`, `GetRolePolicy`, `GetPolicyVersion`, `ListOpenIDConnectProviders`, `GetOpenIDConnectProvider`.
- STS: `GetCallerIdentity`; examine role trust chains offline.
- KMS: `ListKeys`, `DescribeKey`, `GetKeyPolicy`, `ListGrants`.
- Secrets Manager: `ListSecrets`, `DescribeSecret`, `GetResourcePolicy` (never `GetSecretValue`).
- Lambda: `ListFunctions`, `GetFunctionConfiguration`, `GetPolicy` (never deployment/update).
- CloudTrail: `DescribeTrails`, `GetTrailStatus`, `ListEventDataStores`, `GetEventSelectors`.
- CloudWatch Logs, S3/CloudTrail backing store: assess read-only retention, object-lock, policy and ownership settings as applicable.
- IAM Access Analyzer: findings and policy validation are advisory; independently verify actual denial.

### Policy review invariants
1. No production-seat or CI principal can call `iam:PassRole` to a privileged role, assume it, change trust, or modify gate deployment policy.
2. No production-seat or CI principal can bypass approval by modifying Lambda code/config, API Gateway routes, DynamoDB approval table, human authentication configuration or audit output.
3. No plaintext GitHub App key or installation token in Actions secrets/environment.
4. Unenforced private-repo branch protection cannot be counted as a Human review requirement.
5. Every claimed PASS has an evidence reference and independent reviewer; otherwise status is UNKNOWN or BLOCKED.
