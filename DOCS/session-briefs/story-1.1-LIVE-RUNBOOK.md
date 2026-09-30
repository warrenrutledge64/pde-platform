# Story 1.1 (orchestrate-and-pull) — LIVE Deploy & Validation Runbook (turnkey)

> **Story 1.1 = the tier-1 trust fabric (RD-006):** a **member execution role** in each
> member account that a *specific Hub orchestrator role* can assume/direct. The Hub
> **directs**; execution is **local to the member**; the Hub does not push writes in.
>
> **This run uses VALIDATION PATH A (trust-shape).** The Hub orchestrator role
> (`pde-hub-orchestrator`) is created in **Phase 2**, so we validate that each member
> role EXISTS with the correct trust (specific Hub role + ExternalId, never `:root`).
> The full live Hub→member `AssumeRole` is deferred to Phase 2 when that role exists.
>
> **Accounts (PDE only — Pipeline-Forensics `360999005254` is ZTIE's, NOT in PDE):**
> - Members (deploy target): Pipeline-Dev `946509368326`, Pipeline-Sandbox
>   `586917955591`, Pipeline-Prod `466494951534`.
> - Hub (orchestrator, referenced in trust): Pipeline-Hub `641628980935`.
> - Management/root `467866449172`: **zero-touch** — nothing here.
>
> Run `aws sts get-caller-identity` before each block and confirm the account.
> **Artifact:** `infra/member-execution-role.yaml` (offline-proven — 21 invariants via
> `python3 infra/validate_trust_fabric.py`). Story 1.1 stays 🟡 (VD-3) until the
> Path-A validation below returns a recorded pass.

---

## STEP 0 — Set your session variables ONCE (in CloudShell)

```bash
# The ONLY secret. Choose a strong value; do NOT commit it anywhere.
EXTERNAL_ID="<choose-a-strong-shared-secret>"

# Account IDs (pre-filled — PDE members + Hub):
DEV_ID=946509368326
SANDBOX_ID=586917955591
PROD_ID=466494951534
HUB_ID=641628980935
HUB_ORCHESTRATOR_ROLE=pde-hub-orchestrator   # created in Phase 2; trust names it now
```

> The account IDs are baked into the commands below for readability; `EXTERNAL_ID`
> stays a variable so the secret never lands in a file or the repo.

## STEP 1 — Offline proof (optional re-run; already green in the repo)

```bash
python3 infra/validate_trust_fabric.py    # expect: PASS — all 21 orchestrate-and-pull invariants hold
```

> Full cfn-lint / cfn-guard / Checkov static bar runs here in CloudShell / CI (the
> build sandbox has PyPI blocked):
> ```bash
> pip install cfn-lint checkov
> cfn-lint infra/member-execution-role.yaml
> checkov -f infra/member-execution-role.yaml
> ```

## STEP 2 — Deploy the member execution role into EACH member

Run each block in **that member account's** CloudShell session (switch roles/creds
between them — confirm the banner each time).

```bash
# ── Pipeline-Dev (946509368326) ──────────────────────────────────────────────
aws sts get-caller-identity --query Account --output text   # expect 946509368326
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name pde-trust-fabric \
  --template-file infra/member-execution-role.yaml \
  --parameter-overrides \
      HubAccountId=641628980935 \
      HubOrchestratorRoleName="$HUB_ORCHESTRATOR_ROLE" \
      ExternalId="$EXTERNAL_ID" \
      EnvironmentName=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=1.1 Component=trust-fabric
```

```bash
# ── Pipeline-Sandbox (586917955591) ──────────────────────────────────────────
aws sts get-caller-identity --query Account --output text   # expect 586917955591
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name pde-trust-fabric \
  --template-file infra/member-execution-role.yaml \
  --parameter-overrides \
      HubAccountId=641628980935 \
      HubOrchestratorRoleName="$HUB_ORCHESTRATOR_ROLE" \
      ExternalId="$EXTERNAL_ID" \
      EnvironmentName=sandbox \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=1.1 Component=trust-fabric
```

```bash
# ── Pipeline-Prod (466494951534) ─────────────────────────────────────────────
aws sts get-caller-identity --query Account --output text   # expect 466494951534
aws cloudformation deploy \
  --region us-east-1 \
  --stack-name pde-trust-fabric \
  --template-file infra/member-execution-role.yaml \
  --parameter-overrides \
      HubAccountId=641628980935 \
      HubOrchestratorRoleName="$HUB_ORCHESTRATOR_ROLE" \
      ExternalId="$EXTERNAL_ID" \
      EnvironmentName=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=1.1 Component=trust-fabric
```

## STEP 3 — VALIDATE (Path A — trust shape)

In **each member account**, confirm the role exists with the correct scoped trust.

```bash
# CONTEXT: the member account (repeat for dev / sandbox / prod)
aws iam get-role --role-name pde-member-execution-dev \
  --query 'Role.{Name:RoleName,Trust:AssumeRolePolicyDocument}'
# (sandbox → pde-member-execution-sandbox ; prod → pde-member-execution-prod)
```

**PASS criteria (all must hold, in every member):**
1. The role exists (`pde-member-execution-<env>`).
2. Its trust `Principal.AWS` is the **specific Hub orchestrator role ARN** —
   `arn:aws:iam::641628980935:role/pde-hub-orchestrator` — **not** `...:root`.
3. The trust has a `Condition` requiring `sts:ExternalId`.

> **Deferred to Phase 2 (not a failure):** the full live Hub→member `sts:AssumeRole`
> can't run yet because `pde-hub-orchestrator` doesn't exist until Phase 2. When it
> does, the assume-succeeds-with-ExternalId / denied-without check runs then. Path A
> proves the trust is **correct-by-construction** now.

Record in `governance/RUNBOOK.md` Story 1.1:
`pass — member exec roles deployed in Dev/Sandbox/Prod; get-role confirms trust names the specific Hub orchestrator role (not :root) + requires sts:ExternalId; full Hub→member AssumeRole deferred to Phase 2 (Path A), <date>, confirmed by <who>`.

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

- **Direction:** orchestrate-and-pull — STEP 2 runs in each **member**; the Hub is
  only *referenced* in the trust. Re-run `aws sts get-caller-identity` per block.
- **`:root` in the trust = a scoping regression.** STEP 3 must show the specific Hub
  orchestrator role ARN + the ExternalId condition.
- **`EXTERNAL_ID`** is a secret — set it once in STEP 0, never commit it. It must
  match whatever the Hub orchestrator will present in Phase 2.
- **Pipeline-Forensics (`360999005254`) is ZTIE's account — do NOT deploy here.**
  Story 1.1's members are Dev/Sandbox/Prod only.
- **Do NOT** deploy the member role into the management account.
- **Not in scope here (Phase 2 / deferred):** the Hub orchestrator role, Step
  Functions, the member→Hub results intake-contract, the signed-decision token, and
  the org-wide CloudTrail (Story 4.1).
