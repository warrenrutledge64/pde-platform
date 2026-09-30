# Platform Delivery Engine (PDE) — Execution Runbook

> **Living progress ledger.** This runbook mirrors [`PROJECT_PLAN.md`](PROJECT_PLAN.md)
> but is execution-oriented: every story is a trackable item with dependencies,
> do-it steps, a validation check, and a completion marker. The plan is the
> *what/why*; this runbook is the *do-it-and-track-it*. **This file is the source
> of truth for story status** — and it carries the binding Validation &
> Advancement Gate below.
>
> **Ordering:** stories are sequenced by **dependency + reuse value** — do what
> unblocks or gets reused by the most downstream work first; pull genuine shared
> foundations forward and build them once. Validation gates are sacred: no phase
> is done without its live validation, and nothing builds on unproven ground.

## Status Legend

`⬜ Not Started` · `🟡 In Progress` · `⛔ Blocked` · `✅ Done (validated)`

## Validation & Advancement Gate (BINDING)

> The **enforced state machine** for every story and phase. Validation results —
> recorded, live, confirmed — **drive** status changes and **dictate** whether work
> advances. Status is never set on inference; advancement is never taken on faith.

**Roles.** The **validator** (usually the user, on the live system) runs the check
and confirms the outcome; the **executor records** the result (outcome + date) in
the story's *Validation Result* field and only then changes the status. The
executor never self-certifies a story done.

**Story state machine.** A story moves only on a recorded validation result:

| From | Event | To |
|------|-------|----|
| ⬜ Not Started | work begins | 🟡 In Progress |
| 🟡 In Progress | validation **passes** (recorded, confirmed) | ✅ Done (validated) |
| 🟡 In Progress | validation **fails / incomplete** | 🟡 stays (or ⛔ if externally blocked) |
| ✅ Done | (never auto-reverts; a regression opens a new remediation story) | — |

- **No result → no ✅.** Absent a recorded, confirmed pass, a story stays 🟡.
- **Fail → no advancement.** If a story fails or is only partly validated, **stay
  on that story** until it passes. The next session's objective becomes *fix +
  re-validate this story* — not the next one. Mark **⛔ Blocked** only when
  something external prevents progress; otherwise it stays 🟡 and in-focus.

**Hard advancement gate.** A story **cannot begin** until **every** story in its
`Depends on` column is ✅. If a dependency is not ✅, the executor does **not**
start the dependent story's work. (No override.)

**Phase gate.** A phase closes **only** when its end-of-phase gate returns a
recorded, confirmed pass. On phase-close — and not before:
1. capture the restore point (see [`RESTORE.md`](RESTORE.md)),
2. record it in [`BOM.md`](BOM.md),
3. set the phase row in the Progress Summary to ✅.

**Per-session handshake (enforced by the prompt template).** Every session, before
new work:
1. **Close out the prior story:** if it is 🟡 pending validation, obtain the
   result → on pass, record it + flip ✅ (+ Completed date); on fail, keep 🟡 and
   re-focus on it.
2. **Check the advancement gate:** confirm this story's `Depends on` are all ✅; if
   not, stop and surface the blocker.

**Recording a result.** Each story tracks a *Validation Result* — a one-line dated
record (`pass — <what was checked>, <date>, confirmed by <who>` or
`FAIL — <what failed>, <date>`). This line is the auditable driver behind the
status marker; the marker without a recorded result is not a valid ✅.

## Story Close-Out Procedure (how the ledger stays current)

> There is **no hook, CI job, or script** that mutates this file. The ledger is
> kept current by the **executor, by hand, as a mandatory step of closing a story**
> — enforced by the gate above. These are the exact edits and the commit
> convention.

**The paired-commit convention.** Work and status are **separate commits**:
- **Commit A — the work.** Build the story, push to a branch, open a PR. The story
  **stays 🟡** — merging code does not make it done.
- **Commit B — the status flip.** Only after the user confirms a **live pass**, make
  a **small, dedicated commit** that touches the runbook (and, at a phase close,
  the inventory + tag). Status flips ride small, fast-merging PRs so the ledger on
  the main line never lies. If a flip and the main line disagree, the main line
  wins — reconcile by merging the recorded flip.

**On a confirmed pass, edit exactly these three things in this runbook:**
1. **Summary-table row** — change the story's status cell 🟡 → ✅ and fill the
   **Completed** date.
2. **Detail-block header** — change the story's detail heading from
   `🟡 In Progress` to `✅ Done (validated)`.
3. **`Validation Result:` line** — replace the `pending` text with a dated,
   one-line record quoting *what the user actually checked live*
   (`pass — <what was checked>, <date>, confirmed by <who>`).

**On a fail / incomplete:** change nothing to ✅. Keep the row 🟡 (or ⛔ if
externally blocked), and record the failure in the `Validation Result` line
(`FAIL — <what failed>, <date>`). The next session re-focuses on this story.

**If the story closes a phase (and only on a recorded pass):** additionally
1. create the annotated `restore/phase-<N>-green` tag at the validated commit (see
   [`RESTORE.md`](RESTORE.md)),
2. add the restore-point row to [`BOM.md`](BOM.md) (tag + SHA +
   manifest path),
3. flip the **phase row** in the Progress Summary to ✅.

**Then — the warm handoff (mandatory).** Author the NEXT story's brief + prompt
under `session-briefs/`, including a `Lessons Learned / Carry-Forward` section with
THIS session's actual lessons. A close-out without the next handoff is incomplete.

## Build Tiers & Dependency-Driven Sequencing

> **Build tier** = `1 + the highest tier of anything a story depends on`. It is the
> objective measure of how deep in the dependency graph a story sits, and the
> source of truth for *ordering*. Stories are worked in ascending tier order; ties
> are broken by reuse value (build the most-reused foundation first).
>
> **Announce tier transitions explicitly at handoff.** A tier *advance* (opening a
> new dependency layer) is exactly the moment to re-confirm that the ENTIRE new
> dependency set is ✅ **and** the Validation Debt Register is empty — not merely
> glance at the immediately-prior story. A tier transition often coincides with a
> phase change but is distinct from it; when both happen, name both.

| Tier | Story | Depends on | Phase | Notes |
|------|-------|-----------|-------|-------|
| 1 | 1.1 | — | 1 | Foundation: clean Org-wide CloudTrail baseline. First story, no deps. |
| 2 | 1.2 | 1.1 | 1 | Cross-account trust roles (Dev/Sandbox/Prod trust the Hub). |
| 3 | 1.3 | 1.2 | 1 | CloudShell repo access for the bootstrap operator. |
| 4 | 2.1 | Phase 1 gate | 2 | CodeBuild CFN templates (Lint + Deploy), ZTIE-safe prefixes. |
| 4 | 2.2 | Phase 1 gate | 2 | Step Functions state machine (Dev→Sandbox→Prod + approval gates). |
| 5 | 2.3 | 2.1, 2.2 | 2 | Bootstrap PDE infra into the Hub via CLI (tightly-scoped IAM). |
| 6 | 3.1 | Phase 2 gate | 3 | Trivial zero-cost artifact (empty DynamoDB/SQS) in CFN. |
| 7 | 3.2 | 3.1 | 3 | Commit artifact, trigger pipeline, deploy to Pipeline-Dev. |
| 8 | 3.3 | 3.2 | 3 | Validate Dev, approve gate, promote to Pipeline-Sandbox. |
| 9 | 3.4 | 3.3 | 3 | Split-brain validate Sandbox, approve final gate, release to Pipeline-Prod. |

## Validation Debt Register

> The single source of truth for **open validation debt** — any story that is 🟡
> built-but-not-yet-live-validated, or any recorded FAIL awaiting rework. **When
> this register is non-empty the advancement gate is ARMED:** no *new* feature
> story (a new tier / new dependency layer) may begin until the debt is cleared by
> a recorded live pass. Reworking the debited story itself is always allowed (it is
> the covenant working, not failing).

| # | Story | Debt (what is unproven) | Opened | State |
|---|-------|-------------------------|--------|-------|
| — | — | _(empty — no open validation debt; gate DISARMED)_ | — | — |

**Gate status:** **DISARMED** — the register is empty. Story 1.1 (tier 1, first
story) is clear to begin.

## Operational Debt Register

> The single source of truth for **operational / tooling debt** (ITIL known-error
> style): defects, workarounds, and reusable-OS-vs-instance gaps that are not story
> validation debt but still must be tracked, owned, and cleared — never left as a
> scattered note. Each item carries an explicit **Depends-on / Feeds** edge so up-
> and down-stream relationships are visible. `OPEN` items are carried; `PAID` items
> are retained (not deleted) as the audit trail of what was resolved and how.

| # | Item | State | Owner | Depends-on / Feeds | Clear-by / Resolution |
|---|------|-------|-------|--------------------|-----------------------|
| OD-001 | `check_docs.py` CHECK S false-positived: it read the first status glyph *anywhere* in a `\| <story-id> \|` row, so a glyph mentioned in **prose** in an auxiliary Ready-Now/Blocked/Build-Tier table (e.g. `1.1 not yet ✅`) was mis-read as that story's status. | **PAID** (2026-09-30) | executor | **Feeds:** the reusable OS layer. **Depends-on:** SDD-repo-kit PR #2 (source-of-truth fix). | Fixed at the source template ([SDD-repo-kit PR #2](https://github.com/warrenrutledge64/SDD-repo-kit/pull/2), new `_status_cell_glyph()` accepting a glyph only as a cell's sole token) **and paid down in-instance** the same day (Option B): the fixed `scripts/check_docs.py` + tests backported into this repo, so the instance gate is byte-identical to the corrected kit. A future re-sync of the kit's `scripts/` into this instance is therefore a **no-op**. Authoring rule retained: keep status glyphs out of Ready/Blocked/Tier prose cells; only phase summary tables + detail-block headers carry glyphs. |

## Ready-Now / Blocked / Default-Next-Action

**Ready now (all `Depends on` are ✅, or none):**

| Story | Tier | Why ready |
|-------|------|-----------|
| 1.1 | 1 | No dependencies — the first foundation story. |

**Blocked (waiting on an unmet dependency):**

| Story | Tier | Blocked on |
|-------|------|------------|
| 1.2 | 2 | Story 1.1 not yet validated |
| 1.3 | 3 | Story 1.2 not yet validated |
| 2.1, 2.2 | 4 | Phase 1 gate not yet passed |
| 2.3 | 5 | Stories 2.1 + 2.2 not yet validated |
| 3.1 | 6 | Phase 2 gate not yet passed |
| 3.2 | 7 | Story 3.1 not yet validated |
| 3.3 | 8 | Story 3.2 not yet validated |
| 3.4 | 9 | Story 3.3 not yet validated |

**Default next action:** Execute **Story 1.1** — author the net-new Org-wide
CloudTrail CloudFormation (centralized S3 logging bucket + KMS key), prove it
offline (cfn-lint / cfn-guard / Checkov), and hand the human operator the live
deploy + validation runbook for the Phase 1 gate.

## Progress Summary

| Phase | Scope | Gate | Status |
|-------|-------|------|--------|
| **0 — Bootstrap** | Author `PROJECT_PLAN.md` (planner) + derive `RUNBOOK.md`, `RESTORE.md`, `BOM.md`; validated. | `check_docs.py` PASSES **and** a human confirms the runbook faithfully mirrors the plan. | ✅ Done (2026-09-30) |
| **1 — Governance Baseline & Trust Fabric** | Clean Org-wide CloudTrail baseline + cross-account IAM trust from Hub to Spokes + CloudShell bootstrap access. | CloudShell Boto3 script `AssumeRole`s into Dev/Sandbox/Prod (returns their Account IDs) AND the new CloudTrail bucket is receiving logs for those accounts. | ⬜ Not Started |
| **2 — PDE Control Plane (The Hub)** | Greenfield serverless engine (Step Functions + CodeBuild) in the Hub, ZTIE-safe, doing cross-account CFN deploys. | The deployed Step Function, triggered with a dummy payload, reaches the "Awaiting Sandbox Approval" paused state with no IAM/config errors. | ⬜ Not Started |
| **3 — The Golden Path Validation** | Prove end-to-end delivery by sending a real artifact through the pipeline. | The operator queries `Pipeline-Prod` and returns the deployed test artifact's metadata, proving a Hub-orchestrated cross-account production release. | ⬜ Not Started |

---

## Phase 0 — Bootstrap

_Gate: `python3 scripts/check_docs.py` PASSES (no stray placeholders in living docs, PLAN↔RUNBOOK story sets agree, no dangling links) AND a human has read the plan and confirmed the runbook faithfully mirrors it._

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 0.1 | Author the foundational documents (PLAN + RUNBOOK) | — | ✅ | 2026-09-30 | |

**0.1 — Author the foundational documents (PLAN + RUNBOOK)**  ✅ _Done (validated)_
- Steps: (1) drop the planner's finalized `PROJECT_PLAN.md`; (2) derive this RUNBOOK from it (master table + build tiers + Validation Debt Register + all stories ⬜, gate sections kept verbatim); (3) tailor `RESTORE.md` + `BOM.md` to PDE's technology (CloudFormation stacks + IAM roles + CloudTrail as "state"); (4) resolve `METHODOLOGY.md` placeholders; (5) author Story 1.1's brief + prompt (warm handoff); (6) `git config core.hooksPath .githooks`.
- **Validation Result:** pass — `check_docs.py` PASS + full suite 19 tests OK on `main`; PLAN's 10 feature stories (1.1–3.4) map exactly to the RUNBOOK master table; human reviewed the plan↔runbook and confirmed the runbook faithfully mirrors the plan, 2026-09-30, confirmed by warrenrutledge64.
- **Outcome:** Phase 0 baseline validated. (Phase 0 is a bootstrap phase; a `restore/phase-0-green` tag is optional and not cut.)
- **Advancement gate:** Story 1.1 and everything after depended on this baseline; it is now ✅, so Story 1.1 is clear to begin.

---

## Phase 1 — Governance Baseline & Trust Fabric

_Gate: From an AWS CloudShell session in the Hub account, a human operator executes a Boto3 script that successfully performs an STS `AssumeRole` into Dev, Sandbox, and Prod sequentially (returning their Account IDs), AND verifies the new CloudTrail bucket has begun receiving log files for those accounts._

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 1.1 | Net-new Org-wide CloudTrail (centralized S3 bucket + KMS key), capturing all `Pipeline-*` accounts | — | ⬜ | | |
| 1.2 | Cross-account IAM execution roles in Dev/Sandbox/Prod trusting the Hub | 1.1 | ⬜ | | |
| 1.3 | Configure CloudShell environment with repo access for the bootstrap deploy | 1.2 | ⬜ | | |

**1.1 — Net-new Org-wide CloudTrail (centralized S3 bucket + KMS key), capturing all `Pipeline-*` accounts**  ⬜ _Not Started_
- Steps: author CloudFormation (YAML) for a new centralized S3 log bucket (block-public, versioned, SSE-KMS), a dedicated KMS CMK with a CloudTrail-scoped key policy, and an Organization-wide CloudTrail (`IsOrganizationTrail: true`, multi-region, log-file validation on) that captures all `Pipeline-*` accounts. Prove offline (cfn-lint / cfn-guard / Checkov). Deploy only from the management account (467866449172) — the sole permitted management-account resource per Universal Criterion 1.
- **Validation Result:** _pending — deploy the trail stack; confirm the trail is an active Org trail and log files begin landing in the new bucket for the `Pipeline-*` accounts._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 1.2 (and all downstream cross-account work) cannot begin until the clean audit baseline is actively recording.

**1.2 — Cross-account IAM execution roles in Dev/Sandbox/Prod trusting the Hub**  ⬜ _Not Started_
- Steps: author CloudFormation (YAML) for an execution role in each Spoke account (Dev, Sandbox, Prod) whose trust policy explicitly trusts the Hub account for deployment operations, permissions least-privilege-scoped to exactly the CFN deploy actions required. Prove offline.
- **Validation Result:** _pending — from the Hub, `AssumeRole` into each Spoke role and confirm the returned identity is the Spoke role._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 1.3 (and the Phase 1 gate) cannot begin until the trust roles exist and are assumable.

**1.3 — Configure CloudShell environment with repo access for the bootstrap deploy**  ⬜ _Not Started_
- Steps: document + configure the Hub-account CloudShell environment with token-authenticated repository access and the tooling (AWS CLI, Python 3 / Boto3, cfn-lint) needed for the initial bootstrap deployment.
- **Validation Result:** _pending — from Hub CloudShell, clone the repo and run the Phase 1 gate Boto3 script end-to-end._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date). This story closes Phase 1 — capture `restore/phase-1-green` + inventory row.
- **Advancement gate:** Phase 2 (Control Plane) cannot begin until Phase 1's gate passes.

---

## Phase 2 — PDE Control Plane (The Hub)

_Gate: A human operator triggers the deployed Step Function in the Hub account with a dummy payload, and the execution successfully reaches the "Awaiting Sandbox Approval" paused state without IAM or configuration errors._

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 2.1 | CodeBuild CloudFormation templates (Lint + Deploy), ZTIE-safe naming prefixes | Phase 1 gate | ⬜ | | |
| 2.2 | Step Functions state machine (Dev→Sandbox→Prod promotion + manual approval gates) | Phase 1 gate | ⬜ | | |
| 2.3 | Bootstrap the net-new PDE infra into the Hub via CLI, tightly-scoped IAM | 2.1, 2.2 | ⬜ | | |

**2.1 — CodeBuild CloudFormation templates (Lint + Deploy), ZTIE-safe naming prefixes**  ⬜ _Not Started_
- Steps: author CloudFormation (YAML) for the PDE CodeBuild projects (a Linting/static-analysis project and a Deployment project), enforcing standard `pde-` naming prefixes + resource tagging so nothing collides with or alters existing ZTIE infrastructure in the Hub (Universal Criterion 5). Prove offline.
- **Validation Result:** _pending — synth/lint the templates; on deploy, confirm the CodeBuild projects exist under the `pde-` namespace with no ZTIE resource touched._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 2.3 cannot begin until 2.1 + 2.2 are ✅.

**2.2 — Step Functions state machine (Dev→Sandbox→Prod promotion + manual approval gates)**  ⬜ _Not Started_
- Steps: author the Step Functions state machine (definition + its CloudFormation) orchestrating the Dev → Sandbox → Prod promotion workflow, including the manual approval gates (native paused states) and per-environment cross-account CFN deploy tasks. Prove offline.
- **Validation Result:** _pending — validate the state-machine definition; the paused-approval states are present and wired between environment deploys._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 2.3 cannot begin until 2.1 + 2.2 are ✅.

**2.3 — Bootstrap the net-new PDE infra into the Hub via CLI, tightly-scoped IAM**  ⬜ _Not Started_
- Steps: bootstrap-deploy the PDE infrastructure (2.1 + 2.2) into the existing Hub account via CLI, ensuring the IAM roles deployed are tightly scoped to exactly the PDE tasks (Least Privilege / Zero-Trust). Strictly additive + namespace-isolated from ZTIE.
- **Validation Result:** _pending — the Step Function + CodeBuild projects are deployed in the Hub; a dummy-payload run reaches "Awaiting Sandbox Approval" with no IAM/config errors._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date). This story closes Phase 2 — capture `restore/phase-2-green` + inventory row.
- **Advancement gate:** Phase 3 (Golden Path) cannot begin until Phase 2's gate passes.

---

## Phase 3 — The Golden Path Validation

_Gate: The human operator queries the live AWS environment in `Pipeline-Prod` and successfully returns the metadata of the deployed test artifact, proving the Hub successfully orchestrated a cross-account production release._

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 3.1 | Author a trivial, zero-cost artifact (empty DynamoDB table or SQS queue) in CloudFormation | Phase 2 gate | ⬜ | | |
| 3.2 | Commit the artifact and trigger the PDE pipeline to deploy to `Pipeline-Dev` | 3.1 | ⬜ | | |
| 3.3 | Validate the Dev deployment, approve the gate, promote to `Pipeline-Sandbox` | 3.2 | ⬜ | | |
| 3.4 | Split-brain validate the Sandbox artifact, approve the final gate, release to `Pipeline-Prod` | 3.3 | ⬜ | | |

**3.1 — Author a trivial, zero-cost artifact (empty DynamoDB table or SQS queue) in CloudFormation**  ⬜ _Not Started_
- Steps: author a minimal, zero-cost CloudFormation artifact (e.g. an empty on-demand DynamoDB table or an SQS queue) to serve as the payload traversing the pipeline. Prove offline.
- **Validation Result:** _pending — the artifact template lints clean and describes a single trivial resource._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 3.2 cannot begin until 3.1 is ✅.

**3.2 — Commit the artifact and trigger the PDE pipeline to deploy to `Pipeline-Dev`**  ⬜ _Not Started_
- Steps: commit the artifact and trigger the PDE pipeline; the control plane deploys it cross-account into `Pipeline-Dev`.
- **Validation Result:** _pending — the artifact stack is deployed in `Pipeline-Dev`; describe the resource live._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 3.3 cannot begin until 3.2 is ✅.

**3.3 — Validate the Dev deployment, approve the gate, promote to `Pipeline-Sandbox`**  ⬜ _Not Started_
- Steps: validate the Dev deployment, approve the Step Function's Dev→Sandbox gate, and let the pipeline promote the artifact into `Pipeline-Sandbox`.
- **Validation Result:** _pending — the artifact stack is deployed in `Pipeline-Sandbox` after an approved gate._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date).
- **Advancement gate:** 3.4 cannot begin until 3.3 is ✅.

**3.4 — Split-brain validate the Sandbox artifact, approve the final gate, release to `Pipeline-Prod`**  ⬜ _Not Started_
- Steps: perform split-brain validation on the Sandbox artifact (a check executed independently from the build/deploy execution context — Universal Criterion 2), approve the final Step Function gate, and release the artifact to `Pipeline-Prod`.
- **Validation Result:** _pending — the operator queries `Pipeline-Prod` and returns the deployed artifact's metadata._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date). This story closes Phase 3 — capture `restore/phase-3-green` + inventory row.
- **Advancement gate:** closes the project's Golden Path; future Control-Plane updates become self-hosted through the PDE itself.

---

## Universal Acceptance Criteria (apply to EVERY story/phase gate)

In addition to each story's own validation, every deliverable must satisfy:
1. **Zero-Touch Root:** no resources in the management account (467866449172) other than the strictly required Org-wide CloudTrail configuration.
2. **Split-Brain Validation:** production deployments require a validation check executed independently from the build/deploy execution context.
3. **Static Security Passed:** all CloudFormation and Python code passes static analysis (cfn-lint, cfn-guard, Bandit, Checkov) before execution.
4. **Clean State Rollback:** any failed step leaves behind documentation or an automated method to cleanly revert the state.
5. **Non-Destructive Integration:** deployments into `Pipeline-Hub` use strict resource tagging + naming prefixes to avoid altering existing ZTIE operations.

---

## Ledger Maintenance

- Update a story's **Status** as work moves; set **✅** only after its validation
  passes live **and** the Validation Result line is recorded (see the Story
  Close-Out Procedure).
- On each **phase-close pass**: capture a restore point, record it in the
  inventory, set the phase row ✅.
- Keep the **Validation Debt Register** current: add a row the moment a story goes
  🟡-built-not-validated; clear it on the recorded live pass. A non-empty register
  ARMS the advancement gate.
- Runbook and [`PROJECT_PLAN.md`](PROJECT_PLAN.md) must stay in sync — the plan
  defines scope, the runbook tracks execution.
- **Per-story brief + prompt:** filled from the templates into `session-briefs/`.
- **Next-session brief AND prompt are authored during the current session** — the
  final task each session, including Lessons Learned / Carry-Forward, so the next
  session starts with zero cold-start.
