# Issue #81 — Credential-free verification and setup checklist

**All steps are planned, not executed; no AWS credential or account access is assumed.**

## A. Inventory before creating resources
- [ ] Human identifies **AWS account ID privately** and chosen AWS region (do not paste sensitive credentials or secrets).
- [ ] Inventory root/admins; discover all GitHub OIDC integrations, IAM roles/policies, Identity Center/federated access, trust relationships, KMS administrators and CI deployment principals.
- [ ] Create a private effective-permission matrix for Human, external-gate deployer, future runtime, audit reader, CI requester, Gemini, Kiro and Copilot. Identify any shared principals.
- [ ] Confirm Human MFA and a separately controlled authorization identity.
- [ ] Review CloudTrail organization/account logging and immutable audit retention ownership.

## B. Credential-free prototype
- [ ] Run `python3 -m unittest discover -s scripts -p test_seat4_aws_gate.py` on PR #91 in a trusted CI environment; do not assume 15 cases pass.
- [ ] Add mock IAM policy evaluation fixtures with explicit expected-deny outcomes for unauthorized principals.
- [ ] Test request schema, changed digest/ref, unknown operation, wrong audience, missing origin authentication, replay nonce, stale/expired request, forged Human approval, failed audit sink and changed Lambda artifact hash.
- [ ] Ensure tests never call AWS, generate tokens, deploy resources, or upload private material; use mock signers and storage only.
- [ ] Independently review proposed IAM roles, resource policies, trust policies, permission boundaries, and path to privileged operations.

## C. Later sandbox security test (requires separate Human approval)
- [ ] Use isolated nonproduction/test-only IAM roles and no secrets; inspect effective permissions through IAM Access Analyzer, policy simulator and actual scoped API denial attempts (simulation alone is not proof).
- [ ] Verify deny for non-Human AWS principals: `secretsmanager:GetSecretValue`, `kms:Decrypt`, `kms:CreateGrant`, `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`, `iam:PassRole`, `iam:UpdateAssumeRolePolicy`, `sts:AssumeRole`, approval table writes/changes, and audit policy/deletion operations. Also check paths for privilege escalation and service-specific wildcard grants.
- [ ] Positive test Human-approved read-only request with mock credentials, bound SHA/nonce and independently retained receipt.
- [ ] Disable audit/identity provider and verify all requests deny.
- [ ] Record actor, test time, allowed/denied API operations, policy version/hashes, CloudTrail event references, test run SHA in the private evidence store (only after access grants are verified).

## D. Production release prerequisites
- [ ] Human separately ratifies design and authentic approval gate.
- [ ] Privilege-escalation review and denial tests PASS for actual production-seat identities; otherwise STOP.
- [ ] Human explicitly authorizes any real Secrets Manager/KMS/key creation after enforcement proven; do NOT proceed under this plan alone.
- [ ] Issue #80 test suite and negative leakage tests independently executed.
- [ ] PR #87 remains DRAFT until tests/dependencies verified and Human explicitly approves promotion/merge; operational release requires an additional Human decision.

## Exact current evidence
- Private GitHub branch protection shows 'Not enforced'; `seat4-production` is not a valid secret gate.
- Existing Codex Connector after selected-repositories restriction returned 404 accessing private repo; does not prove all identities denied.
- AWS account/region and inventory not verified; no AWS resource, credentials, secrets, or audit backend provisioned.

## Next Human input
Provide AWS **region** and whether existing production-seat AWS principals share administrative roles with the prospective gate's owner. The initial inventory can proceed without disclosing account IDs or credentials in chat.
