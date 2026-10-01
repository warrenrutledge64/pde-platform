# Story 2.2 — LIVE Validation Runbook (turnkey, STATIC BAR only)

> **Story 2.2 = the Hub-side Step Functions promotion state machine
> (RD-003/RD-004/RD-006/RD-009):** `pdlv-promotion-pipeline` sequences
> Dev → Sandbox → Prod, pausing on a **native manual-approval state**
> (`.waitForTaskToken`) before Sandbox and before Prod, each promotion starting the
> Story 2.1 `pdlv-deploy` CodeBuild project (`.sync`). It ships with a least-privilege
> execution role (`pdlv-promotion-pipeline-role`), a `pdlv-promotion-approval` SNS
> topic, and a dedicated `pdlv-` execution log group.
>
> **This is STATIC PROOF only — nothing is deployed.** Story 2.2 is template
> authoring + a static-analysis bar; the live Hub bootstrap deploy is **Story 2.3**,
> and the dummy-payload run that reaches "Awaiting Sandbox Approval" and *pauses* is
> the **Phase 2 gate** (also Story 2.3). No AWS resource is created here. These steps
> run in **Hub CloudShell (641628980935)** / CI purely to lint + scan the template.
>
> **Accounts (reference only — no deploy in 2.2):** Hub `641628980935`; members
> Dev `946509368326`, Sandbox `586917955591`, Prod `466494951534`; management/root
> `467866449172` zero-touch; Pipeline-Forensics `360999005254` is ZTIE's, not PDE.
>
> **Artifact:** `infra/state-machine.yaml` (offline-proven — 48 invariants via
> `python3 infra/validate_state_machine.py`, plus `--self-test`). Story 2.2 stays
> 🟡 until the validator seals a PASS on the static-bar output below.

---

## STEP 0 — Launch pad + get on the right code (Hub CloudShell)

**FREE DISK FIRST (OD-007 — CloudShell is ~1 GB and WILL fill up).** A full disk
silently derailed Story 2.1 twice (`git fetch` failed; a missing file read as a false
"clean"). Clear space *before* cloning and installing:

```bash
df -h ~                               # look for ≥ ~300 MB free
rm -rf ~/.cache ~/.npm /tm/* 2>/dev/null || true
# drop stale clones if present (the big hogs last time): e.g.
#   rm -rf ~/ZTIE-Issues ~/.nvm ~/old-sprint-dirs
df -h ~                               # confirm headroom
```

Use the hardened launch pad from Story 1.2
([`story-1.2-LIVE-RUNBOOK.md`](story-1.2-LIVE-RUNBOOK.md) STEP 0 — the named-script
path) and confirm `LAUNCH-PAD VERIFY: PASS` BEFORE anything else. Then get onto this
story's branch (the 2.2 files are NOT on `main`):

```bash
aws sts get-caller-identity --query Account --output text   # expect 641628980935
cd ~/pde-platform                                           # the cloned repo
git fetch origin
git checkout feature/story-2.2                              # this story's branch
git rev-parse --abbrev-ref HEAD                             # expect: feature/story-2.2
git log --oneline -1                                        # pin this SHA as <HEAD-SHA>

# FAIL-LOUD VERIFY — the target files MUST exist, or STOP (bad checkout / full disk).
# Do NOT use a bare `|| echo CLEAN` anywhere — a missing file must never read as a pass.
for f in infra/state-machine.yaml infra/validate_state_machine.py; do
  if [ ! -s "$f" ]; then echo "VERIFY FAIL: $f missing/empty — STOP (wrong branch or disk)"; exit 1; fi
done
echo "VERIFY PASS: Story 2.2 target files present"
```

> If VERIFY fails, STOP — you are on the wrong branch/commit or out of disk. Do not
> evaluate downstream output from a launch pad on the wrong code (the 2.1 lesson).

## STEP 1 — Offline invariant checker (no network)

```bash
python3 infra/validate_state_machine.py
# expect: validate_state_machine: PASS — all 48 state-machine invariants hold
```

## STEP 2 — Prove the checker actually GUARDS (in memory, NO disk write)

```bash
python3 infra/validate_state_machine.py --self-test; echo "exit=$?"
# expect: PASS — guard flips to FAIL on every sabotage; clean template passes, exit=0
#   (sabotages: pde- prefix regression ×2, over-long Description/E1003, dropped
#    CKV_AWS_158 skip, wildcard action, codebuild:* broadening, approval pause faked
#    with a timer, promotion order broken. In-memory — a full disk cannot invalidate it.)
```

## STEP 3 — Static bar (cfn-lint + Checkov; cfn-guard optional)

```bash
pip install --quiet cfn-lint checkov
cfn-lint infra/state-machine.yaml
checkov -f infra/state-machine.yaml --framework cloudformation
# (optional, if you keep a ruleset)
# cfn-guard validate -d infra/state-machine.yaml -r <your-rules>
```

**PASS criteria (the validator authors the final DoD; this is the operator target):**
- `cfn-lint` returns clean (no errors) — the template + the embedded ASL are well-formed.
- `checkov` reports no failed checks that indicate a real least-privilege / hardening
  regression (CKV_AWS_158 should be the single, justified, SKIPPED Log Group finding;
  triage any informational findings against the DoD).
- The offline checker is `PASS — all 48 invariants hold`.

## STEP 4 — Spot-check the invariants by eye (adversarial)

```bash
# Dev -> Sandbox -> Prod with a NATIVE approval pause before each promotion (not a timer):
grep -nE '"(DeployDev|DeploySandbox|DeployProd|AwaitSandboxApproval|AwaitProdApproval)"' infra/state-machine.yaml
grep -n 'sns:publish.waitForTaskToken' infra/state-machine.yaml        # expect 2 (the two pauses)
grep -n '"taskToken.\$": "\$\$.Task.Token"' infra/state-machine.yaml    # expect 2 (callback token)
grep -n 'codebuild:startBuild.sync' infra/state-machine.yaml           # expect 3 (the three deploys)
grep -n '"Type": "Wait"' infra/state-machine.yaml || echo "no Wait/timer — good (pause is native)"

# Each deploy starts the Story 2.1 pdlv-deploy project:
grep -n '"ProjectName": "${DeployProjectName}"' infra/state-machine.yaml
grep -n 'Default: pdlv-deploy' infra/state-machine.yaml

# No pde- Hub resource name (only pdlv-); exports are pdlv-*
grep -nE '(StateMachineName|RoleName|TopicName|LogGroupName|ManagedPolicyName):' infra/state-machine.yaml
grep -n 'Export:' -A1 infra/state-machine.yaml

# Least privilege — these should return NOTHING (prove absence):
grep -nE 'AdministratorAccess|PowerUserAccess|codebuild:\*|sns:\*' infra/state-machine.yaml || echo "none — good"
grep -nE 'Action:\s*["'\'']\*["'\'']' infra/state-machine.yaml || echo "none — good"
grep -nE 'Resource:\s*["'\'']\*["'\'']' infra/state-machine.yaml   # the only "*" is logs:* delivery-setup (service log-delivery, not a data grant)

# The orchestrator's codebuild power is scoped to the SPECIFIC deploy project ARN:
grep -n 'project/${DeployProjectName}' infra/state-machine.yaml
# ...and it holds NO sts:AssumeRole into a member role (that power stays in the 2.1 CodeBuild role):
grep -nE 'role/\$\{MemberRoleName\}' infra/state-machine.yaml  # appears only in DefinitionSubstitutions (promotion inputs), never as an IAM Resource
```

## STEP 5 — Zero-deploy confirmation (Universal Criteria 1 & 5)

```bash
# Story 2.2 deploys NOTHING. Confirm no pdlv- stack was created by this story:
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName,'pdlv-')].StackName"
# EXPECT: [] — the live Hub deploy is Story 2.3, not 2.2.
```

Record in `governance/RUNBOOK.md` Story 2.2 the validator's sealed one-line verdict:
`pass — state-machine.yaml passes cfn-lint + Checkov + the 48-invariant offline checker; Dev→Sandbox→Prod with native waitForTaskToken approval pauses, each promotion starting the pdlv-deploy project; pdlv- naming, Project=PDE tags, and least-privilege (scoped-ARN codebuild + topic-scoped publish, no wildcard/admin) confirmed; nothing deployed (static proof), <date>, confirmed by <who>`.

## Watch-items

- **Static only — do NOT deploy in 2.2.** The Hub bootstrap deploy + the dummy-payload
  paused-state run are Story 2.3 / the Phase 2 gate.
- **`pde-` in a Hub resource name = a regression** (RD-009). Only `pdlv-` on the Hub;
  the `pde-member-execution-<env>` reference is correct (member accounts, Story 1.1).
- **The pause must be native** — `.waitForTaskToken`, not a `Wait`/timer. The Phase 2
  gate asserts the execution reaches "Awaiting Sandbox Approval" and *pauses* cleanly.
- **No broad orchestrator power** — the state machine's only CodeBuild grant is
  start/stop/describe on the specific `pdlv-deploy` project ARN; the cross-account
  deploy power stays in the 2.1 CodeBuild service role (RD-006).
- **The `logs:*`-resource `Resource: "*"`** in the logging policy is the AWS-required
  log-*delivery* setup (not a data grant); the log-write actions (`CreateLogStream`/
  `PutLogEvents`) are scoped to this state machine's own log-group ARN.
- **Checkov triage:** CKV_AWS_158 on the Log Group is a justified, SKIPPED finding
  (operational control-plane telemetry; AWS-owned-key SSE suffices). Any real
  wildcard/privilege finding is a FAIL.
- **Pipeline-Forensics (`360999005254`) is ZTIE's — never a target.** Management/root
  `467866449172` is zero-touch.
