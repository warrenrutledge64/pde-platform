# Session Brief — Story 2.2: Step Functions state machine (Dev→Sandbox→Prod + approval gates)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Story 2.2 is the second brick of Phase 2 (PDE Control Plane).** Same tier as 2.1
> (tier 3, dep = Phase 1 gate) — no new tier advance; re-confirm the gate at start.

## Story 2.2 — Step Functions state machine (Dev→Sandbox→Prod promotion + manual approval gates)

| Field | Value |
|-------|-------|
| **Phase** | 2 — PDE Control Plane (The Hub) |
| **Build tier** | 3 (depends on the Phase 1 gate; same tier as 2.1 — not a new advance) |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Builds from restore point** | `restore/phase-1-green` (cut at Story 1.2's close) |
| **Session goal** | Author + offline-prove the PDE Step Functions **state machine** (definition + its CloudFormation) orchestrating the Dev → Sandbox → Prod promotion with native **manual-approval paused states**, under the ZTIE-safe **`pdlv-`** naming + `Project=PDE` tagging namespace (RD-009). |

---

### Background & Context

Phase 1 is closed (trust fabric ✅). Story 2.1 landed the two Hub-side **CodeBuild
projects** (`pdlv-lint` + `pdlv-deploy`) + their least-privilege service role, sealed
PASS 2026-10-01 (commit `aa47f85`). Story 2.2 adds the **orchestrator** that drives
them: a Step Functions state machine in Pipeline-Hub `641628980935` that walks an
artifact through Dev → Sandbox → Prod, pausing for a human approval between
environments. The deploy work at each stage is done by invoking the 2.1 `pdlv-deploy`
CodeBuild project (which assumes the Story 1.1 member role and deploys *locally in the
member* — RD-006 orchestrate-and-pull).

### Objective & Value

- **Objective:** a CloudFormation (YAML) template defining the PDE `AWS::StepFunctions::StateMachine`
  (+ its least-privilege execution role) whose definition sequences Dev → Sandbox →
  Prod, with a native **manual-approval paused state** (callback / `.waitForTaskToken`
  or an equivalent paused pattern) before Sandbox and before Prod, each promotion step
  invoking the 2.1 `pdlv-deploy` CodeBuild project — all `pdlv-`-named, `Project=PDE`-
  tagged — offline-proven by a stdlib invariant checker.
- **Why it matters:** this is the control-plane brain. The Phase 2 gate (Story 2.3) is
  a dummy-payload run of *this* state machine reaching the "Awaiting Sandbox Approval"
  paused state with no IAM/config errors — so the approval wiring + least-privilege
  execution role authored here are exactly what that gate proves.

### Scope, Dependencies & Position

- **In scope:** the state-machine CFN template (definition + execution role), the
  Dev→Sandbox→Prod sequence, the manual-approval paused states, the CodeBuild-invoke
  tasks (referencing the 2.1 `pdlv-deploy` project), `pdlv-` naming + `Project=PDE`
  tags, and an offline invariant checker (mirroring `infra/validate_codebuild_projects.py`).
- **Out of scope:** the live Hub bootstrap deploy (Story 2.3 — do NOT deploy in 2.2);
  the CodeBuild projects themselves (Story 2.1, done); the member roles (Story 1.1,
  done); the results-intake data-contract + Hub-signed decision token (later Phase-2/
  product scope, per RD-006); the org-wide CloudTrail (Story 4.1); the management account.
- **Depends on:** the **Phase 1 gate** (1.1 ✅ + 1.2 ✅). _(2.2 reuses the 2.1 deploy
  project by reference but does not require 2.1 ✅ to be authored — however 2.1 **is**
  ✅, so reference its real `pdlv-deploy` name/export.)_
- **Unblocks:** Story 2.3 (bootstrap deploy) needs 2.1 **and** 2.2 both ✅.
- **Roadmap position:** second Phase-2 story; tier 3 (same as 2.1) — no tier advance,
  no phase transition. 2.2 does NOT close Phase 2 (2.3 does, via the Phase 2 gate).

### Approach & Constraints

- **Approach:** (1) author `infra/state-machine.yaml` (CFN YAML) with the
  `AWS::StepFunctions::StateMachine` + a least-privilege execution role; (2) express the
  definition (Amazon States Language) with the Dev→Sandbox→Prod sequence, a manual-
  approval paused state before Sandbox and before Prod, and promotion tasks that start
  the 2.1 `pdlv-deploy` CodeBuild project per environment; (3) enforce `pdlv-` naming +
  `Project=PDE` tags on every resource; (4) write `infra/validate_state_machine.py`
  (stdlib, no network) asserting the invariants + a `--self-test`; (5) hand the USER the
  deploy + static-bar (cfn-lint / cfn-guard / Checkov) commands for the live run.
- **Hard constraints:** CloudFormation (YAML) + Python 3 only — **no Terraform**
  (RD-004); AWS-native + serverless (RD-003); **least privilege / zero-trust** — the
  state-machine execution role is scoped to exactly the tasks it runs (start/describe
  the `pdlv-deploy` CodeBuild project; the approval-callback mechanics), no wildcards,
  no AdministratorAccess (RD-006, Universal Criterion 3); **ZTIE-safe** `pdlv-` namespace
  (RD-009 — `pde-*` is ZTIE's; before any Phase-2 deploy re-run `list-stacks` to confirm
  `pdlv-` names are free), strictly additive + non-destructive (Universal Criterion 5);
  zero-touch management account (Universal Criterion 1).

### Validation Rationale & Compliance Mapping (optional)

- **Rationale:** stands up the control-plane orchestration + human-approval gate under
  least privilege and in a ZTIE-isolated namespace — the exact wiring the Phase 2 gate
  (Story 2.3) proves live.
- **Audit evidence produced:** the CFN template + the offline invariant report; (live)
  cfn-lint / cfn-guard / Checkov output from the USER's run.

### Change & Rollback

- **Change type:** standard (additive, offline authoring; live deploy is Story 2.3).
- **Restore point this builds from:** `restore/phase-1-green`.
- **Backout plan:** 2.2 produces source only — revert via git; no live state is changed
  in 2.2 (the Hub deploy is Story 2.3).

### Definition of Done / Validation Gate

- **Done means:** the state-machine CFN template passes the offline invariant checker
  AND the USER returns raw passing STDOUT from the static bar (cfn-lint, and cfn-guard /
  Checkov as available) confirming the state machine is well-formed, Dev→Sandbox→Prod
  with manual-approval paused states, invokes the 2.1 `pdlv-deploy` project, is
  `pdlv-`-prefixed + `Project=PDE`-tagged, and least-privilege (no wildcard / Admin).
  _(2.2 is template authoring + static proof; the live deploy + the dummy-payload
  paused-state run are Story 2.3 / the Phase 2 gate — do not deploy in 2.2.)_
- **Validated by:** an INDEPENDENT validator (not the builder) via
  `DOCS/session-briefs/story-2.2-VALIDATOR-HANDOVER.md`; the USER runs the live static
  bar and pastes raw output; the executor records the sealed verdict.
- **Validation Result:** `pending`.
- **On pass:** record it, flip 2.2 → ✅. _(Does NOT close Phase 2 — 2.3 remains; the
  Phase 2 gate is the dummy-payload Step Functions run in Story 2.3.)_
- **On fail:** stays 🟡; fix and re-run.
- **Advancement gate:** 2.3 cannot begin until 2.1 **and** 2.2 are ✅.

### Risks & Watch-Items

- **ZTIE collision (RD-009):** every PDE resource uses `pdlv-`, never `pde-` (18 ZTIE
  `pde-*` stacks exist in the Hub). Re-run `list-stacks … contains(StackName,'pdlv-')`
  before any Phase-2 deploy to confirm the chosen names are free.
- **Least-privilege execution role:** scope the state-machine role to exactly
  `codebuild:StartBuild`/`BatchGetBuilds` on the specific `pdlv-deploy` project ARN (and
  the approval-callback actions) — NOT `codebuild:*`, NOT a broad policy. The cross-
  account deploy power stays in the 2.1 CodeBuild service role (which assumes the member
  roles); 2.2's role only *starts* that project.
- **Manual-approval pattern:** use a native paused state (callback token
  `.waitForTaskToken`, or an equivalent human-approval pause) — the Phase 2 gate asserts
  the execution reaches "Awaiting Sandbox Approval" and *pauses* cleanly. Don't fake the
  pause with a wait/timer.
- **Offline checker hygiene:** the checker strips `#` comments — keep asserted
  invariants testing the template, not prose. Keep forbidden literals (`467866449172`,
  `AdministratorAccess`) OUT of the top `Description:` and resource `Description:` prose,
  or they trip the "absence" checks (learned in 2.1).

### Lessons Learned / Carry-Forward *(authored at the end of Story 2.1 — actual lessons)*

- **The static bar catches what the offline checker can't — then fold it back in.** 2.1's
  Attempt-1 sealed **FAIL** on two real defects the stdlib checker didn't test: **cfn-lint
  E1003** (the top `Description` was 1311 B > CFN's 1024-byte hard limit) and **checkov
  CKV_AWS_158** (CloudWatch Log Groups lacked KMS). FIX pattern that passed: shortened the
  Description to ~624 B (fuller rationale moved to resource comments + the brief), and added
  a **justified inline `# checkov:skip=CKV_AWS_158:`** on each log group (operational build
  logs are non-sensitive control-plane output; AWS-owned-key SSE suffices; a CMK is
  unjustified overhead). **Durable fix:** I added two NEW offline invariants mirroring both
  findings (Description ≤ 1024 B; both suppressions present) so this class is caught offline
  next time. **For 2.2:** pre-empt both — keep the state-machine template `Description` short
  (< 1024 B; measure it), and if any resource (e.g. a Logs group for SFN logging) trips a
  checkov KMS/encryption check, decide CMK-vs-justified-skip up front and encode an invariant
  for it.
- **Make the checker's guard provable WITHOUT writing a file.** 2.1's on-disk `sed` sabotage
  test was invalidated TWICE by a full CloudShell disk. I replaced it with an in-memory
  `python3 infra/validate_codebuild_projects.py --self-test` that sabotages the template in
  RAM and asserts each guard flips to FAIL. **For 2.2:** build the checker with the same
  `--self-test` shape (pure `run_checks(text)` fn + in-memory sabotages) from the start.
- **Never let a missing file read as a pass.** The validator caught a `grep … || echo CLEAN`
  fallback that printed "clean" when the file was simply absent (bad checkout / disk). The
  LIVE-RUNBOOK now guards file-existence and distinguishes `grep rc=1` (truly absent, good)
  from `rc>1` (file missing — NOT a pass). **For 2.2:** reuse that guarded-grep pattern in
  the runbook; add a fail-loud VERIFY after checkout before any lint/grep.
- **CloudShell is 1 GB and WILL fill up (OD-007).** Disk exhaustion blocked 2.1 across two
  attempts (invalidated the sabotage, then blocked `git fetch` entirely). The big hogs were
  stale clones (`ZTIE-Issues` ~481 MB, `.nvm` ~237 MB, old sprint dirs). **For 2.2:** FREE
  DISK FIRST — `df -h ~`, clear `~/.cache`, drop stale clones, aim for ≥ 300 MB free before
  cloning + `pip install`. `pip install cfn-lint checkov` needs real headroom (checkov's dep
  tree is large); cfn-lint alone is small and catches E1003. If 1 GB keeps biting, run the
  static bar in CI (the AWS-native direction) — OD-007's clear-by.
- **Independent validation + the full handover set.** 2.1 shipped a `-VALIDATOR-HANDOVER.md`
  (the DoD-authoring packet) + a `-LIVE-RUNBOOK.md` (turnkey operator steps). The builder does
  NOT author the DoD or seal the verdict (METHODOLOGY §4a). **For 2.2:** author BOTH handover
  docs alongside the brief/prompt; put the `[[requirement]]` blank for the stakeholder; point
  the validator at the branch with pinned-SHA fetch commands.
- **Paired-commit + fix-after-merge guard.** 2.1's work PR (#19) merged BEFORE validation;
  the fix for the sealed FAIL then had to land on a follow-up branch (`fix/story-2.1-static-bar`,
  PR #20), and the close-out branch was cut from that validated commit (`aa47f85`) so the ✅
  flip rides the validated code. **For 2.2:** keep the status flip a separate small commit;
  if the work PR merges early, cut the close-out/validate branch from the exact commit that
  passed, and confirm every fix commit is on the base branch.
- **Current true state at handoff:** Story 1.1 ✅, 1.2 ✅ (Phase 1 CLOSED, `restore/phase-1-green`),
  **2.1 ✅** (sealed PASS 2026-10-01, `aa47f85`; VD-5 CLEARED). Validation Debt Register
  **empty**, gate **DISARMED** — 2.2 is properly unblocked (tier 3, same tier as 2.1; dep =
  Phase 1 gate ✅). The 2.1 `pdlv-deploy` CodeBuild project + its exports (`pdlv-codebuild-deploy-project-name`,
  `pdlv-codebuild-service-role-arn`) are the real references 2.2's state machine should start.
- **Account topology (authoritative):** Hub `641628980935` (where SFN + CodeBuild run); members
  Dev `946509368326`, Sandbox `586917955591`, Prod `466494951534`; management/root `467866449172`
  zero-touch; Pipeline-Forensics `360999005254` is **ZTIE's**, not PDE.
- **The committed Phase-1 gate script is still Phase 2's VD-3b.** The live Hub→member
  `sts:AssumeRole` (`python3 scripts/phase1_gate.py`) runs once `pde-hub-orchestrator` exists.
  If 2.2/2.3 create that Hub orchestrator role, run the committed script to clear VD-3b.
- **User notes:** _(open for the user)_
