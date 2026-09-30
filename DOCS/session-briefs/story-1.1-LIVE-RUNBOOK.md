# Story 1.1 (orchestrate-and-pull) — LIVE Deploy & Validation Runbook

> **Story 1.1 is the tier-1 TRUST FABRIC for the RD-006 orchestrate-and-pull model:**
> a **member execution role** in each member account that a **specific Hub
> orchestrator role** can assume/direct. The Hub **directs**; the deployment
> **executes locally in the member**; the Hub does **not** push writes in. This
> runbook deploys that role per member and validates a Hub→member `AssumeRole`.
>
> **Tight tier-1 scope:** this proves the trust *identity + direction* only. The
> orchestration engine (Step Functions), the results intake data-contract, and the
> Hub-signed decision-token machinery are Phase 2.
>
> **Accounts in play:**
> - **Members** (where the role is deployed + where execution happens):
>   `Pipeline-Dev`, `Pipeline-Sandbox`, `Pipeline-Prod`.
> - **Hub** (where the orchestrator initiates the AssumeRole): `Pipeline-Hub`
>   `641628980935`.
> - **NOT** the management/root account (`467866449172`).
>
> Run `aws sts get-caller-identity` before each block and confirm the account.
>
> **Artifact:** `infra/member-execution-role.yaml` (offline-proven — 21 invariants
> via `python3 infra/validate_trust_fabric.py`). Story 1.1 stays 🟡 (VD-3) until the
> AssumeRole gate below returns a recorded pass.

---

## Inputs you need first

| Input | Value | Notes |
|-------|-------|-------|
| Hub account id | `641628980935` | The `Pipeline-Hub` shared control plane (RD-006). |
| Dev / Sandbox / Prod account ids | _(fill in)_ | The three member account ids. `aws organizations list-accounts` from the mgmt account lists them. |
| Hub orchestrator role name | `pde-hub-orchestrator` (default) | The specific Hub role allowed to direct the member role. Created in Phase 2; the trust names it now (need not exist yet). |
| ExternalId | _(a strong shared secret)_ | Required on AssumeRole (confused-deputy protection). Store in Hub config; do NOT commit the real value. |

## STEP 1 — Offline proof (optional re-run; already green in the repo)

```bash
python3 infra/validate_trust_fabric.py    # expect: PASS — all 21 orchestrate-and-pull invariants hold
```

> Full cfn-lint / cfn-guard / Checkov / Bandit static bar (Universal Criterion 3)
> runs here in CloudShell / CI (the build sandbox has PyPI blocked):
> ```bash
> pip install cfn-lint checkov
> cfn-lint infra/member-execution-role.yaml
> checkov -f infra/member-execution-role.yaml
> ```

## STEP 2 — Deploy the member execution role into EACH member

Run this block **three times — once per member** — each time authenticated to that
member account with the matching `EnvironmentName`.

```bash
# CONTEXT: e.g. Pipeline-Dev  (repeat for Sandbox, then Prod)
aws sts get-caller-identity --query Account --output text   # expect the MEMBER account id

EXTERNAL_ID="<the-shared-secret>"     # same value the Hub orchestrator will present

aws cloudformation deploy \
  --region us-east-1 \
  --stack-name pde-trust-fabric \
  --template-file infra/member-execution-role.yaml \
  --parameter-overrides \
      HubAccountId=641628980935 \
      HubOrchestratorRoleName=pde-hub-orchestrator \
      ExternalId="$EXTERNAL_ID" \
      EnvironmentName=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=1.1 Component=trust-fabric

# For Sandbox: EnvironmentName=sandbox ; for Prod: EnvironmentName=prod
# (deploy each in that member account's own session)
```

> **Chicken-and-egg note:** the Hub orchestrator role (`pde-hub-orchestrator`) does
> not exist until Phase 2. That is fine — an IAM trust policy may name a principal
> ARN that doesn't exist yet; the trust resolves at *assume-time*. Until the Hub
> role exists you validate the role's *existence + trust shape* (STEP 3a); the full
> live AssumeRole (STEP 3b) runs once the Hub orchestrator role is created (Phase 2),
> or with a temporary stand-in role you control in the Hub.

## STEP 3 — VALIDATE (the Phase 1 gate, orchestrate-and-pull direction)

```bash
# 3a. In EACH member: confirm the role exists with the correct scoped trust.
# CONTEXT: the member account
aws iam get-role --role-name pde-member-execution-dev \
  --query 'Role.{Name:RoleName,Trust:AssumeRolePolicyDocument}'
# EXPECT: trust Principal AWS = arn:aws:iam::641628980935:role/pde-hub-orchestrator,
#         Condition sts:ExternalId present. (NOT :root.)

# 3b. From the HUB (as the orchestrator principal), assume into each member role
#     and confirm the returned account id — this is the Hub DIRECTING the member.
# CONTEXT: Pipeline-Hub 641628980935
aws sts get-caller-identity --query Account --output text   # expect 641628980935

for ENV in dev sandbox prod; do
  ACCT=<the-matching-member-account-id>   # substitute per env
  echo "== $ENV =="
  aws sts assume-role \
    --role-arn "arn:aws:iam::${ACCT}:role/pde-member-execution-${ENV}" \
    --role-session-name pde-phase1-gate \
    --external-id "$EXTERNAL_ID" \
    --query 'AssumedRoleUser.Arn'
done
# EXPECT: each call returns an assumed-role ARN in the matching member account id.
```

**PASS criteria (all must hold):**
1. In each member, `get-role` shows the trust principal is the **specific Hub
   orchestrator role** (`arn:aws:iam::641628980935:role/pde-hub-orchestrator`), not
   `:root`, with the `sts:ExternalId` condition present.
2. From the Hub, `assume-role` into each member role **succeeds** and returns an
   assumed-role identity in that member's account id (the Hub can direct the member).
3. Assume **without** the correct `ExternalId` is **denied** (confused-deputy
   protection working):
   ```bash
   aws sts assume-role --role-arn "arn:aws:iam::<member>:role/pde-member-execution-dev" \
     --role-session-name no-extid    # EXPECT: AccessDenied (no external id)
   ```

Record in `governance/RUNBOOK.md` Story 1.1:
`pass — member exec roles deployed in Dev/Sandbox/Prod; Hub→member AssumeRole succeeds (correct ExternalId) and is denied without it, <date>, confirmed by <who>`.

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

Per member (deleting the stack removes the role + its managed policy; nothing
retained, no data to preserve):

```bash
# CONTEXT: the member account
aws cloudformation delete-stack --stack-name pde-trust-fabric
aws cloudformation wait stack-delete-complete --stack-name pde-trust-fabric
```

## Watch-items

- **Direction:** this is orchestrate-and-pull — the Hub *directs*, the member
  *executes locally*. STEP 2 runs in each **member**; STEP 3b runs in the **Hub**.
  Re-run `aws sts get-caller-identity` per block.
- **`:root` in the trust** would be a scoping regression — the trust must name the
  specific Hub **orchestrator** role ARN (RD-006). STEP 3a checks this.
- **ExternalId** mismatch/omission correctly yields `AccessDenied` — the guardrail
  working, not a bug.
- **Hub orchestrator role not yet created** (pre-Phase-2): validate 3a now; run 3b
  once the Hub role exists, or with a temporary Hub stand-in role you control.
- **Do NOT** deploy the member role into the management account.
- **Not in scope here:** the orchestration engine, the member→Hub results
  intake-contract, and the Hub-signed decision token — those are Phase 2.
