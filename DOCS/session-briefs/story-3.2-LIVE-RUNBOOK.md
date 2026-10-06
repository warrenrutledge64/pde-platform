# Story 3.2 — LIVE Deploy Runbook (FIRST real end-to-end pipeline run; closes VD-3b)

> **Story 3.2 = the FIRST time the real pipeline does a real cross-account deploy.**
> It stands up the unified Hub orchestrator (`pdlv-hub-orchestrator` — a fresh,
> collision-proof RD-009 name, NOT the legacy `pde-hub-orchestrator`), lights up the
> **two-hop deploy chain** (`pdlv-codebuild-service-role` → `pdlv-hub-orchestrator` →
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
>    `pdlv-hub-orchestrator` role (same account).
> 2. **Hop 2** — the orchestrator (which the Phase-1 member roles trust once repointed,
>    with the ExternalId) assumes `pde-member-execution-dev` and the deploy runs LOCALLY
>    in Dev (RD-006). _(The member trust default is now `pdlv-hub-orchestrator`; STEP 2d
>    redeploys the Dev member role from the branch, which repoints the live trust.)_
>
> Three things must be in place for hop 2 to succeed, and each is a STEP below:
> - the `pdlv-hub-orchestrator` role exists and is trusted ONLY by the deploy service
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

## STEP 1 — Reconcile the `pdlv-` namespace to the canonical set (name-driven, `pdlv-*` only)

> **Two failure classes to clear before STEP 2 deploys (both learned live):**
> 1. a **dead** `ROLLBACK_COMPLETE`/`*_FAILED` `pdlv-` stack blocks a re-deploy; and
> 2. a **healthy but MISNAMED** `pdlv-` stack from a prior manual run holds the
>    resource-name lease and makes STEP 2 fail with
>    `[AWS::EarlyValidation::ResourceExistenceCheck]` (Attempt-5 blocker: rogue
>    `pdlv-codebuild-projects` + `pdlv-state-machine` held the CodeBuild / Step
>    Functions names that the canonical `pdlv-codebuild` / `pdlv-promotion-pipeline-stack`
>    needed). A status-only sweep MISSES case 2 — a misnamed stack can be
>    `CREATE_COMPLETE`.
>
> This step therefore reconciles by NAME: the ONLY `pdlv-` stacks that may exist for
> Story 3.2 are the canonical three — **`pdlv-hub-orchestrator`**, **`pdlv-codebuild`**,
> **`pdlv-promotion-pipeline-stack`**. ANY OTHER `pdlv-`-named stack (misnamed rogue or
> dead) is swept. Sweep the `pdlv-` namespace ONLY — never touch a `pde-*` (ZTIE) stack,
> management `467866449172`, or Forensics `360999005254`.

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935

# The canonical Story-3.2 pdlv- stack set — everything else in pdlv- is a stray to clear.
CANON="pdlv-hub-orchestrator pdlv-codebuild pdlv-promotion-pipeline-stack"

# List EVERY pdlv- stack currently present (any non-deleted status), then compute the
# strays = present pdlv- stacks NOT in the canonical set (this catches BOTH a healthy
# misnamed stack like pdlv-codebuild-projects / pdlv-state-machine AND any dead stack).
PRESENT=$(aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE \
      ROLLBACK_COMPLETE CREATE_FAILED ROLLBACK_FAILED UPDATE_ROLLBACK_FAILED \
      DELETE_FAILED REVIEW_IN_PROGRESS IMPORT_COMPLETE IMPORT_ROLLBACK_COMPLETE \
  --query "StackSummaries[?starts_with(StackName, 'pdlv-')].StackName" --output text)
echo "pdlv- stacks present: ${PRESENT:-<none>}"

STRAYS=""
for S in $PRESENT; do
  case " $CANON " in
    *" $S "*) : ;;                 # canonical — keep
    *) STRAYS="$STRAYS $S" ;;      # not in the canonical set — stray to sweep
  esac
done
echo "STRAY pdlv- stacks to delete (misnamed/dead, not in the canonical set):${STRAYS:-<none>}"

# Reusable pdlv--only force-delete that CLEARS a DELETE_FAILED stack (attempt-6:
# pdlv-promotion-pipeline-stack was stuck DELETE_FAILED — a plain delete-stack+wait does
# NOT clear that state; you must re-issue delete-stack RETAINING the stuck resources).
force_delete () {
  local S="$1"
  case "$S" in pdlv-*) : ;; *) echo "REFUSING to touch non-pdlv stack: $S"; return 0 ;; esac
  local ST
  ST=$(aws cloudformation describe-stacks --stack-name "$S" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo ABSENT)
  [ "$ST" = ABSENT ] && { echo "  $S already absent"; return 0; }
  echo "deleting pdlv- stack: $S (status $ST)"
  aws cloudformation delete-stack --stack-name "$S"
  if aws cloudformation wait stack-delete-complete --stack-name "$S" 2>/dev/null; then
    echo "  deleted: $S"; return 0
  fi
  # DELETE_FAILED path: retry retaining the resources that blocked the delete.
  ST=$(aws cloudformation describe-stacks --stack-name "$S" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo ABSENT)
  [ "$ST" = ABSENT ] && { echo "  deleted: $S"; return 0; }
  if [ "$ST" = DELETE_FAILED ]; then
    local STUCK
    STUCK=$(aws cloudformation describe-stack-events --stack-name "$S" \
      --query "StackEvents[?ResourceStatus=='DELETE_FAILED'].LogicalResourceId" --output text | tr '\t' ' ')
    echo "  DELETE_FAILED; retrying --retain-resources $STUCK"
    aws cloudformation delete-stack --stack-name "$S" --retain-resources $STUCK
    aws cloudformation wait stack-delete-complete --stack-name "$S" 2>/dev/null \
      && echo "  deleted (retained stuck resources): $S" \
      || { echo "  STILL stuck: $S — capture describe-stack-events and STOP (do not deploy over it)"; return 1; }
  else
    echo "  $S is $ST — inspect before deploying; do not proceed"; return 1
  fi
}

# Delete each stray — pdlv--only guard (never a pde-*/ZTIE/management/Forensics stack):
for S in $STRAYS; do force_delete "$S"; done

# ALSO clear any CANONICAL stack sitting in a DEAD / DELETE_FAILED / *_FAILED state (attempt-6:
# a canonical name can be stuck DELETE_FAILED and must be cleared before a fresh create):
for S in $CANON; do
  ST=$(aws cloudformation describe-stacks --stack-name "$S" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo ABSENT)
  case "$ST" in
    DELETE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED|CREATE_FAILED|UPDATE_ROLLBACK_FAILED|REVIEW_IN_PROGRESS)
      echo "canonical stack $S is $ST — clearing before deploy"; force_delete "$S" ;;
    *) : ;;  # ABSENT / CREATE_COMPLETE / UPDATE_COMPLETE are fine (STEP 2 create-or-update)
  esac
done

# VERIFY no pdlv- stack remains in a dead/stuck state, and only canonical names (or none) are present:
echo "--- dead/stuck pdlv- stacks remaining (EXPECT none) ---"
aws cloudformation list-stacks \
  --stack-status-filter DELETE_FAILED ROLLBACK_COMPLETE ROLLBACK_FAILED CREATE_FAILED \
      UPDATE_ROLLBACK_FAILED REVIEW_IN_PROGRESS \
  --query "StackSummaries[?starts_with(StackName, 'pdlv-')].StackName" --output text
echo "--- live pdlv- stacks (EXPECT only canonical names, or empty) ---"
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?starts_with(StackName, 'pdlv-')].StackName" --output text
# If any dead/stuck pdlv- stack remains, or any NON-canonical name is present, STOP — STEP 2 will collide.
```

> **Only ever delete `pdlv-`-named stacks**, and only those outside the canonical set.
> Deleting a stray `pdlv-` stack is non-destructive to ZTIE/PDE's real control plane
> (the canonical stacks are re-created in STEP 2; the artifact is a disposable empty
> table). If a stray stack has EXPORTS imported by another stack, delete the importer
> first (CloudFormation will name it in the delete error) — but in a clean Story-3.2
> Hub there should be none.

---

## STEP 2 — Deploy the orchestrator + refresh the two-hop control plane (Hub)

Three deploys, all **additive** / in-place updates of `pdlv-` Hub stacks (plus a member
redeploy per account). Each carries the mandatory `Project=PDE` stack tag (OD-012).

> ### 🧭 STEP 2 DIRECTORY GUARD — run FIRST, in the SAME shell as every 2a-2d deploy (BLOCKING)
> Attempt 6 (2026-10-04) failed because the deploys ran from the home directory (`~`), not the
> clone — so `--template-file infra/*.yaml` resolved to nothing and every deploy died with
> `[ERROR]: Invalid template path`. The STEP-0 LAUNCH-PAD LOCK is a separate block that was
> skipped. This guard re-asserts the working directory + branch + template presence RIGHT HERE,
> and HARD-EXITS the shell before any `cloudformation deploy` if you are not in the clone. Paste
> it as one block, in the same CloudShell tab you will run 2a-2c in; re-paste it if the tab drops:
>
> ```bash
> # Target: Pipeline-Hub 641628980935 (us-east-1)  — run from ~/pde-platform
> {
>   case "$(pwd)" in */pde-platform) : ;; *) echo "STEP2 GUARD: FAIL — pwd is $(pwd), not .../pde-platform. Run: cd ~/pde-platform"; exit 1 ;; esac
>   git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "STEP2 GUARD: FAIL — not inside the git clone (cd ~/pde-platform)"; exit 1; }
>   [ "$(git rev-parse --abbrev-ref HEAD)" = "feature/story-3.2" ] || { echo "STEP2 GUARD: FAIL — not on feature/story-3.2"; exit 1; }
>   for f in infra/hub-orchestrator-role.yaml infra/codebuild-projects.yaml infra/state-machine.yaml infra/member-execution-role.yaml; do
>     test -f "$f" || { echo "STEP2 GUARD: FAIL — $f not found from $(pwd) (wrong dir/branch)"; exit 1; }
>   done
>   echo "STEP2 GUARD: PASS — $(pwd) @ $(git log --oneline -1); templates resolve. Safe to deploy."
> }
> ```
>
> Do NOT run any 2a-2d `cloudformation deploy` until this prints `STEP2 GUARD: PASS`. The guard
> for STEP 2d (which runs in the Dev account) is restated in that block, since it is a different
> shell/account.

**2a — the NEW unified Hub orchestrator** (`pdlv-hub-orchestrator`, pass-through + boundary,
trust pinned to the deploy service role):

> ✅ **COLLISION-PROOF BY DESIGN (resolves the attempt-4 blocker).** Attempt 4 was blocked
> because the earlier template tried to create a role literally named `pde-hub-orchestrator`,
> and a legacy role of that exact name already exists in the Hub (created `2026-06-10`, trusts
> Step Functions, targets `pde-cross-account-deployer`). Per the stakeholder decision (Q1,
> 2026-10-05), the Story-3.2 orchestrator is renamed to **`pdlv-hub-orchestrator`** — a fresh
> `pdlv-` name (RD-009-clean; `pde-*` is ZTIE's). Because the name is new, this deploy CANNOT
> collide with the legacy role, so there is **no legacy-cleanup step and nothing to delete** —
> you never touch, delete, or even need to diagnose the ownership of the legacy
> `pde-hub-orchestrator` role (whether it is CFN-managed by `PDE-Orchestrator-Foundation` or
> un-managed no longer matters). This honours the ZTIE/legacy zero-touch boundary.
>
> _(Optional, informational only — NOT required to proceed. If you want the record of what the
> legacy role is, you may read it; it is never modified:_
> ```bash
> # Target: Pipeline-Hub 641628980935 (us-east-1) — READ-ONLY, informational
> aws iam get-role --role-name pde-hub-orchestrator \
>   --query "Role.{Created:CreateDate,Tags:Tags,Path:Path}" --output json 2>/dev/null \
>   || echo "legacy pde-hub-orchestrator not present (nothing to note)"
> ```
> _A `aws:cloudformation:stack-name` tag ⇒ it is CFN-managed by that stack; absent ⇒ un-managed
> legacy. Either way we do nothing to it — our role is `pdlv-hub-orchestrator`.)_

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
# Confirm the NEW role exists and its trust is pinned to the CodeBuild service role:
aws iam get-role --role-name pdlv-hub-orchestrator \
  --query "Role.AssumeRolePolicyDocument.Statement[0].Principal" --output json
#   expect AWS=.../role/pdlv-codebuild-service-role  (NOT Service=states.amazonaws.com)
# Confirm the permissions boundary is attached:
aws iam get-role --role-name pdlv-hub-orchestrator \
  --query "Role.PermissionsBoundary" --output json      # expect a pdlv-hub-orchestrator-boundary ARN
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

> **STEP 2d DIRECTORY GUARD (BLOCKING — this is a DIFFERENT shell + account than 2a-2c).**
> The Dev shell in attempt 6 was outside the clone (`git log` → "fatal: not a git repository").
> You must have the `feature/story-3.2` clone on THIS Dev CloudShell too (clone it here if the
> Dev CloudShell is a fresh box). Paste this guard first; it hard-exits unless you are in the
> clone, on the branch, in Dev, with the member template present:
>
> ```bash
> # Target: Pipeline-Dev 946509368326 (us-east-1)  — run from ~/pde-platform on the Dev box
> {
>   [ "$(aws sts get-caller-identity --query Account --output text)" = "946509368326" ] || { echo "2d GUARD: FAIL — not in Pipeline-Dev 946509368326"; exit 1; }
>   case "$(pwd)" in */pde-platform) : ;; *) echo "2d GUARD: FAIL — pwd is $(pwd), not .../pde-platform (clone the repo on the Dev box + cd in)"; exit 1 ;; esac
>   git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "2d GUARD: FAIL — not inside the git clone"; exit 1; }
>   [ "$(git rev-parse --abbrev-ref HEAD)" = "feature/story-3.2" ] || { echo "2d GUARD: FAIL — not on feature/story-3.2"; exit 1; }
>   test -f infra/member-execution-role.yaml || { echo "2d GUARD: FAIL — infra/member-execution-role.yaml not found from $(pwd)"; exit 1; }
>   echo "2d GUARD: PASS — Dev 946509368326, $(pwd) @ $(git log --oneline -1)"
> }
> ```

```bash
# Target: Pipeline-Dev 946509368326 (us-east-1)  <-- SWITCH ACCOUNT (run from ~/pde-platform)
aws sts get-caller-identity --query Account --output text   # MUST print 946509368326
git rev-parse --abbrev-ref HEAD && git log --oneline -1     # MUST be feature/story-3.2 (NOT "fatal: not a git repository")
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
  --role-arn arn:aws:iam::641628980935:role/pdlv-hub-orchestrator \
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
>
> **PR STRUCTURE FOR THE CLOSE-OUT (two PRs, by design — see METHODOLOGY §7).** Story
> 3.2's non-deliverable work (this runbook + the handoff docs + the governance ledger
> records of attempts 1-4 and the Q1 rename) was split onto **docs-only PR #43**, which
> merged to `main` immediately because it touches no `infra/*.yaml` (the merge-order
> guard does not apply). The **deployable deliverable** — the four `infra/*.yaml`
> templates + their pinned checkers/scripts + the static-bar workflow — stays on the
> **gated PR #42**, which is intentionally un-mergeable (`mergeable_state: unstable`,
> merge-order guard RED) while the gate is **ARMED**. So the close-out rides **#42**:
> on the sealed PASS, land the close-out commit on `feature/story-3.2` (record the
> verdict in `governance/RUNBOOK.md`, flip 3.2 ✅, clear VD-9 → set **Gate status:
> DISARMED**, add the new deployed resources to BOM §2). The merge-order guard then
> goes GREEN, #42 becomes mergeable, and the deliverable + close-out land together.

---

## Backout

The artifact is one empty, free DynamoDB table — minimal blast radius. To back out the
Dev artifact: `aws cloudformation delete-stack --stack-name pdlv-golden-path-artifact`
(from Pipeline-Dev). The Hub control-plane updates (orchestrator, codebuild,
state-machine) are additive `pdlv-` stacks; revert by redeploying
`restore/phase-2-green` templates if a Hub-side defect is found. Never touch a `pde-*`
(ZTIE) stack, management `467866449172`, or Forensics `360999005254`.
---

## Validation Attempt 3 — SEALED INCONCLUSIVE (Environment / Execution Failure)

**Date:** 2026-10-04
**Validator:** Independent AI Validator (did not author the deliverable or the DoD rubric)
**Target under test:** branch `feature/story-3.2`, HEAD `03cb20e`, PR #42 (open, not merged)
**Verdict:** **INCONCLUSIVE — the branch deliverable was NOT under test (stale/undeployed live infra + unreachable Dev account).** Not a FAIL: no DoD condition could be evaluated against the branch, so there is nothing to pass or fail.

### Evidence (raw output on the real AWS system)

1. **Stale Hub orchestrator — decisive.** `aws iam get-role --role-name pde-hub-orchestrator` (Hub `641628980935`) returned a trust Principal of `states.amazonaws.com` / `states.us-east-1.amazonaws.com`. The branch template `infra/hub-orchestrator-role.yaml` pins the trust to EXACTLY `arn:aws:iam::<hub>:role/pdlv-codebuild-service-role` (Sid `TrustOnlyTheCodeBuildDeployServiceRole`) and never trusts the Step Functions service — so `states.*` is a state the branch template cannot produce. This is the legacy pre-3.2 role; the branch was never deployed.

2. **Plaintext ExternalId in the SFN execution history — independent confirmation.** The execution history passed `"EXTERNAL_ID": "set-this-at-deploy-time"` as an environment-variable override. The branch `infra/state-machine.yaml` REMOVED the ExternalId passthrough entirely (overrides carry only `TARGET_ENV` + `TARGET_ROLE_ARN`); the secret is resolved at the edge via a `PARAMETER_STORE` env var in `infra/codebuild-projects.yaml`. A plaintext `EXTERNAL_ID` placeholder in the history can only come from the OLD Phase-2 definition — i.e. the stale state machine is live.

3. **Dev account unreachable.** Every Dev-targeted command failed with `aws: [ERROR]: The config profile (dev-profile) could not be found`, and the `pdlv-deploy` CodeBuild step failed at `aws sts assume-role` (`exit status 254`). The Dev-side DoD (artifact stack did not pre-exist; live `describe-table` for `pdlv-golden-path-artifact`; `Project=PDE` tag; `pdlv-`-scoped member role) could not be exercised at all. Unprovable ≠ failed.

Per the validation rules, stale/undeployed infra and a missing profile are INCONCLUSIVE (execution failure), not FAIL. Per the write-only-scribe covenant: Story 3.2 stays 🟡, no status flipped, `governance/RUNBOOK.md` untouched.

### Carry-forward for the re-run (attempt 4)

- **Judge the Dev member role by POLICY CONTENT, not the `Story` tag.** This branch's `infra/member-execution-role.yaml` still tags the role `Story=1.1`; only the deployed artifact STACK/TABLE gets `Story=3.2` (from the deploy buildspec `--tags`). Validate the role strictly by its mechanically enforceable bounds: the concrete `dynamodb:` table-lifecycle action set scoped to `table/pdlv-*` (NOT `dynamodb:*`, no data-plane item actions) and the CloudFormation grant scoped to `stack/pdlv-*`. Any `pde-`/wildcard-resource grant is a defect.
- **Confirm the branch IS deployed before judging anything:** `pde-hub-orchestrator` trust Principal = `.../role/pdlv-codebuild-service-role` (NOT `states.*`); `pdlv-promotion-pipeline` definition contains NO `EXTERNAL_ID`.
- **Establish a working `dev-profile`** (or assumable route into `946509368326`) and **confirm the `pdlv-golden-path-artifact` stack does not pre-exist** in Dev before the run, so a PASS proves THIS run created it.

### RUNBOOK record (one line — for the stakeholder to transcribe when they choose; NOT written to governance/RUNBOOK.md by the validator)

`INCONCLUSIVE — execution failure (stale Hub infra deployed: orchestrator trust=states.amazonaws.com + plaintext EXTERNAL_ID placeholder in SFN history = pre-3.2 infra; missing dev-profile blocked all Dev-account checks), 2026-10-04, confirmed by AI Validator`

---

## Validation Attempt 4 — SEALED INCONCLUSIVE (Environment / Execution Failure)

**Date:** 2026-10-04
**Validator:** Independent AI Validator (did not author the deliverable or the DoD rubric)
**Target under test:** branch `feature/story-3.2`, HEAD `03cb20e`, PR #42 (open, not merged)
**Verdict:** **INCONCLUSIVE — the branch deliverable was NOT under test (Hub deploy blocked by a name collision).** Not a FAIL: the orchestrator stack never created, so no DoD condition could be evaluated.

### Evidence (raw output on the real AWS system)

- The Story 3.2 Hub deploy was blocked: a `pde-hub-orchestrator` role already exists in Hub (`641628980935`), so `cloudformation deploy` of the orchestrator stack could not create the role of the same name. The `feature/story-3.2` orchestrator (trust pinned to `pdlv-codebuild-service-role`, pass-through + permissions boundary) was therefore never stood up — the branch was not under test.

### Open question that determines the correct next step (NOT yet resolved from raw output)

The runbook's STEP 2a documents this collision as an **un-managed, hand-created legacy IAM role** (created 2026-06-10; trusts `states.amazonaws.com`; holds S3/events power; targets `pde-cross-account-deployer`) and prescribes an in-scope remedy: confirm it is not CFN-managed, then detach its inline policies and `delete-role` it — explicitly a `pde-` *role* deletion (in scope for closing VD-3b), NOT a `pde-*` *stack* change.

Whether a true Catch-22 exists depends on one unverified fact: is `pde-hub-orchestrator` actually CloudFormation-managed (e.g. owned by a live `PDE-Orchestrator-Foundation` stack), or the un-managed legacy role the runbook assumes?

- **If un-managed (runbook's assumption):** no dead-end — run STEP 2a cleanup as written, redeploy, re-check. This is an execution step not yet performed, not a design defect.
- **If CFN-managed by `PDE-Orchestrator-Foundation`:** deleting the role out from under CloudFormation is wrong; the runbook's "un-managed" assumption is itself the defect — kick back to the builder/architect to either release the name from that stack (with authorization) or refactor Story 3.2 to a new orchestrator role name and repoint the member-role trust.

**The validator does NOT assert which world is true** — sealing a specific root cause on an unverified stack lease is the exact trap this process avoids. The verdict is INCONCLUSIVE either way (branch not deployed, nothing under test); the ownership answer only decides the operator's next move.

### One raw check that settles it (Hub `641628980935`, us-east-1)

- `aws iam get-role --role-name pde-hub-orchestrator` → read `Role.Tags` + `Role.Path`. A CFN-managed role carries an `aws:cloudformation:stack-name` / `aws:cloudformation:stack-id` tag naming its owning stack. Present + naming `PDE-Orchestrator-Foundation` ⇒ true scope conflict. Absent ⇒ un-managed legacy role ⇒ STEP 2a cleanup applies.
- `aws cloudformation describe-stacks --stack-name PDE-Orchestrator-Foundation` (does it exist?) and, if so, `aws cloudformation list-stack-resources --stack-name PDE-Orchestrator-Foundation` filtered for the role's logical id.

### RUNBOOK record (one line — for the stakeholder to transcribe; NOT written to governance/RUNBOOK.md by the validator)

`INCONCLUSIVE — execution failure (Hub deploy blocked: pde-hub-orchestrator name collision prevented the Story 3.2 orchestrator stack from creating; ownership of the colliding role — un-managed legacy vs. CFN-managed by PDE-Orchestrator-Foundation — not yet confirmed from raw output, so root cause unresolved; branch not under test), 2026-10-04, confirmed by AI Validator`

### Operator next steps

1. Resolve the ownership question first (the one `get-role` tags + `describe-stacks`/`list-stack-resources` check above); paste the raw output.
2. If un-managed: run STEP 2a cleanup as written (detach inline policies, `delete-role`; a `pde-` *role*, not a `pde-*` *stack*), redeploy the three Hub stacks, re-check (orchestrator trust = `pdlv-codebuild-service-role`; state machine has no `EXTERNAL_ID`).
3. If CFN-managed by `PDE-Orchestrator-Foundation`: kick back to the builder/architect (release the name with authorization, or refactor to a new orchestrator name + repoint member-role trust).
4. Establish the Dev route (`dev-profile` → `946509368326`), confirm `pdlv-golden-path-artifact` does not pre-exist, then run the full LIVE-RUNBOOK and paste raw output for the final seal (Attempt 5).

Per the write-only-scribe covenant: Story 3.2 stays 🟡, no status flipped, `governance/RUNBOOK.md` untouched. For the re-run, judge the Dev member role by POLICY CONTENT (concrete `dynamodb:` table-lifecycle actions scoped to `table/pdlv-*`; CloudFormation scoped to `stack/pdlv-*`), not the `Story` tag.

---

## Attempt 5 — RESOLUTION OF THE ATTEMPT-4 BLOCKER (orchestrator name collision)

**Date:** 2026-10-05
**Decision owner:** warrenrutledge64 (stakeholder) — chose **Q1** (rename), builder implemented.

Attempt 4 sealed INCONCLUSIVE because the Hub deploy was blocked by a name collision: the
earlier Story-3.2 orchestrator template tried to create a role named literally
`pde-hub-orchestrator`, and a legacy role of that exact name already exists in the Hub
(`CreateDate 2026-06-10`; trusts `states.amazonaws.com`; targets `pde-cross-account-deployer`).
Whether that legacy role is CFN-managed (e.g. by `PDE-Orchestrator-Foundation`) or un-managed
dictated two mutually-exclusive remedies — and could only be read live.

**Resolution (collision-proof regardless of that ownership answer):** the Story-3.2
orchestrator is **renamed `pde-hub-orchestrator` → `pdlv-hub-orchestrator`**, and the Phase-1
member-role trust + the Phase-1 gate script are repointed to the new name. This:

- is **RD-009-clean** — the orchestrator is a Hub resource, so it belongs in the `pdlv-`
  namespace (the legacy `pde-hub-orchestrator` name was itself an RD-009 violation);
- is **collision-proof by construction** — a brand-new `pdlv-` name cannot collide with the
  legacy `pde-hub-orchestrator`, so there is **no legacy cleanup / delete step** and the
  legacy role's ownership (CFN-managed vs. un-managed) **no longer matters** — we never touch,
  delete, or diagnose it (ZTIE/legacy zero-touch boundary honoured);
- repoints the member trust **in the same run** — STEP 2d redeploys the Dev member role from
  the branch (its `HubOrchestratorRoleName` default is now `pdlv-hub-orchestrator`), so the
  live Dev trust names the new orchestrator.

**What changed in the deliverable (branch `feature/story-3.2`):**
`infra/hub-orchestrator-role.yaml` (role name → `pdlv-hub-orchestrator`, `pdlv-`-only
`AllowedPattern`, pdlv- export names unchanged); `infra/member-execution-role.yaml`
(`HubOrchestratorRoleName` default → `pdlv-hub-orchestrator`); `infra/codebuild-projects.yaml`
(`OrchestratorRoleName` default → `pdlv-hub-orchestrator`, hop-1 target by param, unchanged);
`scripts/phase1_gate.py` (`HUB_ORCHESTRATOR_ROLE = "pdlv-hub-orchestrator"`);
`scripts/preflight_story_3_2.py` (`ORCHESTRATOR_ROLE = "pdlv-hub-orchestrator"`); the offline
checkers + their `--self-test`s updated accordingly (all green). The two-hop chain is now
`pdlv-codebuild-service-role → pdlv-hub-orchestrator → pde-member-execution-<env>`.

**This SUPERSEDES the Attempt-3/4 "operator next steps" above** (the delete-if-unmanaged /
kick-back-if-CFN-managed branch): there is no longer a branch to take — just run the clean
LIVE-RUNBOOK top to bottom. The Attempt-3/4 records themselves are retained verbatim as the
audit trail (do not edit sealed verdicts); only the forward operator action changes.

### The clean Attempt-5 run (no legacy cleanup)

1. **STEP 0** — launch pad + LAUNCH-PAD LOCK (inside the `feature/story-3.2` clone) + populate
   the two `/pdlv/` SecureStrings (`external-id` = the real Phase-1 member-trust secret;
   `repo-token` = a read-only PAT).
2. **STEP 1** — dead-stack sweep (`pdlv-*` only).
3. **STEP 2a-2c** — deploy `pdlv-hub-orchestrator` (new name, no collision), refresh
   `pdlv-codebuild`, refresh `pdlv-promotion-pipeline-stack` (Hub).
4. **STEP 2d** — redeploy the Dev member role from the branch (Pipeline-Dev `946509368326`),
   then VERIFY the live role changed: `Story=3.2` tag, `stack/pdlv-*` CFN scope + `table/pdlv-*`
   DynamoDB grant, and the trust Principal now names `.../role/pdlv-hub-orchestrator` with a
   real ExternalId.
5. **STEP 4 PRE-FLIGHT** — `python3 scripts/preflight_story_3_2.py --hub-profile <hub>
   --dev-profile <dev>` MUST print `preflight_story_3_2: PASS` (it now reads the live
   `pdlv-hub-orchestrator`). A FAIL = branch not deployed; go back to STEP 2.
6. **STEP 4/5** — trigger `pdlv-promotion-pipeline`, let DeployDev run the two-hop deploy, and
   verify from the live Dev account: the `pdlv-golden-path-artifact` stack is `CREATE_COMPLETE`
   and `describe-table` returns the on-demand `pdlv-golden-path-artifact` table tagged
   `Project=PDE`. Paste ALL raw output back for the independent validator to seal Attempt 5.

> This runbook is the operator execution surface (how to produce the raw output); it is
> NOT the acceptance criteria. The INDEPENDENT validator authors the Definition of Done
> itself (split-brain, METHODOLOGY §4a) from the stakeholder's requirement + the raw repo
> change, and may adopt, reorder, or ignore these steps. Per the write-only-scribe covenant
> Story 3.2 stays 🟡 until the sealed PASS; `governance/RUNBOOK.md` is updated only on the
> recorded verdict.
