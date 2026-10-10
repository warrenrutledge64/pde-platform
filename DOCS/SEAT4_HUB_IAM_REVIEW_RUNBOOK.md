# Troikauge Issue #81 — Pipeline-Hub IAM review runbook

**Preparation only. No command has been executed against AWS.** AWS target: Pipeline-Hub (641628980935), region `us-east-1`. Use a Human-controlled read-only profile. Do not paste raw IAM data/account credentials in chats or commit to shared PDE. Account numbers here identify architecture, not authorization.

## First no-change verification
1. The Human selects a read-only AWS CLI profile for Hub, independent from Gemini, Kiro, Copilot and CI. The inventory script at `scripts/seat4_iam_inventory_readonly.sh` (proposal PR #93) is still draft; review locally before use.
2. Run read-only identity query privately: `AWS_PROFILE=<human-auditor> aws sts get-caller-identity`. Confirm the returned Account matches expected Hub ID before proceeding; **STOP** otherwise. Do not share raw response; report only match/mismatch.
3. Using `AWS_PROFILE=<human-auditor>`, review existing IAM roles/users/managed policy bindings, principal trust relationships, OIDC providers, KMS key/grant administrators, Secrets Manager resource policies, Lambda and API Gateway modification permissions, DynamoDB approval tables, and audit retention control.
4. Build a **private** authority graph including effective principals that operate `pdlv-` and ZTIE orchestration, CI/deployments, management/root/admins and each production AI seat. Include indirect `sts:AssumeRole` / `iam:PassRole` / role update / OIDC trust alteration paths. If IAM inspection denies an action, mark UNKNOWN, not SAFE.
5. Test least-privilege design offline first. Do **not** call `secretsmanager:GetSecretValue`, `kms:Decrypt`, create roles, deploy Lambda or generate private keys during this phase.

## Public / private separation
**Shared proposal:** account roles, high-level target namespace, threat model, evidence *categories*, no real principal ARNs/trust paths or raw logs. **Private evidence:** actual role names/IDs and permissions, complete trust policy documents, API outcomes, account inventory exports, signer/authenticator details. The existing Codex Connector no longer has private repo read access, so do not temporarily widen it to store evidence. Keep locally with Human until an authenticated Seat 4-only write route exists.

## Verification matrix
| Test | Expected | Current |
|---|---|---|
| Human auditor account identity | Matches Hub; read-only | UNKNOWN |
| Production-seat principals can change Lambda | DENY | UNKNOWN |
| Production-seat principals can read App secret / KMS Decrypt | DENY | UNKNOWN |
| Production-seat principals can edit IAM or assume gate roles | DENY | UNKNOWN |
| Hub `pdlv-` and ZTIE orchestrator can mutate gate controls | DENY | UNKNOWN |
| CI can alter API Gateway policy / approval ledger | DENY | UNKNOWN |
| Gate may receive ZTIE raw artifacts | NEVER | NOT IMPLEMENTED |
| Audit sink modifications by gate/CI | DENY | UNKNOWN |
| Human MFA transaction-specific approval | REQUIRED | NOT IMPLEMENTED |
| Seat 4-only App installation, read-only | CONFIGURED in UI; token test pending | UNVERIFIED EFFECTIVE |
| Current Codex Connector read of private GitHub repository | DENY | 404 observed, scoped only |

## Exit criteria
After inventory, run controlled denial tests under **actual** principals with separate Human authorization. An IAM policy simulator alone is insufficient. Compare results and record privately. Only then decide whether existing Hub account genuinely supports independent authorization. If not, return to Human with a revised trust boundary. Never silently advance PR #87 or enable packets.
