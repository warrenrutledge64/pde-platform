# Troikauge 3.0 / Issue #81 — us-east-1 credential-free IAM inventory package

**Design / preparation only, not AWS evidence.** Human selected an existing AWS account, region `us-east-1`, and external Human authorization gate (Lambda + Secrets Manager + KMS). No account connection, AWS execution, resource creation, secrets, release, or IAM policy change is authorized by this package.

## Boundaries
- The existing GitHub personal-account branch-protection rule is marked **Not enforced**. The GitHub Actions `seat4-production` environment is not an authorization or secret-protection mechanism.
- Keep GitHub App private key and installation tokens outside GitHub Actions, GitHub repository and chat; the proposed future gate alone may hold them after independently verified controls.
- The selected AWS account is shared with other workloads. Isolation is unproven until effective permission, assumed-role paths, KMS grants, Lambda update rights, DynamoDB write rights and audit controls are reviewed against **actual** production-seat principals. IAM boundaries alone may not block account administrators.
- `us-east-1` is the planned regional deployment target, **not** proof all IAM resources are regional: IAM users, roles, identity policies and trust relationships are account-global. Inventory relevant cross-region / cross-account escalation paths as applicable.

## Human-controlled execution instructions
1. Privately choose an existing AWS CLI profile whose effective permissions are **read-only**, under a Human-controlled principal. Do not use Kiro, Gemini, Copilot or production CI credentials. The script will not itself ensure the profile is read-only.
2. Review `scripts/seat4_iam_inventory_readonly.sh` before execution. It uses only AWS describe/get/list APIs and writes metadata to a new absolute local directory. It requires the environment variable `AWS_PROFILE`, deliberately does not accept static access keys, and performs **no AWS call until a Human runs it**.
3. Example: `AWS_PROFILE=human-inventory bash scripts/seat4_iam_inventory_readonly.sh /absolute/private/path/seat4-iam-inventory`
4. Store raw output privately and securely. IAM trust policies, account identifiers, user names, ARNs and infrastructure metadata can be sensitive. Do **not** commit output to PDE or paste it into chat. Do not treat script output as complete proof of effective restrictions.
5. The initial script does not enumerate every KMS key policy, Secrets Manager resource policy, attached permission boundary/SCP, CloudTrail bucket policy, IAM Identity Center effective grant or regional resource policy. Those require a subsequent Human-driven scoped review.
6. If any command lacks permission, record that evidence as `NOT_INSPECTED`; do not assume the relevant configuration is absent. Do not silently increase privileges.

## Evidence table (fill privately, redact when summarizing)
| Control | Evidence to collect | Result |
|---|---|---|
| Caller authority | STS caller identity and account/role provenance | NOT_INSPECTED |
| AWS administrators | IAM/admin policies, trust chains, root and federated/Identity Center permissions | NOT_INSPECTED |
| Production seats | Actual principal identities for Gemini, Kiro, Copilot, their CI, OIDC and roles | NOT_INSPECTED |
| Gate deployment control | Who can modify Lambda function/code, aliases, layers, resource policy, IAM pass-role | NOT_INSPECTED |
| Gate runtime | Exact future least-privilege role, trust policy, permission boundary | NOT_INSPECTED |
| Key custody | KMS key policy, grants, grant creation, Secrets Manager ACL and resource policy | NOT_INSPECTED |
| Approval state | Who can put/update/delete DynamoDB entries and tables, plus backup/restore | NOT_INSPECTED |
| Audit custody | Who can stop/update CloudTrail, modify logs, retention, bucket object-lock and KMS | NOT_INSPECTED |
| Cross-account access | STS roles, federation, org SCPs and CI OIDC audience/subject trust | NOT_INSPECTED |
| Human approval | Independent MFA authenticator, requester separation, scope/digest binding | NOT_DESIGNED |
| Direct denial probes | Authenticated actual-role API denial with harmless test resources | NOT_EXECUTED |

## Verification phases
A. Inventory effective identities and policies **without modifying resources**.
B. Offline review of IAM/STS assume-role and permission escalation paths; mock tests for approval forgery, SHA substitution, wrong audience, replay, expiry, token leakage and audit outage.
C. Independent Human decision on any temporary *nonproduction* read-only security test roles, followed by separately authorized live denied-call testing. IAM simulation is useful but not proof of real credentials' effective access.
D. Only after controls are demonstrably enforced: new, separately authorized provisioning decision for AWS infrastructure and future secrets. Never use GitHub Actions unprotected environment or repository workflows to administer the gate.

## Acceptance / stop rules
Fail closed if shared administrators or production-seat credentials can alter Lambda code or its execution role, Secret Manager/KMS access, approval state or audit evidence without independent Human authorization. Stop if Human MFA/approval and separate gate deployment protection cannot be enforced. The Issue #80 packet checker and issue #81 Lambda prototype remain non-production. PR #87 stays **draft, open, unmerged**, until independent tests and dependencies are verified and Human separately authorizes merge.
