# Session Brief — Story 2.3: Bootstrap the PDE infra into the Hub via CLI (CLOSES Phase 2)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Story 2.3 is the THIRD and FINAL brick of Phase 2 (PDE Control Plane).** It is the
> **first live-deploy story** (2.1 + 2.2 were offline authoring) and it **closes
> Phase 2** via the Phase 2 gate. Build tier 4 — a NEW tier advance over 2.1/2.2
> (tier 3); re-confirm the full dependency set at start.

## Story 2.3 — Bootstrap the net-new PDE infra into the Hub via CLI, tightly-scoped IAM

| Field | Value |
|-------|-------|
| **Phase** | 2 — PDE Control Plane (The Hub) |
| **Build tier** | 4 (depends on 2.1 ✅ **and** 2.2 ✅ — a tier advance over tier 3) |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Builds from restore point** | `restore/phase-1-green` (Phase 1 close); Phase 2 has no restore point yet — **this story cuts `restore/phase-2-green`** on its gate pass |
| **Session goal** | Bootstrap-deploy the already-authored PDE control plane (Story 2.1 CodeBuild projects + Story 2.2 Step Functions state machine) into **Pipeline-Hub `641628980935`** via CLI, with tightly-scoped IAM, strictly additive + ZTIE-isolated — then run the **Phase 2 gate**: a dummy-payload Step Functions execution reaches the **"Awaiting Sandbox Approval"** paused state with no IAM/config errors. |

---

### Background & Context

Phase 1 is closed (trust fabric ✅, `restore/phase-1-green`). The two Phase-2
deliverables are authored, offline-proven, and sealed-PASS:

- **Story 2.1 ✅** — `infra/codebuild-projects.yaml` (`pdlv-lint` + `pdlv-deploy`
  CodeBuild projects + the `pdlv-codebuild-service-role`, whose only cross-account
  power is `sts:AssumeRole` into the three Story 1.1 `pde-member-execution-<env>`
  roles — RD-006 orchestrate-and-pull). Sealed PASS 2026-10-01, commit `aa47f85`.
- **Story 2.2 ✅** — `infra/state-machine.yaml` (`pdlv-promotion-pipeline` STANDARD
  state machine: `DeployDev → AwaitSandboxApproval → DeploySandbox → AwaitProdApproval
  → DeployProd → PromotionSucceeded`; each `DeployX` starts the 2.1 `pdlv-deploy`
  project via `codebuild:startBuild.sync`; each `AwaitXApproval` is a native
  `sns:publish.waitForTaskToken` paused state; `pdlv-promotion-pipeline-role`
  least-privilege execution role; `pdlv-promotion-approval` SNS topic (SSE via
  `alias/aws/sns`); dedicated `pdlv-` log group). Sealed PASS 2026-10-01, CI run
  #36943324686, commit `4aa3e5a` (checkout-proof).

Story 2.3 takes those two templates **off the shelf and into the Hub**: a CLI
bootstrap deploy, then the live Phase 2 gate run. **This is the first time anything
is deployed** in PDE's control plane.

### Objective & Value

- **Objective:** deploy the 2.1 + 2.2 CloudFormation into Pipeline-Hub `641628980935`
  via CLI (`aws cloudformation deploy`, `--capabilities CAPABILITY_NAMED_IAM`), confirm
  the IAM roles landed are tightly scoped to exactly the PDE tasks, then start a
  dummy-payload execution of the `pdlv-promotion-pipeline` state machine and confirm it
  reaches the **"Awaiting Sandbox Approval"** paused state (`.waitForTaskToken`) with no
  IAM/config errors.
- **Why it matters:** this is the **Phase 2 gate** — proof that the control-plane brain
  stands up and pauses cleanly for human approval. Passing it closes Phase 2 and opens
  Phase 3 (the Golden Path end-to-end delivery).

### Scope, Dependencies & Position

- **In scope:** the CLI bootstrap deploy of `infra/codebuild-projects.yaml` +
  `infra/state-machine.yaml` into the Hub (order: CodeBuild projects first so the state
  machine can reference the `pdlv-deploy` project; then the state machine); a live
  post-deploy IAM-scope verification (describe the deployed roles/policies — no wildcard,
  no Admin); the **dummy-payload Phase 2 gate run** to the "Awaiting Sandbox Approval"
  paused state; recording the deployed resources in the BOM §2 inventory; cutting
  `restore/phase-2-green` + its state manifest on the gate pass.
- **Out of scope:** actually approving/promoting past the paused state (that is Phase 3,
  Stories 3.2–3.4, with a real artifact); the trivial test artifact itself (Story 3.1);
  any member-side deploy content (the gate stops at the first approval pause, before any
  CodeBuild deploy runs); the org-wide CloudTrail (Story 4.1); the management account.
- **Depends on:** **2.1 ✅ AND 2.2 ✅** (both sealed PASS). _Advancement gate satisfied._
- **Unblocks:** Phase 3 (Golden Path) — Story 3.1 begins once the Phase 2 gate passes.
- **Roadmap position:** final Phase-2 story; **tier 4 — a tier advance over 2.1/2.2
  (tier 3)**; it **closes Phase 2** (cut `restore/phase-2-green`). Announce the tier
  advance at handoff.

### Approach & Constraints

- **Approach (operator-run, in Hub CloudShell):** (1) STEP 0 — bootstrap the launch pad
  (`scripts/bootstrap_launchpad.sh` — confirm identity `641628980935`, clean clone,
  checkout, `LAUNCH-PAD VERIFY: PASS`); (2) confirm the `pdlv-` names are free
  (`list-stacks … contains(StackName,'pdlv-')`) — ZTIE owns `pde-*`; (3) `aws
  cloudformation deploy` the CodeBuild stack, THEN the state-machine stack, with
  `CAPABILITY_NAMED_IAM`; (4) **verify the real deployed resources** — describe the
  state machine + the two execution roles, confirm `pdlv-` naming + `Project=PDE` tags +
  no wildcard/Admin in the landed policies (never trust the green `CREATE_COMPLETE`
  line alone); (5) start a dummy-payload execution and confirm it reaches **"Awaiting
  Sandbox Approval"** and *pauses* (status `RUNNING`, the approval task waiting on its
  token) with no `States.*`/IAM error; (6) paste raw output for the independent
  validator.
- **Hard constraints:** CloudFormation (YAML) + Python 3 / AWS CLI only — **no Terraform**
  (RD-004); AWS-native + serverless (RD-003); **least privilege / zero-trust** — verify
  the landed roles are scoped (no wildcards, no AdministratorAccess) (RD-006, Universal
  Criterion 3); **ZTIE-safe `pdlv-` namespace** (RD-009 — `pde-*` is ZTIE's; re-check
  names are free before deploy), strictly additive + non-destructive (Universal
  Criterion 5); zero-touch management account `467866449172` (Universal Criterion 1).

### Validation Rationale & Compliance Mapping (optional)

- **Rationale:** proves the control plane deploys and the human-approval gate pauses
  cleanly under least privilege in a ZTIE-isolated namespace — the Phase 2 gate itself.
- **Audit evidence produced:** `cloudformation describe-stacks`/`describe-stack-resources`
  output, the deployed-role policy JSON (least-privilege proof), and the Step Functions
  `describe-execution` / `get-execution-history` showing the paused approval state.

### Change & Rollback

- **Change type:** standard but **live** (first PDE control-plane deploy; additive —
  net-new `pdlv-` stacks, no existing resource touched).
- **Restore point this builds from:** `restore/phase-1-green`.
- **Backout plan:** the deploy is additive net-new `pdlv-` stacks — back out by deleting
  them (`aws cloudformation delete-stack` on the `pdlv-` stacks, importers before
  exporters) with no effect on ZTIE's `pde-*` or on the member accounts. On the gate
  pass, cut `restore/phase-2-green` + the state manifest so Phase 2 is a restorable
  baseline.

### Definition of Done / Validation Gate

- **Done means (this IS the Phase 2 gate):** the 2.1 + 2.2 stacks are deployed in the
  Hub; the landed IAM roles are verified tightly scoped (no wildcard / no Admin); and a
  dummy-payload execution of `pdlv-promotion-pipeline` reaches the **"Awaiting Sandbox
  Approval"** paused state with **no IAM/config errors**, confirmed from live
  `describe-execution` / `get-execution-history` output.
- **Validated by:** an INDEPENDENT validator (not the builder) via
  `DOCS/session-briefs/story-2.3-VALIDATOR-HANDOVER.md`; the USER runs the live deploy +
  gate in Hub CloudShell and pastes raw output; the executor records the sealed verdict.
- **Validation Result:** `pending`.
- **On pass:** record it, flip 2.3 → ✅, **flip the Phase 2 Progress-Summary row ✅**,
  cut `restore/phase-2-green` + its state manifest, add the deployed resources to BOM §2,
  then author Story 3.1's brief + prompt (warm handoff). _(This CLOSES Phase 2.)_
- **On fail:** stays 🟡; fix (fix-then-validate-once) and re-run.
- **Advancement gate:** Phase 3 cannot begin until this (the Phase 2 gate) passes.

### Risks & Watch-Items

- **Deploy order matters.** Deploy the CodeBuild stack BEFORE the state-machine stack —
  the state machine references the `pdlv-deploy` project (by name/ARN or import). If 2.2
  imports a 2.1 export, the exporter must exist first.
- **Verify the real deployed artifact, not the green line (standing lesson).** A
  `✅ CREATE_COMPLETE` can still ship the wrong thing (stale checkout / wrong account).
  After deploy, describe the live state machine + roles and confirm the `pdlv-` names,
  `Project=PDE` tags, the `waitForTaskToken` approval states, and least privilege are
  actually present.
- **ZTIE collision (RD-009).** Re-run `list-stacks … contains(StackName,'pdlv-')` before
  deploy; `pde-*` (18 stacks) is ZTIE's. Never deploy a `pde-`-named stack.
- **The pause is the point.** The gate asserts the execution PAUSES at "Awaiting Sandbox
  Approval" — it must NOT auto-advance (that would mean the approval wasn't a real
  `.waitForTaskToken` pause). Do not approve/send the task token in 2.3 (that's Phase 3).
- **VD-3b opportunity.** If this story (or the state-machine role) causes
  `pde-hub-orchestrator` to exist, run the committed `scripts/phase1_gate.py` live to
  clear the deferred VD-3b (Hub→member `sts:AssumeRole`). Otherwise VD-3b stays carried.
- **CloudShell is ~1 GB (OD-007).** Free disk first (`df -h ~`, clear `~/.cache`, drop
  stale clones) before the clone + any `pip`. Prefer the launch-pad bootstrap.

### Lessons Learned / Carry-Forward *(authored at the end of Story 2.2 — actual lessons)*

- **Validate on a checkout-proof target — CI on the PR head, never a hand-pasted
  CloudShell clone.** Story 2.2 took **8 attempts** to a sealed PASS; every wasted cycle
  was a human clone/checkout failure, NOT a deliverable defect: attempts 1–2 cloned the
  wrong repo (CodeCommit `pde-hub` instead of GitHub `warrenrutledge64/pde-platform`);
  attempt 6 pasted the literal `<TOKEN>` placeholder with an unquoted URL so bash read
  `<` as a redirect and the clone never ran; attempts 3–5 validated a STALE pre-fix
  commit. The moment the committed `.github/workflows/static-bar.yml` ran on the PR head,
  it was green. **For 2.3:** the live deploy + gate must run in CloudShell (that part is
  inherently operator-run), but any *static* re-check should go through CI; and the
  LIVE-RUNBOOK must (a) bootstrap the launch pad with `LAUNCH-PAD VERIFY: PASS` FIRST,
  (b) use a QUOTED clone URL with a REAL token (never the literal `<TOKEN>`), and
  (c) confirm `git log --oneline -1` + a positive content-check before trusting anything.
- **When a gate runs more than one tool over the same tree, match their scope** (2.2
  attempt 7: a non-recursive `cfn-lint infra/*.yaml` vs a recursive `checkov -d infra`
  failed 2.2's PR on a deferred template neither story owned — fixed with `--skip-path
  infra/deferred`). **For 2.3:** if you add any CI/static step, scope it to the active
  artifacts consistently.
- **Merge the deliverable and its close-out together — never land the artifact ahead of
  its validated ledger (the fix-after-merge trap).** 2.2's deliverable merged early at
  PRs #24 and #25, forcing two reconciliation PRs (#26). A **CI merge-order guard**
  (`scripts/check_merge_order.py`, wired into the static bar) now turns a deliverable PR
  red while the gate is ARMED; the convention is **merge only when green** (server-side
  branch protection is NOT enforced on this private/free repo). **For 2.3:** keep the
  status flip + close-out on the same branch as (or merged together with) the work;
  confirm the gate is DISARMED at head before merging.
- **Verify the real deployed resource, not the green deploy line.** A standing lesson now
  doubly relevant since 2.3 is the first live deploy: after `cloudformation deploy`,
  inspect the live state machine + roles (names, tags, policies, approval states) — a
  "successful" deploy of a stale/wrong template is a silent gap.
- **Coerce numeric/boolean reads from AWS APIs; never trust a green status line.** General
  AWS-API hygiene carried across PDE/ZTIE.
- **Current true state at handoff:** Phase 1 CLOSED (`restore/phase-1-green`); **2.1 ✅**
  (sealed PASS, `aa47f85`); **2.2 ✅** (sealed PASS, CI #36943324686, `4aa3e5a`); the
  Validation Debt Register is **empty**, the gate is **DISARMED**, and 2.3's advancement
  gate (2.1 ✅ + 2.2 ✅) is **satisfied**. 2.3 is tier 4 — a tier advance over tier 3,
  and the Phase-2-closing story.
- **Account topology (authoritative):** Hub `641628980935` (where SFN + CodeBuild run +
  deploy); members Dev `946509368326`, Sandbox `586917955591`, Prod `466494951534`;
  management/root `467866449172` zero-touch; Pipeline-Forensics `360999005254` is
  **ZTIE's**, not PDE.
- **VD-3b still carried for Phase 2.** The live Hub→member `sts:AssumeRole`
  (`python3 scripts/phase1_gate.py`) runs once `pde-hub-orchestrator` exists. If 2.3's
  wiring creates that role, clear VD-3b in this story.
- **User notes:** _(open for the user)_
