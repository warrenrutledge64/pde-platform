# Story 1.1 (re-scoped) — LIVE Deploy & Validation Runbook (operator copy-paste)

> **Story 1.1 is now the cross-account TRUST FABRIC** (RD-006), not the org-wide
> CloudTrail. The CloudTrail work is deferred (RD-007) to Story 4.1 and preserved in
> `infra/deferred/`. This runbook deploys the Spoke execution role into each Spoke
> and validates a Hub→Spoke `AssumeRole`.
>
> **Accounts in play:**
> - **Spokes** (where the role is deployed): `Pipeline-Dev`, `Pipeline-Sandbox`,
>   `Pipeline-Prod`.
> - **Hub** (where the AssumeRole is *initiated*): `Pipeline-Hub` `641628980935`.
> - **NOT** the management/root account (`467866449172`) — nothing here touches it.
>
> Run `aws sts get-caller-identity` before each block and confirm the account. A
> banner comment does not change your credentials.
>
> **Artifact:** `infra/spoke-execution-role.yaml` (offline-proven — 19 invariants via
> `python3 infra/validate_trust_fabric.py`). Story 1.1 stays 🟡 (VD-2) until the
> AssumeRole gate below returns a recorded pass.

---

## Inputs you need first

| Input | Value | Notes |
|-------|-------|-------|
| Hub account id | `641628980935` | The `Pipeline-Hub` shared control plane (RD-006). |
| Dev / Sandbox / Prod account ids | _(fill in)_ | The three Spoke account ids. `aws organizations list-accounts` from the mgmt account lists them if needed. |
| Hub deployer role name | `pde-hub-deployer` (default) | The specific Hub role allowed to assume the Spoke role. Created in Phase 2; the trust references it by name now (it need not exist yet). |
| ExternalId | _(a strong shared secret)_ | Required on AssumeRole (confused-deputy protection). Store in Hub config; do NOT commit the real value. |

## STEP 1 — Offline proof (optional re-run; already green in the repo)

```bash
python3 infra/validate_trust_fabric.py    # expect: PASS — all 19 trust-fabric invariants hold
```

> The full cfn-lint / cfn-guard / Checkov / Bandit static bar (Universal Criterion 3)
> runs here in CloudShell / CI (the build sandbox has PyPI blocked):
> ```bash
> pip install cfn-lint checkov
> cfn-lint infra/spoke-execution-role.yaml
> checkov -f infra/spoke-execution-role.yaml
> ```

## STEP 2 — Deploy the Spoke execution role into EACH Spoke

Run this block **three times — once per Spoke** — each time authenticated to that
Spoke account and with the matching `EnvironmentName`.

```bash
# CONTEXT: e.g. Pipeline-Dev  (repeat for Sandbox, then Prod)
aws sts get-caller-identity --query Account --output text   # expect the SPOKE account id

EXTERNAL_ID="<the-shared-secret>"     # same value the Hub deployer will present

aws cloudformation deploy \
  --region us-east-1 \
  --stack-name pde-trust-fabric \
  --template-file infra/spoke-execution-role.yaml \
  --parameter-overrides \
      HubAccountId=641628980935 \
      HubDeployerRoleName=pde-hub-deployer \
      ExternalId="$EXTERNAL_ID" \
      EnvironmentName=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=1.1 Component=trust-fabric

# For Sandbox: EnvironmentName=sandbox ; for Prod: EnvironmentName=prod
# (deploy each in that Spoke account's own session)
```

> **Chicken-and-egg note:** the Hub deployer role (`pde-hub-deployer`) does not exist
> until Phase 2. That is fine — an IAM trust policy may name a principal ARN that
> doesn't exist yet; the trust resolves at *assume-time*. Until the Hub role exists
> you validate the role's *existence + trust shape* (STEP 3a); the full live
> AssumeRole (STEP 3b) can be run once the Hub deployer role is created (Phase 2), or
> with a temporary stand-in role you control in the Hub.

## STEP 3 — VALIDATE (the Phase 1 gate, AssumeRole half)

```bash
# 3a. In EACH Spoke: confirm the role exists with the correct scoped trust.
# CONTEXT: the Spoke account
aws iam get-role --role-name pde-spoke-execution-dev \
  --query 'Role.{Name:RoleName,Trust:AssumeRolePolicyDocument}'
# EXPECT: trust Principal AWS = arn:aws:iam::641628980935:role/pde-hub-deployer,
#         Condition sts:ExternalId present. (NOT :root.)

# 3b. From the HUB, assume into each Spoke role and confirm the returned account id.
# CONTEXT: Pipeline-Hub 641628980935 (as the Hub deployer principal)
aws sts get-caller-identity --query Account --output text   # expect 641628980935

for ENV in dev sandbox prod; do
  ACCT=<the-matching-spoke-account-id>   # substitute per env
  echo "== $ENV =="
  aws sts assume-role \
    --role-arn "arn:aws:iam::${ACCT}:role/pde-spoke-execution-${ENV}" \
    --role-session-name pde-phase1-gate \
    --external-id "$EXTERNAL_ID" \
    --query 'AssumedRoleUser.Arn'
done
# EXPECT: each call returns an assumed-role ARN in the matching Spoke account id.
```

**PASS criteria (all must hold):**
1. In each Spoke, `get-role` shows the trust principal is the **specific Hub role**
   (`arn:aws:iam::641628980935:role/pde-hub-deployer`), not `:root`, with the
   `sts:ExternalId` condition present.
2. From the Hub, `assume-role` into each Spoke role **succeeds** and returns an
   assumed-role identity in that Spoke's account id.
3. Assume **without** the correct `ExternalId` is **denied** (confused-deputy
   protection working):
   ```bash
   aws sts assume-role --role-arn "arn:aws:iam::<spoke>:role/pde-spoke-execution-dev" \
     --role-session-name no-extid    # EXPECT: AccessDenied (no external id)
   ```

Record in `governance/RUNBOOK.md` Story 1.1:
`pass — Spoke roles deployed in Dev/Sandbox/Prod; Hub→Spoke AssumeRole succeeds (correct ExternalId) and is denied without it, <date>, confirmed by <who>`.

## STEP 4 — Zero-Touch-Root check (Universal Criterion 1)

```bash
# CONTEXT: management/root 467866449172
aws sts get-caller-identity --query Account --output text   # expect 467866449172
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName,'pde-')].StackName"
# EXPECT: [] — Story 1.1 deploys NOTHING in the management account.
```

## Backout / rollback (clean-state, Universal Criterion 4)

Per Spoke (deleting the stack removes the role + its managed policy; nothing is
retained, no data to preserve):

```bash
# CONTEXT: the Spoke account
aws cloudformation delete-stack --stack-name pde-trust-fabric
aws cloudformation wait stack-delete-complete --stack-name pde-trust-fabric
```

## Watch-items

- **Wrong account** is the #1 failure: STEP 2 runs in each **Spoke**; STEP 3b runs in
  the **Hub**. Re-run `aws sts get-caller-identity` per block.
- **`:root` in the trust** would be a scoping regression — the trust must name the
  specific Hub deployer role ARN (RD-006). STEP 3a checks this.
- **ExternalId** must match between the Spoke role and whatever the Hub presents; a
  mismatch (or omission) correctly yields `AccessDenied` — that is the guardrail
  working, not a bug.
- **Hub deployer role not yet created** (pre-Phase-2): validate 3a now; run 3b once
  the Hub role exists, or with a temporary Hub stand-in role you control.
- **Do NOT** deploy the Spoke role into the management account.
