# Story 2.3 — LIVE Deploy + Phase 2 Gate Runbook (turnkey, FIRST LIVE DEPLOY)

> **Story 2.3 = the FIRST live-deploy story and the Phase 2 gate (CLOSES Phase 2).**
> It bootstraps the already-authored, sealed-PASS Phase-2 templates into
> **Pipeline-Hub `641628980935`** via CLI, verifies the landed IAM is least-privilege,
> then runs the **Phase 2 gate**: a **dummy-payload** execution of the
> `pdlv-promotion-pipeline` Step Functions state machine reaches the
> **"Awaiting Sandbox Approval"** paused state **without IAM/config errors**.
>
> **This runbook is the operator execution surface.** The INDEPENDENT validator
> (`story-2.3-VALIDATOR-HANDOVER.md`) authors the Definition of Done + seals the
> verdict; this runbook is how you (the operator) produce the raw evidence. The
> builder does NOT author the acceptance criteria.
>
> **Target (reference only — the operator trusts `aws sts get-caller-identity`, not a
> label):** Pipeline-Hub `641628980935`, region `us-east-1`. Members: Dev
> `946509368326`, Sandbox `586917955591`, Prod `466494951534`. Management/root
> `467866449172` is **zero-touch**. Pipeline-Forensics `360999005254` is **ZTIE's**,
> never a target.
>
> **Artifacts deployed (both sealed PASS, offline + CI-green):**
> `infra/codebuild-projects.yaml` (`pdlv-lint` + `pdlv-deploy` + the
> `pdlv-codebuild-service-role`; Story 2.1 ✅ `aa47f85`) and
> `infra/state-machine.yaml` (`pdlv-promotion-pipeline` + `pdlv-promotion-pipeline-role`
> + `pdlv-promotion-approval` SNS topic + `pdlv-` log group; Story 2.2 ✅ CI
> #36943324686 `4aa3e5a`). Story 2.3 stays 🟡 until the validator seals a PASS on the
> live output below.

---

> ### ⚠️ BEFORE YOU START — the one real risk of this gate (read this first)
>
> The state machine's **first** state is `DeployDev` — a `codebuild:startBuild.sync`
> on the `pdlv-deploy` project — and ONLY after it completes does the execution reach
> **`AwaitSandboxApproval`** (the pause the gate asserts). The `pdlv-deploy` buildspec
> begins with `aws sts assume-role` into `pde-member-execution-dev`. So a naive dummy
> run can **fail at `DeployDev`** (and never reach the pause) if the Dev member role
> is absent or does not yet trust the caller — the Phase-1 trust fabric currently
> trusts `pde-hub-orchestrator` (a Hub role that does **not exist yet** — that is the
> deferred **VD-3b**), **not** the `pdlv-codebuild-service-role` that `pdlv-deploy`
> runs as.
>
> The Phase 2 gate asks only that the execution **reaches "Awaiting Sandbox Approval"
> without IAM/config errors** — it does NOT require a real cross-account deploy (that
> is Phase 3). STEP 5 therefore gives you **two honest routes** to a dummy-safe
> `DeployDev` so the run can reach the pause; the **validator decides** which is
> acceptable for the gate. Do not fabricate a pause — if `DeployDev` fails, the gate
> has NOT passed; capture the failure verbatim and hand it back.

---

## STEP 0 — Launch pad + get on the right code (Hub CloudShell)

**FREE DISK FIRST (OD-007 — CloudShell is ~1 GB and WILL fill up).** A full disk
silently derailed Story 2.1 twice (`git fetch` failed; a missing file read as a false
"clean"). Clear space *before* cloning:

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
df -h ~                               # look for >= ~300 MB free
rm -rf ~/.cache ~/.npm /tmp/* 2>/dev/null || true
# drop stale clones if present (the big hogs last time): e.g.
#   rm -rf ~/ZTIE-Issues ~/.nvm ~/old-sprint-dirs
df -h ~                               # confirm headroom
```

Confirm you are in the Hub, then stand up + VERIFY the launch pad with the hardened
named script from Story 1.2 (confirm `LAUNCH-PAD VERIFY: PASS` BEFORE anything else):

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935
```

> **AUTHORITATIVE SOURCE — clone THIS repo, nothing else (OD-008):** the PDE repo is
> **GitHub `warrenrutledge64/pde-platform`**, cloned token-auth. It is **NOT** a
> CodeCommit repo and is **NOT** named `pde-hub`. A clone of
> `https://git-codecommit.us-east-1.amazonaws.com/v1/repos/pde-hub/` returns
> `repository not found` and every downstream step cascades into "file not found".
>
> **Clone with a QUOTED URL and a REAL token — never the literal `<TOKEN>` (OD-008,
> attempt 6):** bash reads a bare leading `<` as an input redirection, so an
> un-substituted `<TOKEN>` makes the clone silently never run.

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# If the repo is not already on disk, clone the CORRECT repo (replace REAL_PAT with a
# real token; the whole URL is quoted). NOT CodeCommit, NOT pde-hub:
#   git clone "https://REAL_PAT@github.com/warrenrutledge64/pde-platform.git"
cd ~/pde-platform
git remote -v                              # expect github.com/warrenrutledge64/pde-platform (NOT codecommit / pde-hub)
git fetch origin
git checkout feature/story-2.3             # this story's branch
git reset --hard origin/feature/story-2.3  # pin EXACTLY the remote tip (no stale local commit)
git rev-parse --abbrev-ref HEAD            # expect: feature/story-2.3
git log --oneline -1                       # pin this SHA as <HEAD-SHA> for the validator

# FAIL-LOUD VERIFY — the target files MUST exist, or STOP (bad checkout / full disk).
# Never use a bare `|| echo CLEAN` anywhere — a missing file must never read as a pass.
for f in infra/codebuild-projects.yaml infra/state-machine.yaml; do
  if [ ! -s "$f" ]; then echo "VERIFY FAIL: $f missing/empty — STOP (wrong branch or disk)"; exit 1; fi
done
echo "VERIFY PASS: Story 2.3 target templates present"
```

> If VERIFY fails, STOP — you are on the wrong commit/branch or out of disk. Do not
> deploy from a launch pad on stale/wrong code (the standing deploy-gap lesson: a green
> `CREATE_COMPLETE` on a stale checkout silently ships the wrong template).

## STEP 1 — Re-confirm the `pdlv-` names are FREE in the Hub (RD-009, ZTIE-safe)

ZTIE owns **18 `pde-*` stacks** in this Hub. PDE deploys ONLY `pdlv-`-named stacks.
Confirm nothing named `pdlv-*` already exists (a non-empty list means a prior partial
deploy — investigate before re-deploying), and confirm the `pde-*` co-occupants are
present (so you know you are in the right account) but **never a target**:

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935

# PDE's namespace — EXPECT [] (empty) on a clean first deploy:
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE ROLLBACK_COMPLETE \
                        CREATE_IN_PROGRESS UPDATE_IN_PROGRESS \
  --query "StackSummaries[?contains(StackName,'pdlv-')].StackName" --output json

# ZTIE's namespace — these co-occupants exist and are OFF-LIMITS (do not touch):
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "length(StackSummaries[?contains(StackName,'pde-')])" --output text
```

> If the `pdlv-` list is non-empty, STOP and reconcile (a leftover from an earlier
> attempt) before deploying — do not blindly re-deploy over it. See STEP 1a.

## STEP 1a — Delete any DEAD stack first (MANDATORY on a re-attempt — VD-7 / OD-009)

> **A stack in `ROLLBACK_COMPLETE` CANNOT be updated in place.** If a prior deploy
> attempt failed (e.g. the attempt-1 `CreateStateMachine` managed-rule `AccessDenied`),
> CloudFormation leaves the stack in `ROLLBACK_COMPLETE`. A re-run of
> `cloudformation deploy` against it does NOT redeploy — it fails on the dead stack, no
> resources are provisioned, and the downstream least-privilege audit + gate run then
> fail with "resource/parameter not found" errors that LOOK like a deliverable defect
> but are actually just the dead stack blocking everything. This is exactly what the
> attempt-2 re-validation hit (VD-7). **Delete the dead stack before re-deploying.**

> **⚠️ NAME-AGNOSTIC — delete the dead stack by WHATEVER it is named (attempt-4 lesson,
> VD-7).** Attempts 2-4 kept failing on a stack the validator reported as
> **`pdlv-promotion-pipeline-stack`**, but the manual delete targeted `pdlv-state-machine`
> (this runbook's name) — a DIFFERENT name, so the dead stack was never removed. Do NOT
> assume the stack name; SWEEP the whole `pdlv-` namespace for any dead stack and delete
> each by its real name. (Whatever the deploy script named it, it starts with `pdlv-`.)

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935

# Find EVERY pdlv- stack in a dead/un-updatable state — by whatever name it has:
DEAD=$(aws cloudformation list-stacks \
  --stack-status-filter ROLLBACK_COMPLETE ROLLBACK_FAILED CREATE_FAILED \
                        DELETE_FAILED UPDATE_ROLLBACK_FAILED UPDATE_ROLLBACK_COMPLETE \
                        REVIEW_IN_PROGRESS \
  --query "StackSummaries[?contains(StackName,'pdlv-')].StackName" --output text)
echo "dead pdlv- stacks: ${DEAD:-<none>}"

# Delete each dead pdlv- stack by its REAL name and WAIT (only pdlv-*, never pde-*/ZTIE):
for S in $DEAD; do
  case "$S" in
    pdlv-*) echo "deleting dead stack $S…"
            aws cloudformation delete-stack --stack-name "$S"
            aws cloudformation wait stack-delete-complete --stack-name "$S"
            echo "  $S deleted." ;;
    *)      echo "REFUSING to touch non-pdlv stack $S" ;;
  esac
done

# Re-confirm the pdlv- namespace has NO dead stack left before deploying the FIXED template:
aws cloudformation list-stacks \
  --stack-status-filter ROLLBACK_COMPLETE ROLLBACK_FAILED CREATE_FAILED DELETE_FAILED \
                        UPDATE_ROLLBACK_FAILED UPDATE_ROLLBACK_COMPLETE REVIEW_IN_PROGRESS \
  --query "StackSummaries[?contains(StackName,'pdlv-')].StackName" --output json
# EXPECT [] — then proceed to STEP 2.
```

> **Only ever delete `pdlv-`-named stacks.** Never touch a `pde-*` stack (ZTIE's, 18 of
> them) or anything in management `467866449172` / Pipeline-Forensics `360999005254`.
> Deleting a dead `pdlv-` stack is non-destructive (it provisioned nothing — it rolled
> back) and keeps the deploy strictly additive.

## STEP 2 — Deploy the CodeBuild stack FIRST (`pdlv-codebuild`)

Deploy order matters: the state machine starts the `pdlv-deploy` project, so the
CodeBuild projects should exist first. (The state-machine template takes the project
name as a **parameter**, default `pdlv-deploy`, so it will *synthesize* without the
import — but for the dummy run to resolve the project, deploy CodeBuild first.)

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935

# --- SELF-HEALING pre-deploy guard (CANNOT be skipped — attempts 2 & 3 failed because
#     the dead ROLLBACK_COMPLETE stack was never deleted; VD-7 / OD-009). Define once,
#     then call before each deploy. It deletes ONLY a pdlv- stack that is in a dead,
#     un-updatable state (ROLLBACK_COMPLETE / *_FAILED / DELETE_FAILED) and WAITS. ---
ensure_deployable () {
  local S="$1"
  case "$S" in pdlv-*) : ;; *) echo "REFUSING: $S is not a pdlv- stack — STOP"; return 1 ;; esac
  local ST
  ST=$(aws cloudformation describe-stacks --stack-name "$S" \
        --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "ABSENT")
  echo "$S => $ST"
  case "$ST" in
    ROLLBACK_COMPLETE|ROLLBACK_FAILED|CREATE_FAILED|DELETE_FAILED|UPDATE_ROLLBACK_FAILED|REVIEW_IN_PROGRESS)
      echo "  dead stack — deleting before deploy (self-heal)…"
      aws cloudformation delete-stack --stack-name "$S"
      aws cloudformation wait stack-delete-complete --stack-name "$S"
      echo "  $S deleted; ready for a clean create." ;;
    *_IN_PROGRESS)
      echo "  $S is $ST — WAIT for it to settle, do not deploy over an in-progress stack"; return 1 ;;
    ABSENT|CREATE_COMPLETE|UPDATE_COMPLETE) : ;;  # fine to deploy
    *) echo "  $S is $ST — inspect before deploying"; return 1 ;;
  esac
}

ensure_deployable pdlv-codebuild || { echo "guard stop"; }

aws cloudformation deploy \
  --template-file infra/codebuild-projects.yaml \
  --stack-name pdlv-codebuild \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=2.3 Component=codebuild \
  --no-fail-on-empty-changeset

# Confirm the stack reached CREATE_COMPLETE / UPDATE_COMPLETE (not ROLLBACK):
aws cloudformation describe-stacks --stack-name pdlv-codebuild \
  --query "Stacks[0].StackStatus" --output text

# Capture the outputs (names the state machine + the gate run will reference):
aws cloudformation describe-stacks --stack-name pdlv-codebuild \
  --query "Stacks[0].Outputs" --output table
```

## STEP 3 — Deploy the state-machine stack (`pdlv-promotion-pipeline-stack`)

`ExternalId` is a `NoEcho` secret parameter — pass the **real** shared secret that
matches the Story 1.1 member-role trust (do NOT commit it; type it at deploy time):

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935

# SELF-HEALING guard again (this is the stack that was stuck in ROLLBACK_COMPLETE on
# attempts 1-3). If you are in a FRESH shell that did not run STEP 2, re-paste the
# ensure_deployable () {...} definition from STEP 2 first, then:
ensure_deployable pdlv-promotion-pipeline-stack || { echo "guard stop"; }

aws cloudformation deploy \
  --template-file infra/state-machine.yaml \
  --stack-name pdlv-promotion-pipeline-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ExternalId="<THE-REAL-SHARED-EXTERNAL-ID>" \
  --tags Project=PDE Story=2.3 Component=state-machine \
  --no-fail-on-empty-changeset

aws cloudformation describe-stacks --stack-name pdlv-promotion-pipeline-stack \
  --query "Stacks[0].StackStatus" --output text

# Capture outputs — PIN the state-machine ARN for the gate run:
aws cloudformation describe-stacks --stack-name pdlv-promotion-pipeline-stack \
  --query "Stacks[0].Outputs" --output table
```

## STEP 3a — If the deploy ROLLED BACK, capture the FAILURE REASON (MANDATORY — VD-7)

> **A `ROLLBACK_COMPLETE`/`CREATE_FAILED` is NEVER acceptable as "it rolled back."**
> Attempt 5 rolled back on a clean slate with no cause recorded, which cost a cycle —
> the fix for any rollback requires the CloudFormation **first-failure event**, not the
> symptom. If STEP 3's status is anything other than `CREATE_COMPLETE`/`UPDATE_COMPLETE`,
> run this and paste the raw output to the validator/builder BEFORE deleting the stack.

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# The FIRST resource that failed + the EXACT reason (this is the diagnostic line):
aws cloudformation describe-stack-events --stack-name pdlv-promotion-pipeline-stack \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[Timestamp,LogicalResourceId,ResourceStatusReason]" \
  --output table

# Full ordered event trail (oldest first) if the above is not enough:
aws cloudformation describe-stack-events --stack-name pdlv-promotion-pipeline-stack \
  --query "reverse(StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason])" \
  --output table
```

> **To preserve the failed resource for inspection** (CloudFormation auto-deletes it on
> rollback), re-deploy the state-machine stack with rollback DISABLED so the failed
> resource + its reason survive — then read the events above, then delete:
>
> ```bash
> # (after STEP 1a has cleared any dead stack) create with on-failure DO_NOTHING:
> aws cloudformation create-stack \
>   --stack-name pdlv-promotion-pipeline-stack \
>   --template-body file://infra/state-machine.yaml \
>   --capabilities CAPABILITY_NAMED_IAM \
>   --on-failure DO_NOTHING \
>   --parameters ParameterKey=ExternalId,ParameterValue="<THE-REAL-SHARED-EXTERNAL-ID>" \
>   --tags Key=Project,Value=PDE Key=Story,Value=2.3 Key=Component,Value=state-machine
> aws cloudformation wait stack-create-complete --stack-name pdlv-promotion-pipeline-stack || true
> aws cloudformation describe-stack-events --stack-name pdlv-promotion-pipeline-stack \
>   --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason]" \
>   --output table
> ```
>
> **Do NOT patch the template blindly on "it rolled back."** The builder fixes
> fix-then-validate-once ONLY against the captured `ResourceStatusReason` (that is how
> the attempt-1 managed-rule defect was fixed from its exact error string). Hand the
> reason back; a template edit without it risks another wasted cycle.

## STEP 4 — Verify the REAL deployed resources (never trust the green line)

> Standing lesson (doubly relevant on the first live deploy): a `✅ CREATE_COMPLETE`
> can still ship the wrong thing. Describe the LIVE resources and confirm names, tags,
> and **least privilege** are actually present.

### 4a — Names + `Project=PDE` tags are correct (`pdlv-`, not `pde-`)

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# The state machine, both CodeBuild projects, the SNS topic, and both exec roles exist, pdlv--named:
aws stepfunctions list-state-machines \
  --query "stateMachines[?contains(name,'pdlv-')].name" --output json
aws codebuild list-projects --query "projects[?contains(@,'pdlv-')]" --output json
aws sns list-topics --query "Topics[?contains(TopicArn,'pdlv-')].TopicArn" --output json
aws iam list-roles --query "Roles[?contains(RoleName,'pdlv-')].RoleName" --output json

# NONE of PDE's own resources should be pde--named (that is ZTIE's). EXPECT [] here:
aws stepfunctions list-state-machines \
  --query "stateMachines[?starts_with(name,'pdlv-')==\`false\` && contains(name,'pde-')].name" --output json

# Project=PDE tag landed on the state machine + the exec role:
SM_ARN=$(aws cloudformation describe-stacks --stack-name pdlv-promotion-pipeline-stack \
  --query "Stacks[0].Outputs[?OutputKey=='PromotionStateMachineArn'].OutputValue" --output text)
echo "state machine: $SM_ARN"
aws stepfunctions list-tags-for-resource --resource-arn "$SM_ARN" --output table
aws iam list-role-tags --role-name pdlv-promotion-pipeline-role --output table
aws iam list-role-tags --role-name pdlv-codebuild-service-role --output table
```

### 4b — The landed IAM is least-privilege (no wildcard, no admin, scoped ARNs)

Dump the live attached policies for BOTH execution roles and read them adversarially:

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# --- State-machine execution role: only starts the SPECIFIC pdlv-deploy project,
#     publishes to the approval topic, writes its own logs; NO cross-account assume. ---
for RN in pdlv-promotion-pipeline-role pdlv-codebuild-service-role; do
  echo "===== $RN ====="
  aws iam list-attached-role-policies --role-name "$RN" --output table
  for PA in $(aws iam list-attached-role-policies --role-name "$RN" \
               --query "AttachedPolicies[].PolicyArn" --output text); do
    VID=$(aws iam get-policy --policy-arn "$PA" --query "Policy.DefaultVersionId" --output text)
    echo "----- policy $PA ($VID) -----"
    aws iam get-policy-version --policy-arn "$PA" --version-id "$VID" \
      --query "PolicyVersion.Document" --output json
  done
  # Trust policy (who may assume it):
  aws iam get-role --role-name "$RN" --query "Role.AssumeRolePolicyDocument" --output json
done
```

**Adversarial checks the validator will apply to the JSON above (prove ABSENCE):**
- No `"Action": "*"`, no `AdministratorAccess`/`PowerUserAccess`, no `codebuild:*`,
  no `sns:*`, no `iam:*`.
- The state-machine role's only CodeBuild grant is `StartBuild/StopBuild/BatchGetBuilds`
  on the **specific** `project/pdlv-deploy` ARN (not `*`); its only `sns:Publish` target
  is the `pdlv-promotion-approval` topic ARN (not `*`); its `logs:*` `Resource: "*"`
  entries are the AWS-required log-*delivery* setup only (write actions are scoped to
  its own log group ARN).
- The state-machine role's EventBridge grant (the `codebuild:startBuild.sync` managed
  rule) is the complete lifecycle set `events:PutRule/PutTargets/DescribeRule/DeleteRule/
  RemoveTargets` **scoped to the `rule/StepFunctionsGetEventsFor*` rule-name family**
  in this account+region — NOT `events:*`, NOT `Resource "*"`. _(Attempt-1 FAIL class,
  VD-7: a one-literal-rule scope + missing `DeleteRule`/`RemoveTargets` denied
  `CreateStateMachine` with "not authorized to create managed-rule" and rolled the
  stack back. Confirm the deployed policy shows the family-scoped, complete set.)_
- The state-machine role holds **NO** `sts:AssumeRole` into any member role (that power
  lives ONLY in `pdlv-codebuild-service-role`, scoped to the three named
  `pde-member-execution-<env>` ARNs — RD-006).
- The CodeBuild service role trusts ONLY `codebuild.amazonaws.com` with the
  `aws:SourceAccount` condition; the SFN role trusts ONLY `states.amazonaws.com`.

## STEP 5 — The Phase 2 GATE: dummy-payload run reaches "Awaiting Sandbox Approval"

> **The gate assertion:** a dummy execution reaches the `AwaitSandboxApproval` paused
> state (`sns:publish.waitForTaskToken`) **without IAM/config errors**, and PAUSES
> (does NOT auto-advance — that would mean the approval was not a real callback pause).
> Do **not** approve / send the task token in 2.3 (that is Phase 3).
>
> **Because `DeployDev` runs BEFORE the pause** (see the risk banner at the top), pick
> ONE dummy-safe route so `DeployDev` succeeds trivially and the execution advances to
> the pause. **The validator decides which route is acceptable for the gate** — present
> the raw output of whichever you run; if `DeployDev` fails, the gate has NOT passed.

> **DUMMY-SAFE ROUTE (decided 2026-10-02, after attempt 8): a SEPARATE gate-probe state
> machine — `pdlv-gate-probe`.** Attempt 8 proved the real `pdlv-promotion-pipeline`
> deploys clean + passes least-privilege, but a dummy run through it hard-fails at
> `DeployDev` (`sts:assume-role` into `pde-member-execution-dev`, whose trust targets the
> Phase-3 `pde-hub-orchestrator`, not the CodeBuild role). Rather than weaken the real
> pipeline with an input-driven bypass (a vulnerability vector) or a temporary member
> trust (a standing cross-account hole), the template ships a SEPARATE, structurally
> non-promoting probe: it `StartAt`s the `AwaitSandboxApproval` pause and then terminates
> in `Fail` — it has NO deploy/CodeBuild state and its role has ONLY `sns:Publish` + its
> own logs. The PRODUCTION pipeline carries NO bypass branch (zero added attack surface).
> Proving the probe reaches the pause IS the Phase 2 gate.

Start the **gate probe** (not the production pipeline) and observe:

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935

PROBE_ARN=$(aws cloudformation describe-stacks --stack-name pdlv-promotion-pipeline-stack \
  --query "Stacks[0].Outputs[?OutputKey=='GateProbeStateMachineArn'].OutputValue" --output text)
echo "gate probe: $PROBE_ARN"

EXEC_ARN=$(aws stepfunctions start-execution \
  --state-machine-arn "$PROBE_ARN" \
  --name "phase2-gate-probe-$(date +%s)" \
  --input '{"probe":true,"note":"phase-2 gate probe — reach the pause, then abort"}' \
  --query executionArn --output text)
echo "execution: $EXEC_ARN"

# The probe publishes to the approval topic and WAITS on the task token immediately.
sleep 15
aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" \
  --query "{status:status,startDate:startDate,stopDate:stopDate}" --output table

# The authoritative proof — the history shows the execution ENTERED AwaitSandboxApproval
# and is WAITING on the task token (no States.*/IAM error, no DeployDev at all):
aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" \
  --max-results 100 --reverse-order \
  --query "events[].{id:id,type:type,name:stateEnteredEventDetails.name}" --output table
```

**What a PASS looks like in the raw output (the validator confirms):**
- `describe-execution` `status` is **`RUNNING`** (NOT `SUCCEEDED`/`FAILED`/`TIMED_OUT`/
  `ABORTED`) — the probe is paused at the approval, waiting on the task token.
- `get-execution-history` shows the execution **ENTERED `AwaitSandboxApproval`** on an
  `sns:publish.waitForTaskToken` `TaskScheduled`/`TaskSubmitted`, with **no** following
  `TaskFailed`/`ExecutionFailed`/`ExecutionAborted` and **no** `States.*`/access-denied
  error — and there is **no `DeployDev`/CodeBuild event at all** (the probe can't deploy).
- The probe NEVER reaches `Succeed`; its only terminal is the `Fail`
  (`GateProbeReachedPause`) that follows a human response — which the gate run does NOT do.

> **If the probe execution FAILS before the pause** (any `States.*`/IAM error on the
> `sns:publish.waitForTaskToken`), the gate has NOT passed — capture the
> `get-execution-history` events verbatim and hand them to the validator; do not retry
> blindly or fabricate a pause.
>
> **Note on the production pipeline:** you may ALSO confirm the real `pdlv-promotion-pipeline`
> exists and is least-privilege (STEP 4) — but do NOT dummy-run it (its `DeployDev` requires
> the Phase-3 member trust / VD-3b). The gate is proven via the probe.

### 5a — Leave it paused; do NOT approve (Phase 3)

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# Confirm it is STILL paused a moment later (did not auto-advance):
aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" \
  --query status --output text    # expect: RUNNING
# Do NOT SendTaskSuccess/SendTaskFailure. Optionally stop the dummy run after the proof:
# aws stepfunctions stop-execution --execution-arn "$EXEC_ARN" --cause "phase-2 gate proof complete"
```

## STEP 6 — Hand the raw output to the validator

Paste the RAW output of STEP 1 (names free), STEP 2–3 (deploy status + outputs),
STEP 4 (names/tags + the least-privilege policy JSON), and STEP 5 (describe-execution +
get-execution-history showing the pause) to the INDEPENDENT validator per
[`story-2.3-VALIDATOR-HANDOVER.md`](story-2.3-VALIDATOR-HANDOVER.md). The validator
authors the Definition of Done and seals PASS/FAIL/INCONCLUSIVE. **Do not summarize —
paste the raw output.**

On the validator's sealed verdict, the **executor** records it in
`governance/RUNBOOK.md` Story 2.3 and — **only on PASS** — flips 2.3 🟡 → ✅, flips the
Phase 2 Progress-Summary row ✅, cuts `restore/phase-2-green` + its state manifest, adds
the deployed resources to BOM §2, confirms the merge-order guard reads **DISARMED** at
head, and authors Story 3.1's warm handoff. **This CLOSES Phase 2.**

## Watch-items

- **Prove the gate via the SEPARATE `pdlv-gate-probe`, NOT the production pipeline.** A
  dummy run through the real `pdlv-promotion-pipeline` hard-fails at `DeployDev`
  (`sts:assume-role` into the member role, whose trust is Phase-3/VD-3b). The probe is a
  separate, structurally non-promoting state machine (no deploy state; role has only
  publish + logs) that reaches the pause with no cross-account dependency. The production
  pipeline deliberately has NO bypass branch (zero added attack surface).
- **The pause is the point.** The execution must stay `RUNNING` and WAIT on the token —
  it must NOT auto-advance (that would mean the approval is not a real
  `.waitForTaskToken` pause). Never send the task token in 2.3.
- **Verify the real resource, not the green deploy line.** After `cloudformation deploy`,
  describe the live state machine + both roles and confirm `pdlv-` names, `Project=PDE`
  tags, the `waitForTaskToken` approval states, and least privilege are actually present.
- **ZTIE-safe (RD-009).** Deploy ONLY `pdlv-`-named stacks. `pde-*` (18 stacks) is
  ZTIE's — never a target. Re-check `list-stacks … contains(StackName,'pdlv-')` is empty
  before the first deploy.
- **Zero-touch management/root `467866449172`.** Nothing in 2.3 touches it.
  Pipeline-Forensics `360999005254` is ZTIE's — never a target.
- **Additive + reversible.** The deploy is net-new `pdlv-` stacks. Back out with
  `aws cloudformation delete-stack` on `pdlv-promotion-pipeline-stack` then
  `pdlv-codebuild` (importers before exporters) with no effect on ZTIE's `pde-*` or on
  members.
- **VD-3b opportunity.** If this story stands up a `pde-hub-orchestrator` Hub role (it
  does not, by default — the deploy project runs as `pdlv-codebuild-service-role`),
  run `python3 scripts/phase1_gate.py` live to clear the deferred VD-3b. Otherwise
  VD-3b stays carried into Phase 3.
- **CloudShell is ~1 GB (OD-007).** Free disk first; prefer the launch-pad bootstrap.
