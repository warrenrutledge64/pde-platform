# Story 3.2 — LIVE Deploy Runbook (FIRST real end-to-end pipeline run; closes VD-3b)

> **Story 3.2 = the FIRST time the real pipeline does a real cross-account deploy.**
> It stands up the unified Hub orchestrator (`pde-hub-orchestrator`), lights up the
> **two-hop deploy chain** (`pdlv-codebuild-service-role` → `pde-hub-orchestrator` →
> `pde-member-execution-dev`), triggers the live `pdlv-promotion-pipeline`, and lets
> the Hub orchestrate a cross-account CloudFormation deploy of the frozen Story 3.1
> Golden-Path artifact into **Pipeline-Dev `946509368326`**. Done when the Dev artifact
> stack is `CREATE_COMPLETE` and `describe-table` returns the live
> `pdlv-golden-path-artifact` table (on-demand, `Project=PDE`).
>
> **This runbook is the operator execution surface.** The INDEPENDENT validator
> (`story-3.2-VALIDATOR-HANDOVER.md`) authors the Definition of Done + seals the
> verdict; this runbook is how you (the operator) produce the raw evidence. The builder
> does NOT author the acceptance criteria.
>
> **Target (reference only — the operator trusts `aws sts get-caller-identity`, not a
> label):** Pipeline-Hub `641628980935`, region `us-east-1`. Members: Dev
> `946509368326`, Sandbox `586917955591`, Prod `466494951534`. Management/root
> `467866449172` is **zero-touch**. Pipeline-Forensics `360999005254` is **ZTIE's**,
> never a target.

---

> ### ⚠️ WHAT MAKES 3.2 DIFFERENT (read first)
>
> Phase 2 proved its gate with the **non-promoting `pdlv-gate-probe`**, so the live
> Hub→member assume (**VD-3b**) has **never run in production**. 3.2 closes it with a
> genuine two-hop chain:
>
> 1. **Hop 1** — the `pdlv-deploy` CodeBuild service role assumes the NEW
>    `pde-hub-orchestrator` role (same account).
> 2. **Hop 2** — the orchestrator (which the Phase-1 member roles already trust, with
>    the ExternalId) assumes `pde-member-execution-dev` and the deploy runs LOCALLY in
>    Dev (RD-006).
>
> Three things must be in place for hop 2 to succeed, and each is a STEP below:
> - the `pde-hub-orchestrator` role exists and is trusted ONLY by the deploy service
>   role (STEP 2);
> - the Dev member role can actually create the artifact (its execution policy now
>   grants `pdlv-`-scoped CloudFormation + DynamoDB — a redeploy of the member role,
>   STEP 2);
> - the ExternalId + repo-clone token are in Hub SSM so the deploy resolves them at the
>   edge (STEP 0). **A missing ExternalId shows up as a generic AccessDenied on hop 2 —
>   the buildspec fast-fails with a clear message so you don't misdiagnose it as a trust
>   defect.**

---

## STEP 0 — Launch pad, right code, and the two /pdlv/ secrets (Hub CloudShell)

**FREE DISK FIRST (OD-007 — CloudShell is ~1 GB and WILL fill up).**

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
df -h ~
rm -rf ~/.cache ~/.npm /tmp/* 2>/dev/null || true
df -h ~
```

Confirm the Hub, then clone the CORRECT repo and get on `feature/story-3.2`:

> **AUTHORITATIVE SOURCE (OD-008):** GitHub **`warrenrutledge64/pde-platform`**,
> token-auth. NOT CodeCommit, NOT `pde-hub`. Clone with the whole URL **QUOTED** and a
> **REAL** token — never the literal `<TOKEN>` (bash reads a bare `<` as a redirect).

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935
cd ~
rm -rf pde-platform
git clone "https://REAL_PAT@github.com/warrenrutledge64/pde-platform.git"
cd pde-platform
git remote -v                              # confirm github.com/warrenrutledge64/pde-platform
git fetch origin
git checkout feature/story-3.2
git reset --hard origin/feature/story-3.2
```

**STEP 0 LAUNCH-PAD LOCK (mechanical, fail-loud — paste as one block).** This is the
guard for the attempt-2 miss: in a fresh/lost CloudShell the operator ran commands from
OUTSIDE the clone (`git rev-parse HEAD` → "fatal: not a git repository"), so the STEP
2a-2d deploys never ran and the pipeline hit stale infra. This block HARD-EXITS unless
you are inside the clone, on `feature/story-3.2`, with every deliverable on disk — run it
and every later step from this same shell/directory:

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)  — run from ~/pde-platform
{
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || { echo "LAUNCH-PAD LOCK: FAIL — not inside a git repo (cd into ~/pde-platform first)"; exit 1; }
  BR=$(git rev-parse --abbrev-ref HEAD)
  [ "$BR" = "feature/story-3.2" ] \
    || { echo "LAUNCH-PAD LOCK: FAIL — on branch '$BR', expected feature/story-3.2"; exit 1; }
  git remote get-url origin | grep -q 'warrenrutledge64/pde-platform' \
    || { echo "LAUNCH-PAD LOCK: FAIL — origin is not warrenrutledge64/pde-platform"; exit 1; }
  for f in infra/hub-orchestrator-role.yaml infra/codebuild-projects.yaml \
           infra/state-machine.yaml infra/member-execution-role.yaml \
           infra/golden-path-artifact.yaml scripts/preflight_story_3_2.py; do
    test -f "$f" || { echo "LAUNCH-PAD LOCK: FAIL — $f missing (wrong checkout)"; exit 1; }
  done
  echo "LAUNCH-PAD LOCK: PASS — $(git rev-parse --abbrev-ref HEAD) @ $(git log --oneline -1)"
}
```

> Do not proceed past a `LAUNCH-PAD LOCK: FAIL`. Every subsequent STEP (2a-2d deploys,
> the preflight, STEP 4 trigger) assumes you are in THIS shell, in THIS directory, on
> this branch. If your CloudShell session drops or you open a new tab, re-run this block
> before continuing — losing the working directory is the attempt-2 failure.

**Populate the two `/pdlv/` SecureStrings (idempotent — safe to re-run).** These are
the secret-at-the-edge inputs the deploy project resolves at runtime; they must exist
BEFORE the first pipeline run or hop 2 / the clone fail-fasts.

- `EXTERNAL_ID` must be the **exact** value baked into the Phase-1 member trust (the
  `sts:ExternalId` condition on `pde-member-execution-<env>`). If you do not have it,
  it is the value used when the member roles were deployed (Story 1.1 /
  `restore/phase-1-green`).
- `REPO_TOKEN` is a **read-only** GitHub token (repo scope) for cloning the private PDE
  repo at the edge.

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# Set these two shell vars first (NOT echoed): the real ExternalId + a read-only PAT.
read -rs -p "ExternalId: " PDE_EXTERNAL_ID; echo
read -rs -p "Repo token (read-only PAT): " PDE_REPO_TOKEN; echo

aws ssm put-parameter --name /pdlv/promotion/external-id --type SecureString \
  --value "$PDE_EXTERNAL_ID" --overwrite \
  --tags Key=Project,Value=PDE Key=Story,Value=3.2 2>/dev/null \
  || aws ssm put-parameter --name /pdlv/promotion/external-id --type SecureString \
       --value "$PDE_EXTERNAL_ID" --overwrite
aws ssm put-parameter --name /pdlv/promotion/repo-token --type SecureString \
  --value "$PDE_REPO_TOKEN" --overwrite \
  --tags Key=Project,Value=PDE Key=Story,Value=3.2 2>/dev/null \
  || aws ssm put-parameter --name /pdlv/promotion/repo-token --type SecureString \
       --value "$PDE_REPO_TOKEN" --overwrite
unset PDE_EXTERNAL_ID PDE_REPO_TOKEN

# Confirm BOTH exist as SecureString (value NOT printed):
aws ssm get-parameter --name /pdlv/promotion/external-id --query "Parameter.Type" --output text
aws ssm get-parameter --name /pdlv/promotion/repo-token  --query "Parameter.Type" --output text
```

> The `--tags` on first create may fail on some CLI versions when combined with
> `--overwrite`; the `||` fallback writes the value regardless (tags are cosmetic here).

---

## STEP 1 — Dead-stack sweep (name-agnostic, `pdlv-*` only)

A dead `ROLLBACK_COMPLETE`/`*_FAILED` `pdlv-` stack blocks a re-deploy. Sweep the
`pdlv-` namespace ONLY — never touch a `pde-*` (ZTIE) stack, management, or Forensics.

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935
aws cloudformation list-stacks \
  --stack-status-filter ROLLBACK_COMPLETE CREATE_FAILED ROLLBACK_FAILED \
      UPDATE_ROLLBACK_FAILED DELETE_FAILED REVIEW_IN_PROGRESS \
  --query "StackSummaries[?starts_with(StackName, 'pdlv-')].StackName" --output text
# For EACH pdlv- name printed above (there should normally be none):
#   aws cloudformation delete-stack --stack-name <that-pdlv-name>
#   aws cloudformation wait stack-delete-complete --stack-name <that-pdlv-name>
```

---

## STEP 2 — Deploy the orchestrator + refresh the two-hop control plane (Hub)

Three deploys, all **additive** / in-place updates of `pdlv-` Hub stacks (plus a member
redeploy per account). Each carries the mandatory `Project=PDE` stack tag (OD-012).

**2a — the NEW unified Hub orchestrator** (`pde-hub-orchestrator`, pass-through + boundary,
trust pinned to the deploy service role):

> ⚠️ **LEGACY-ROLE COLLISION (found in attempt 2):** a `pde-hub-orchestrator` role already
> exists in the Hub, created `2026-06-10`, NOT managed by this stack (it trusts Step Functions,
> holds S3/events power, targets `pde-cross-account-deployer`). This CFN stack creates a role
> of the SAME name — `CreateStack` will fail with "already exists" if the legacy role is still
> there. Confirm whether it is CFN-managed and, if it is an un-managed legacy role, delete it
> first (it is a `pde-` *role*, not a ZTIE `pde-*` *stack* — deleting this specific role is in
> scope for closing VD-3b; do NOT touch any `pde-*` stack):
> ```bash
> # Target: Pipeline-Hub 641628980935 (us-east-1)
> aws iam get-role --role-name pde-hub-orchestrator \
>   --query "Role.{Created:CreateDate,Trust:AssumeRolePolicyDocument.Statement[0].Principal}" --output json
> # If it is the June-10 legacy role (trusts states.amazonaws.com) and NOT managed by a
> # pdlv- stack, detach its inline policies + delete it so the stack can create the correct one:
> #   for p in $(aws iam list-role-policies --role-name pde-hub-orchestrator --query PolicyNames --output text); do \
> #     aws iam delete-role-policy --role-name pde-hub-orchestrator --policy-name "$p"; done
> #   aws iam delete-role --role-name pde-hub-orchestrator
> ```

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws cloudformation deploy \
  --template-file infra/hub-orchestrator-role.yaml \
  --stack-name pdlv-hub-orchestrator \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=3.2 Component=hub-orchestrator \
  --no-fail-on-empty-changeset
aws cloudformation describe-stacks --stack-name pdlv-hub-orchestrator \
  --query "Stacks[0].StackStatus" --output text        # expect CREATE_COMPLETE / UPDATE_COMPLETE
# Confirm the role is now the Story-3.2 role (trust pinned to the CodeBuild service role):
aws iam get-role --role-name pde-hub-orchestrator \
  --query "Role.AssumeRolePolicyDocument.Statement[0].Principal" --output json
#   expect AWS=.../role/pdlv-codebuild-service-role  (NOT Service=states.amazonaws.com)
```

**2b — refresh the CodeBuild projects** (the `pdlv-deploy` project now does the two-hop
clone+deploy; the service role now assumes the orchestrator + reads the two `/pdlv/`
SecureStrings). Note: do NOT pass an `ExternalId` override here (removed from the
template — the secret is resolved at the edge):

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws cloudformation deploy \
  --template-file infra/codebuild-projects.yaml \
  --stack-name pdlv-codebuild \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=3.2 Component=codebuild \
  --no-fail-on-empty-changeset
aws cloudformation describe-stacks --stack-name pdlv-codebuild \
  --query "Stacks[0].StackStatus" --output text
```

**2c — refresh the state machine** (the `EXTERNAL_ID` plaintext passthrough is removed;
the ASL now overrides only `TARGET_ENV` + `TARGET_ROLE_ARN`). **Do NOT** pass
`--parameter-overrides ExternalId=...` — that parameter no longer exists:

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws cloudformation deploy \
  --template-file infra/state-machine.yaml \
  --stack-name pdlv-promotion-pipeline-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=3.2 Component=state-machine \
  --no-fail-on-empty-changeset
aws cloudformation describe-stacks --stack-name pdlv-promotion-pipeline-stack \
  --query "Stacks[0].StackStatus" --output text
```

**2d — redeploy the Dev member role FROM THIS BRANCH (BLOCKING — attempt-1 FAIL root cause).**
Attempt 1 (2026-10-04) sealed FAIL because this step was skipped: the pipeline ran against
the **pre-3.2 Phase-1 role** (scoped to `pde-*`, no DynamoDB grant, placeholder ExternalId,
still tagged `Story=1.1`). The deliverable was never deployed, so it was never judged. You
MUST redeploy the member role from `feature/story-3.2` AND VERIFY THE LIVE ROLE ACTUALLY
CHANGED before any pipeline run — never trust the deploy line. Run this **from a Pipeline-Dev
`946509368326` CloudShell/credential**, on the `feature/story-3.2` checkout (confirm with
`git log --oneline -1`). The ExternalId is the SAME shared secret you put in SSM in STEP 0:

```bash
# Target: Pipeline-Dev 946509368326 (us-east-1)  <-- SWITCH ACCOUNT
aws sts get-caller-identity --query Account --output text   # MUST print 946509368326
git log --oneline -1                                        # confirm feature/story-3.2 tip
read -rs -p "ExternalId (the REAL shared secret): " PDE_EXTERNAL_ID; echo
aws cloudformation deploy \
  --template-file infra/member-execution-role.yaml \
  --stack-name pde-trust-fabric \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides EnvironmentName=dev ExternalId="$PDE_EXTERNAL_ID" \
  --tags Project=PDE Story=3.2 Component=trust-fabric \
  --no-fail-on-empty-changeset
unset PDE_EXTERNAL_ID
aws cloudformation describe-stacks --stack-name pde-trust-fabric \
  --query "Stacks[0].StackStatus" --output text
```

**VERIFY THE LIVE ROLE CHANGED (do NOT proceed until all three pass):**

```bash
# Target: Pipeline-Dev 946509368326 (us-east-1)
# (1) The role now carries the Story=3.2 tag (proves the branch deployed, not the old role):
aws iam list-role-tags --role-name pde-member-execution-dev \
  --query "Tags[?Key=='Story'].Value" --output text          # MUST print 3.2 (NOT 1.1)
# (2) The attached managed policy now grants pdlv--scoped CFN + DynamoDB (not pde-, not empty):
POL=$(aws iam list-attached-role-policies --role-name pde-member-execution-dev \
  --query "AttachedPolicies[?contains(PolicyName,'member-execution-permissions')].PolicyArn" --output text)
VER=$(aws iam get-policy --policy-arn "$POL" --query "Policy.DefaultVersionId" --output text)
aws iam get-policy-version --policy-arn "$POL" --version-id "$VER" \
  --query "PolicyVersion.Document" --output json
#   EXPECT: cloudformation Resource ...stack/pdlv-* (NOT pde-*); a dynamodb statement with
#   CreateTable/DeleteTable/UpdateTable/Describe*/Tag* scoped to table/pdlv-* . If you still
#   see stack/pde-* or NO dynamodb block, the OLD role is live -> STOP, the branch did not deploy.
# (3) The trust ExternalId is a real value, not a placeholder:
aws iam get-role --role-name pde-member-execution-dev \
  --query "Role.AssumeRolePolicyDocument.Statement[0].Condition" --output json
#   EXPECT a StringEquals sts:ExternalId with a real secret (NOT "<paste-the-new-value>" / any placeholder).
```

> If any of the three VERIFY checks shows the OLD role (`pde-*` scope, no DynamoDB, placeholder
> ExternalId, or `Story=1.1`), the branch was NOT deployed — STOP and fix the deploy before
> STEP 4. Triggering the pipeline against the old role is exactly the attempt-1 FAIL.

---

## STEP 3 — Prove the two-hop assume live (VD-3b) BEFORE triggering the pipeline

A quick, read-only proof the chain works end-to-end, so a pipeline failure can be
cleanly attributed. Run in Hub CloudShell.

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # 641628980935
# HOP 1: assume the orchestrator (as yourself / the CodeBuild role if you can):
ORCH=$(aws sts assume-role \
  --role-arn arn:aws:iam::641628980935:role/pde-hub-orchestrator \
  --role-session-name vd3b-hop1 --query Credentials --output json 2>&1) && echo "HOP1 OK" || echo "HOP1: $ORCH"
# (If you are not the deploy service role, hop 1 may be denied by the pinned trust —
#  that is CORRECT. The authoritative hop-1+hop-2 proof is the pipeline run in STEP 4,
#  which runs AS the pdlv-codebuild-service-role.)
```

> The orchestrator trust is pinned to `pdlv-codebuild-service-role`, so a human SSO
> principal is EXPECTED to be denied hop 1 — that is the chokepoint working, not a bug.
> The real VD-3b proof is the live pipeline deploy in STEP 4/5 (the CodeBuild run logs
> show `get-caller-identity` landing in Dc `946509368326` after hop 2).

---

## STEP 4 — Trigger the pipeline (the first real end-to-end run)

> ### 🚦 PRE-FLIGHT GATE — MECHANICAL, not prose (do NOT start the pipeline until it PASSES)
> This gate exists because attempts 1 AND 2 (2026-10-04) FAILED by triggering the pipeline
> against **un-redeployed, stale infra** (a June-10 legacy `pde-hub-orchestrator`, the pre-3.2
> state machine/buildspec, the `Story=1.1` Dev member role) — in attempt 2 the operator was
> not even inside the clone (`git rev-parse HEAD` -> "fatal: not a git repository"), so the
> STEP 2a-2d `cloudformation deploy` commands never ran. Prose "please deploy first" gates
> kept being skipped, so this is now a MECHANICAL check that reads the LIVE resources and
> hard-fails unless they match the Story-3.2 baseline:
>
> ```bash
> # Target: Pipeline-Hub 641628980935 (us-east-1), with Dev 946509368326 read access
> # (run from INSIDE the feature/story-3.2 clone — confirm first):
> git rev-parse --abbrev-ref HEAD && git log --oneline -1   # MUST be feature/story-3.2 (NOT "fatal: not a git repository")
> python3 scripts/preflight_story_3_2.py --hub-profile <hub> --dev-profile <dev>
> ```
>
> It MUST print `preflight_story_3_2: PASS`. A FAIL (exit 1) means the branch is NOT deployed
> — go back and run STEP 2a-2d, then re-run the preflight. An ENV error (exit 2) means a
> credentials/account read problem — fix that; it is not a baseline result. Do NOT trigger the
> pipeline on anything but a printed PASS.
>
> Also confirm both `/pdlv/` SecureStrings exist with REAL values (STEP 0):
> ```bash
> aws ssm get-parameter --name /pdlv/promotion/external-id --query "Parameter.Type" --output text  # SecureString
> aws ssm get-parameter --name /pdlv/promotion/repo-token  --query "Parameter.Type" --output text  # SecureString
> ```

Start the production `pdlv-promotion-pipeline`. DeployDev is the first state; it starts
the `pdlv-deploy` CodeBuild project, which does the two-hop deploy into Dev and then the
execution reaches `AwaitSandboxApproval` and PAUSES (3.3 handles the promotion).

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
SM_ARN=$(aws cloudformation describe-stacks --stack-name pdlv-promotion-pipeline-stack \
  --query "Stacks[0].Outputs[?OutputKey=='PromotionStateMachineArn'].OutputValue" --output text)
echo "state machine: $SM_ARN"
EXEC_ARN=$(aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --name "story-3-2-$(date +%s)" --input '{"artifact":"golden-path"}' \
  --query executionArn --output text)
echo "execution: $EXEC_ARN"
# Poll until DeployDev finishes and the execution reaches the pause (RUNNING):
aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" \
  --query "{status:status}" --output json
# Read the DeployDev CodeBuild logs (two-hop proof — hop1 orchestrator, hop2 Dev id):
aws logs tail /aws/codebuild/pdlv-deploy --since 15m --format short | tail -60
```

> If DeployDev fails: capture the CodeBuild build's `phases`/log verbatim and the CFN
> `CREATE_FAILED` `ResourceStatusReason` (STEP 5) — do NOT diagnose from "it rolled
> back". The buildspec fast-fails loudly on an empty ExternalId/token (a STEP 0 miss).

---

## STEP 5 — VERIFY the live result in Pipeline-Dev (not the green execution line)

The skeptical proof: the artifact stack is `CREATE_COMPLETE` in Dev and the live
`pdlv-golden-path-artifact` table exists, is on-demand, and is `Project=PDE`-tagged.
**Run from a Pipeline-Dev `946509368326` CloudShell/credential.**

```bash
# Target: Pipeline-Dev 946509368326 (us-east-1)  <-- SWITCH ACCOUNT
aws sts get-caller-identity --query Account --output text   # MUST print 946509368326
aws cloudformation describe-stacks --stack-name pdlv-golden-path-artifact \
  --query "Stacks[0].{Status:StackStatus,Tags:Tags}" --output json
# If it failed, capture the exact reason (do not guess):
aws cloudformation describe-stack-events --stack-name pdlv-golden-path-artifact \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason]" \
  --output text | head
# The live table — on-demand, present, named pdlv-golden-path-artifact:
aws dynamodb describe-table --table-name pdlv-golden-path-artifact \
  --query "Table.{Name:TableName,Status:TableStatus,Billing:BillingModeSummary.BillingMode}" \
  --output json
aws dynamodb list-tags-of-resource \
  --resource-arn "$(aws dynamodb describe-table --table-name pdlv-golden-path-artifact --query 'Table.TableArn' --output text)" \
  --query "Tags" --output json
```

> Hand ALL raw output back to the validator. On the sealed PASS the executor records
> the verdict, flips 3.2 ✅, and authors Story 3.3's warm handoff. 3.2 does NOT close
> Phase 3 (3.3/3.4 remain). On FAIL/INCONCLUSIVE, 3.2 stays 🟡.

---

## Backout

The artifact is one empty, free DynamoDB table — minimal blast radius. To back out the
Dev artifact: `aws cloudformation delete-stack --stack-name pdlv-golden-path-artifact`
(from Pipeline-Dev). The Hub control-plane updates (orchestrator, codebuild,
state-machine) are additive `pdlv-` stacks; revert by redeploying
`restore/phase-2-green` templates if a Hub-side defect is found. Never touch a `pde-*`
(ZTIE) stack, management `467866449172`, or Forensics `360999005254`.
