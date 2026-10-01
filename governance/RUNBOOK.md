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
| 1 | 1.1 | — | 1 | Foundation: orchestrate-and-pull trust fabric — a member execution role the Hub *invokes* (RD-006 amended). First story, no deps. |
| 2 | 1.2 | 1.1 | 1 | CloudShell repo access for the bootstrap operator. |
| 3 | 2.1 | Phase 1 gate | 2 | CodeBuild CFN templates (Lint + Deploy), ZTIE-safe prefixes. |
| 3 | 2.2 | Phase 1 gate | 2 | Step Functions state machine (Dev→Sandbox→Prod + approval gates). |
| 4 | 2.3 | 2.1, 2.2 | 2 | Bootstrap PDE infra into the Hub via CLI (tightly-scoped IAM). |
| 5 | 3.1 | Phase 2 gate | 3 | Trivial zero-cost artifact (empty DynamoDB/SQS) in CFN. |
| 6 | 3.2 | 3.1 | 3 | Commit artifact, trigger pipeline, deploy to Pipeline-Dev. |
| 7 | 3.3 | 3.2 | 3 | Validate Dev, approve gate, promote to Pipeline-Sandbox. |
| 8 | 3.4 | 3.3 | 3 | Split-brain validate Sandbox, approve final gate, release to Pipeline-Prod. |
| 9 | 4.1 | Phase 3 gate | 4 | **Governance cutover (deferred, RD-007):** switch on the org-wide CloudTrail as a Hub-delegated shared service; retire the audit debt (OD-002). |
| G | G-1 | — | Governance | Independent adversarial **fat-audit** of the prompt/handoff templates (RD-008 / §4a; AI RMF MEASURE-2.7). No pipeline dep; runs now. |
| G | G-2 | G-1 | Governance | **Trim** templates to the audit findings + record the **lean pass** (satisfies the RD-008/§4a gate). Gates Story 1.1's live validation (which uses the audited validator handover). |

> **Governance (`G-`) series.** Tooling/OS-quality stories, tracked separately from the
> pipeline phases (they are not gate-enforced by `check_docs`, which tracks only
> `N.N` IDs — the human tracks G-status). Governance thread **G-1 → G-2 both ✅**
> (2026-09-30) — templates audited + trimmed. Original framing kept for context: **G-1 → G-2**,
> which must complete **before Story 1.1's live validation** (Story 1.1 uses the
> validator-handover template G-1/G-2 audit + trim). Story 1.1 may stay 🟡 meanwhile;
> its *live pass* waits on G-2.

## Validation Debt Register

> The single source of truth for **open validation debt** — any story that is 🟡
> built-but-not-yet-live-validated, or any recorded FAIL awaiting rework. **When
> this register is non-empty the advancement gate is ARMED:** no *new* feature
> story (a new tier / new dependency layer) may begin until the debt is cleared by
> a recorded live pass. Reworking the debited story itself is always allowed (it is
> the covenant working, not failing).

| # | Story | Debt (what is unproven) | Opened | State |
|---|-------|-------------------------|--------|-------|
| ~~VD-1~~ | ~~1.1 (old)~~ | _Superseded 2026-09-30: Story 1.1 re-scoped from the org-wide CloudTrail to the trust fabric (RD-006/RD-007). Org-trail work moved to Story 4.1. Replaced by VD-2._ | 2026-09-30 | SUPERSEDED |
| ~~VD-2~~ | ~~1.1 (Hub-pushes)~~ | _Superseded 2026-09-30: the trust-fabric direction was corrected from Hub-pushes-into-Spoke to the RD-006 **orchestrate-and-pull** model (Hub invokes; member executes locally). The push-model template is retired to `infra/deferred/`. Replaced by VD-3._ | 2026-09-30 | SUPERSEDED |
| VD-4 | 1.2 (CloudShell bootstrap + Phase-1 gate) | The Hub CloudShell bootstrap (`DOCS/CLOUDSHELL_BOOTSTRAP.md`) + the Phase-1 gate script (`scripts/phase1_gate.py`) are authored + offline-proven (24 invariants via `scripts/test_phase1_gate.py`), but 1.2's **live Option-B proof** — Hub-CloudShell reachability + tooling (AWS CLI / Python 3 / Boto3 / cfn-lint) + token-auth repo access, from Pipeline-Hub `641628980935` — is NOT yet recorded. On that live pass 1.2 flips ✅ and **closes Phase 1** (restore tag + inventory). _(The gate script's live cross-account `AssumeRole` run is the separate deferred **VD-3b**, Phase 2 — not this debt.)_ **Attempt 1 (head `fcfe4f3d`) sealed FAIL (2026-09-30, Independent Validator):** token left in the git remote + the 1.2 artifacts were not on disk (the live CloudShell was never on `feature/story-1.2`; a plain clone lands on `main`, and `git show fcfe4f3d` was `invalid object name`). Conditions 1+2 (Hub identity, tooling) passed. **Remediated 2026-10-01** — runbook/bootstrap hardened (explicit `feature/story-1.2` checkout; `git-credential-store` so no token is ever written into the remote URL; a post-clone VERIFY block that fails loudly if the commit/scripts are absent or a token lingers). **Attempt 2 sealed FAIL (2026-09-30):** an EXECUTION MISMATCH — the live CloudShell ran the OLD attempt-1 instructions, not the remediation (HEAD at `330487…`, a commit absent from this repo; `git remote -v` still showed the literal `YOUR_TOKEN` placeholder). The hardened STEP 2 / STEP 2a were never executed. No new deliverable defect found; the fix for attempt 3 is **execution integrity** (clone the clean URL, `git checkout feature/story-1.2`, run STEP 2a and confirm `LAUNCH-PAD VERIFY: PASS` before proceeding). Still OPEN pending a clean re-validation on head `677b632`+. | 2026-10-01 | OPEN (2 FAILs recorded; attempt-2 was an execution mismatch, awaiting a clean re-run) |
| ~~VD-3~~ | ~~1.1 (VD-3a)~~ | Orchestrate-and-pull trust fabric (`infra/member-execution-role.yaml`) authored + offline-proven (21 invariants), but NOT yet live-validated. **Validation is split (Path A, stakeholder-chosen):** VD-3a = the member roles are deployed in Dev/Sandbox/Prod and `get-role` confirms each trusts the *specific* Hub orchestrator role (not `:root`) + requires `sts:ExternalId` — **provable now**; VD-3b = the full live Hub→member `sts:AssumeRole` (succeeds with ExternalId / denied without) — **deferred to Phase 2** because the `pde-hub-orchestrator` Hub role does not exist until then. Story 1.1 flips ✅ on VD-3a (trust correct-by-construction); VD-3b is tracked as a Phase-2 confirmation, not a 1.1 blocker. **CLEARED 2026-09-30** on the independent validator's sealed PASS (all four VD-3a DoD conditions met). VD-3b remains a Phase-2 item (created with the `pde-hub-orchestrator` role), NOT open 1.1 debt. | 2026-09-30 | CLEARED (VD-3a); VD-3b → Phase 2 |

**Gate status:** **ARMED** — VD-4 is OPEN: Story 1.2 (CloudShell bootstrap + Phase-1
gate) is 🟡 built + offline-proven (24 invariants) but awaiting its live Option-B pass
from Hub CloudShell. No new feature story / new tier may begin until VD-4 is cleared by a
recorded live pass. (Reworking 1.2 itself is always allowed.) Story 1.1 remains ✅; its
VD-3b (live Hub→member `sts:AssumeRole`) is a Phase-2 confirmation, not open 1.2 debt.

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
| OD-002 | **Deferred org-wide audit governance (declared debt, RD-007).** During PDE design/build (Phases 1–3) there is **no PDE-provided org-wide CloudTrail audit trail** on the cross-account deploys. This is a *deliberate, accepted* deferral (no interim baseline built) so the delivery engine is proven first — **not** a hidden gap. Accepted risk: activity in that window is not captured by a PDE org trail, and logs not collected in the gap are unrecoverable. | **OPEN** (accepted) | warrenrutledge64 | **Feeds:** Phase 4 governance. **Depends-on:** Phase 3 gate (engine proven first). | **Clear-by = Story 4.1** (Phase 4 — Governance Cutover): switch on the org-wide CloudTrail as a Hub-delegated shared control-plane service (RD-006), adapting `infra/deferred/cloudtrail-org-baseline.yaml` from root-hosted to Hub-delegated. On that story's recorded live pass, OD-002 flips PAID. The org-trail template + its 28-invariant proof are preserved in `infra/deferred/` for historical reference. |
| OD-003 | **Optional dashboard display of agent activity (deferred capability — cross-reference stub).** The Hub dashboard could optionally surface **agent activity**. This is a *deferred feature*, not a defect. **Authoritative owner = the agent build** (this row is a visibility cross-reference only, per the single-source-of-truth rule); the *display surface* is the PDE Hub dashboard (Phase 2/3), which is why PDE records the edge so its dashboard design does not foreclose the option. | **DEFERRED** (documented) | agent build (owner) · PDE (cross-ref) | **Feeds:** the PDE Hub dashboard (Phase 2/3 control-plane surface). **Depends-on:** dashboard design. | **Clear-by / trigger:** revisit when the Hub dashboard is designed — decision = adopt or drop. If adopted, ensure agent-activity telemetry is retained so the option stays open. The authoritative deferred item lives in the **agent build's** register; keep this PDE stub in sync (do not duplicate ownership). |
| OD-004 | **`pde-` namespace in the Hub is ZTIE's, not PDE's (naming-collision correction — surfaced live 2026-10-01).** The Story 1.2 live gate found **18 `pde-*` stacks** already deployed in Pipeline-Hub `641628980935` (created Jun–Aug 2026, **all untagged**). Stack **descriptions** confirm they are **ZTIE's** control plane — e.g. `pde-ztie-websocket-api` ("ZTIE Detonation Chamber - WebSocket API"), `pde-compliance-heatmap` ("Compliance Heatmap Cache … HIPAA 164.530(j)"), `pde-hub-synthesis-parser` ("Contextual Synthesis Engine Parser"), `pde-remediation-statemachine` ("Remediation Engine … Story 9.A.5"), `pde-intake-gateway` ("Secure Intake Gateway … multi-tenant") — plus an early CodeBuild stack `pde-codebuild-foundation` ("PDE CodeBuild Project for Hub Account") that would have **directly collided** with Story 2.1. PDE's plan wrongly assumed `pde-` was its own clean prefix (Universal Criterion 5). | **PAID** (RD-009 ratified 2026-10-01) | warrenrutledge64 (ratified) · executor (implemented) | **Feeds:** Story 2.1 (CodeBuild naming) + all Phase-2/3 Hub deploys. **Depends-on:** RD-009 (ratified). | **Resolution:** **RD-009** (proposed) — PDE's Hub prefix becomes **`pdlv-`** (substring-disjoint from `pde`, so no collision and no inventory-filter overlap with ZTIE); Universal Criterion 5 corrected (ZTIE-safe = **avoid** `pde-*`, not adopt it); already-validated Story 1.1 member roles keep `pde-member-execution-<env>` (member accounts, not the Hub — no collision). On ratification, Story 2.1 is authored against `pdlv-` and `list-stacks` is re-checked for no clash before any Phase-2 deploy. **Companion gap:** see OD-005 (untagged ZTIE stacks). |
| OD-005 | **18 `pde-*` Hub stacks are untagged (ownership/attribution gap — surfaced live 2026-10-01).** None of the pre-existing ZTIE-owned `pde-*` stacks in Pipeline-Hub `641628980935` carry a `Project` (or any ownership) tag, so ownership, cost allocation, and safe-teardown attribution cannot be derived from metadata — it took reading each stack's free-text Description to establish they are ZTIE's. | **DEFERRED** (cross-reference — not PDE's to fix) | ZTIE build (owner) · PDE (cross-ref) | **Feeds:** Hub governance / cost attribution. **Depends-on:** ZTIE adopting a tagging standard. | **Clear-by / trigger:** whoever owns the ZTIE control plane applies a `Project=ZTIE` (and owner) tag pass to those stacks. PDE's own deploys set `Project=PDE` from Story 2.1 onward (Universal Criterion 5), so PDE does not add to this gap; this row exists only so the attribution risk is tracked, not duplicated-owned. |

## Ready-Now / Blocked / Default-Next-Action

**Ready now (all `Depends on` are ✅, or none):**

| Story | Tier | Why ready |
|-------|------|-----------|
| 1.2 | 2 | 🟡 **in progress** — built + offline-proven (24 invariants); its only dependency (1.1) is ✅. Awaiting the live Option-B pass (Hub-CloudShell reachability + tooling + token-auth repo access). Closes Phase 1. _(No other story is Ready: the gate is ARMED on VD-4.)_ |

**Blocked (waiting on an unmet dependency):**

| Story | Tier | Blocked on |
|-------|------|------------|
| 2.1, 2.2 | 3 | Phase 1 gate not yet passed |
| 2.3 | 4 | Stories 2.1 + 2.2 not yet validated |
| 3.1 | 5 | Phase 2 gate not yet passed |
| 3.2 | 6 | Story 3.1 not yet validated |
| 3.3 | 7 | Story 3.2 not yet validated |
| 3.4 | 8 | Story 3.3 not yet validated |
| 4.1 | 9 | Phase 3 gate not yet passed (deferred governance cutover, RD-007) |

**Default next action:** **Story 1.2 — run its live Option-B gate (then close Phase 1).**
1.2 is 🟡 built + offline-proven; the gate is ARMED on **VD-4**. The next action is the
**live validation** per
[`../DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md`](../DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md):
from Pipeline-Hub `641628980935` CloudShell, prove reachability + tooling (AWS CLI /
Python 3 / Boto3 / cfn-lint) + token-auth repo access, with the committed gate script
([`../scripts/phase1_gate.py`](../scripts/phase1_gate.py)) passing its offline proof. On
the recorded pass, flip 1.2 ✅ and **close Phase 1** — capture `restore/phase-1-green`,
write the state manifest, add the BOM inventory row, flip the Phase 1 Progress row ✅.
_(The full live Hub→member `sts:AssumeRole` — the committed gate script's cross-account
run — is the deferred **VD-3b**, run in Phase 2 once `pde-hub-orchestrator` exists; it is
not part of 1.2's DoD.)_

## Progress Summary

| Phase | Scope | Gate | Status |
|-------|-------|------|--------|
| **0 — Bootstrap** | Author `PROJECT_PLAN.md` (planner) + derive `RUNBOOK.md`, `RESTORE.md`, `BOM.md`; validated. | `check_docs.py` PASSES **and** a human confirms the runbook faithfully mirrors the plan. | ✅ Done (2026-09-30) |
| **1 — Trust Fabric** | Cross-account IAM trust from the Hub to the Spokes (Spokes trust specific Hub roles, RD-006) + CloudShell bootstrap access. _(Org-wide audit deferred to Phase 4 per RD-007.)_ | **Option B (2026-09-30):** Hub CloudShell reachability + tooling + token-auth repo access proven live, AND the Boto3 gate script (AssumeRole into Dev/Sandbox/Prod → account IDs) authored + committed. The live cross-account `AssumeRole` run is the deferred **VD-3b**, executed in Phase 2 once `pde-hub-orchestrator` exists (not a temporary stand-in). | ⬜ Not Started |
| **2 — PDE Control Plane (The Hub)** | Greenfield serverless engine (Step Functions + CodeBuild) in the Hub, ZTIE-safe, doing cross-account CFN deploys. | The deployed Step Function, triggered with a dummy payload, reaches the "Awaiting Sandbox Approval" paused state with no IAM/config errors. | ⬜ Not Started |
| **3 — The Golden Path Validation** | Prove end-to-end delivery by sending a real artifact through the pipeline. | The operator queries `Pipeline-Prod` and returns the deployed test artifact's metadata, proving a Hub-orchestrated cross-account production release. | ⬜ Not Started |
| **4 — Governance Cutover** _(deferred, RD-007)_ | Switch on the org-wide CloudTrail as a Hub-delegated shared control-plane service (RD-006); retire the audit debt (OD-002). Executed after the engine is proven. | From the Hub (delegated CloudTrail admin), the org trail is active (org / multi-region / log-file validation) AND logs land for all `Pipeline-*` accounts. | ⬜ Not Started |

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

## Phase 1 — Trust Fabric

_Gate: From an AWS CloudShell session in the Hub account, a human operator (as the Hub orchestrator principal) performs an STS `AssumeRole` into the **member execution role** in Dev, Sandbox, and Prod sequentially, returning their Account IDs — proving the Hub can direct a member function and the orchestrate-and-pull trust direction is correct. (The original CloudTrail half of this gate is deferred to the Phase 4 governance gate per RD-007.) **[Option B, 2026-09-30]** Story 1.2 CLOSES Phase 1 on: Hub CloudShell reachability + tooling + token-auth repo access proven live, AND the Boto3 gate script authored + committed. The live cross-account `AssumeRole` itself is the deferred **VD-3b**, run in Phase 2 once `pde-hub-orchestrator` exists — no temporary Hub stand-in is created._

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 1.1 | Orchestrate-and-pull trust fabric — member execution roles the Hub invokes (RD-006 amended) | — | ✅ | 2026-09-30 | |
| 1.2 | Configure CloudShell environment with repo access for the bootstrap deploy | 1.1 | 🟡 | | |

**1.1 — Orchestrate-and-pull trust fabric — member execution roles the Hub invokes (RD-006 amended)**  ✅ _Done (validated)_
- Steps: author CloudFormation (YAML) for a least-privilege PDE **member execution role** in each member (Dev/Sandbox/Prod) whose trust policy names a **specific** `Pipeline-Hub` (`641628980935`) **orchestrator** role (never the Hub account root, RD-006) and requires an `sts:ExternalId`; permissions scoped to the CloudFormation actions the member's **local** execution needs on the `pde-` stack namespace (execution is local to the member — the Hub directs, it does not push writes in). Prove offline. Deploy once per member (or via a StackSet) — **not** into the management account. _(Tight tier-1 scope: the orchestration engine, the results intake data-contract, and the Hub-signed decision-token machinery are Phase 2. Re-scoped twice — from the deferred org-wide CloudTrail (→ `infra/deferred/`, Story 4.1), then from the initial Hub-pushes shape to this orchestrate-and-pull direction; the retired push-model template is preserved in `infra/deferred/`.)_
- **As built:** `infra/member-execution-role.yaml` (member exec role; trust = specific Hub **orchestrator** role ARN + `ExternalId` NoEcho; least-privilege managed policy scoped to `cloudformation:*` stack ops on this member's `stack/${RolePrefix}*`, no AdministratorAccess, no wildcard; per-env `dev`/`sandbox`/`prod`; exports the role ARN). Offline proof: `python3 infra/validate_trust_fabric.py` — 21 invariants PASS (PyPI is blocked in the build sandbox, so cfn-lint / cfn-guard / Checkov run operator-side / CI). Live deploy + gate steps: [`../DOCS/session-briefs/story-1.1-LIVE-RUNBOOK.md`](../DOCS/session-briefs/story-1.1-LIVE-RUNBOOK.md).
- **Validation Result:** _pass — Story 1.1 trust shape (member roles deployed, explicit hub principal, external-id enforced, mgmt untouched), 2026-09-30, confirmed by Independent Validator. Sealed PASS on all four Path-A (VD-3a) DoD conditions: (1) `pde-member-execution-{dev,sandbox,prod}` exist in 946509368326 / 586917955591 / 466494951534; (2) trust `Principal.AWS` = `arn:aws:iam::641628980935:role/pde-hub-orchestrator` (no `:root`, no wildcard) in all three; (3) `sts:ExternalId` `StringEquals` condition enforced in all three; (4) adversarial zero-touch check — management account 467866449172 has no role (`NoSuchEntity`) and no `pde-` stacks (`[]`). The full live Hub→member `sts:AssumeRole` (succeeds-with-ExternalId / denied-without) remains **deferred to Phase 2** (VD-3b), when `pde-hub-orchestrator` exists — not a 1.1 blocker._
- **History:** _An earlier validator run sealed FAIL (roles missing in Sandbox+Prod, then a wrong-env role name in Prod — an operator `EnvironmentName` copy-paste error, not a template defect; offline invariants stayed 21/21). Remediated operator-side (derive-`EnvironmentName`-from-account deploy pattern) + the ExternalId rotated after it was exposed in a `get-role` full-document dump, then re-validated blind to the PASS above. Interim FAIL recorded at PR #14 (superseded by this PASS)._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date), clear VD-3.
- **Advancement gate:** 1.2 (and all downstream control-plane work) cannot begin until the trust fabric is proven directable by the Hub.

**1.2 — Configure CloudShell environment with repo access for the bootstrap deploy**  🟡 _In Progress_
- Steps: document + configure the Hub-account CloudShell environment with token-authenticated repository access and the tooling (AWS CLI, Python 3 / Boto3, cfn-lint) needed for the initial bootstrap deployment; author + commit the Phase-1 gate Boto3 `AssumeRole`-into-each-member script (targeting `pde-hub-orchestrator`, ExternalId-parameterised, derive-`EnvironmentName`-from-account). _**Option B (2026-09-30):** the script's live cross-account run is deferred to Phase 2 (VD-3b) — no temporary Hub stand-in is stood up; 1.2 proves reachability + tooling + repo access live and commits the gate script._
- **As built:** [`DOCS/CLOUDSHELL_BOOTSTRAP.md`](../DOCS/CLOUDSHELL_BOOTSTRAP.md) (reproducible Hub-CloudShell setup — zero-touch account check, tooling check + `--user` cfn-lint, token-auth clone with token-scrub, `read -rs` ExternalId as an env var, gate-script run guidance); [`scripts/phase1_gate.py`](../scripts/phase1_gate.py) (the committed Phase-1 gate — Boto3, targets the real `pde-hub-orchestrator`, walks Dev→Sandbox→Prod, presents `PDE_EXTERNAL_ID`/`--external-id` never a hardcoded literal, fixed account→env table so no per-account literal is hand-edited, confirms the landed account from the assumed-role ARN, refuses to run outside the Hub and to target the Hub/management accounts, uses only `sts:AssumeRole` + `sts:GetCallerIdentity`); [`scripts/test_phase1_gate.py`](../scripts/test_phase1_gate.py) (offline proof bar — 24 source + behaviour invariants against a fake STS stub, no AWS/network); [`scripts/bootstrap_launchpad.sh`](../scripts/bootstrap_launchpad.sh) (one named command that stands up + VERIFIES the launch pad — Hub-account check, credential-helper PAT, clean clone + `feature/story-1.2` checkout, fail-loud VERIFY — removing the copy-paste-stale-block failure of attempts 1–2). Offline proof: `python3 scripts/test_phase1_gate.py` → PASS (24 invariants); `ruff` clean; `bash -n scripts/bootstrap_launchpad.sh` syntax-clean. Live steps: [`../DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md`](../DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md).
- **Validation Result:** _FAIL — Story 1.2 DoD: target commit missing, gate scripts absent from disk, and auth token exposed in git remote, 2026-09-30 (attempt 2), confirmed by Independent Validator. **Root cause = instruction mismatch, not a deliverable defect: the live CloudShell did not run the remediated runbook.** The transcript shows HEAD at `330487…` — a commit that exists NOWHERE in this repo (not on `main`, not on `feature/story-1.2`) — and `git remote -v` showing the literal placeholder `YOUR_TOKEN@github.com`, i.e. an attempt-1-style `git clone https://YOUR_TOKEN@github.com/…` was pasted verbatim (placeholder and all). The hardened STEP 2 (credential-helper clone), the explicit `git checkout feature/story-1.2`, and the STEP 2a fail-loud VERIFY were never executed — which is why VERIFY (designed to stop before STEP 3) never appeared. Conditions 1 (Hub identity 641628980935) + 2 (tooling) PASSED again. **Fix for attempt 3 = execution integrity, not more code:** operator must clone the CLEAN URL, `git checkout feature/story-1.2`, and run STEP 2a — pasting its `LAUNCH-PAD VERIFY: PASS` line as the precondition before any further step. Awaiting re-validation._
- **History (interim FAILs — superseded on re-validation):** _attempt 1 at head `fcfe4f3d` (token left in remote; artifacts not on disk — CloudShell on `main`, not the feature branch). attempt 2 (2026-09-30) at an UNRELATED commit `330487…` with the `YOUR_TOKEN` placeholder still in the URL — the remediated runbook was not used (execution mismatch). In both, conditions 1+2 passed; the gate script itself never ran because the launch pad was never on the right code. Fixes retained: credential-helper clone (no token-in-URL), explicit feature-branch checkout, STEP 2a VERIFY gate._
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

## Phase 4 — Governance Cutover (deferred org-wide audit, RD-007)

_Gate: From the Hub (as the delegated CloudTrail administrator), a human operator confirms the org-wide trail is active (`IsOrganizationTrail` / multi-region / log-file validation) AND log files are landing for all `Pipeline-*` accounts. (This is the original CloudTrail half of the old Phase 1 gate, moved here per RD-007.)_

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 4.1 | Switch on org-wide CloudTrail as a Hub-delegated shared service; retire the audit debt (OD-002) | Phase 3 gate | ⬜ | | |

**4.1 — Switch on org-wide CloudTrail as a Hub-delegated shared service; retire the audit debt (OD-002)**  ⬜ _Not Started_
- Steps: from the Organization root, `register-delegated-administrator` for `cloudtrail.amazonaws.com` to the Hub (`641628980935`) — root's sole, one-time governance action. Adapt the preserved template `infra/deferred/cloudtrail-org-baseline.yaml` from the root-hosted model to the **Hub-delegated** model (RD-006): deploy the org-wide CloudTrail + centralized S3 log bucket + KMS CMK **in the Hub** under a dedicated governance role (separate from the PDE deploy role). Re-prove offline.
- **Validation Result:** _pending — deploy from the Hub as delegated admin; confirm the org trail is active (org/multi-region/log-file validation) AND logs land for all `Pipeline-*` accounts._
- **On pass (and only then):** record the Validation Result, set this row ✅ (+ Completed date), and flip **OD-002 → PAID** (the audit debt is retired). This story closes Phase 4 — capture `restore/phase-4-green` + inventory row.
- **Advancement gate:** retires the RD-007 audit deferral; the program-wide shared audit service is live for all current and future Hub tenants.

---

## Governance (G-) series — OS-quality / tooling stories

_Tracked separately from the pipeline phases. Not gate-enforced by `check_docs` (which tracks only `N.N` IDs); the human tracks G-status. Current thread: **G-1 → G-2**, which must complete before Story 1.1's LIVE validation (Story 1.1 uses the validator-handover template being audited/trimmed)._

| Story | Title | Depends on | Status | Completed |
|-------|-------|-----------|--------|-----------|
| G-1 | Independent adversarial fat-audit of the prompt/handoff templates | — | ✅ | 2026-09-30 |
| G-2 | Trim templates to the audit findings + record the lean pass | G-1 | ✅ | 2026-09-30 |

**G-1 — Independent adversarial fat-audit of the prompt/handoff templates**  ✅ _Done (validated)_
- Steps: paste the ready-to-paste bloat-focused audit prompt ([`../DOCS/session-briefs/story-G-1-fat-audit-prompt.md`](../DOCS/session-briefs/story-G-1-fat-audit-prompt.md)) to an **independent** validator (Gemini — not the author). The auditor authors its own rubric under the axiom **fat causes drift and hallucination**, attacks the templates, and returns findings + a **measurably tighter rewrite**.
- **Validation Result:** pass — independent auditor (Gemini) authored its own rubric and sealed a verdict + two tighter rewrites (~50% reduction, 0 load-bearing lines lost), 2026-09-30, confirmed by warrenrutledge64. Verdict on the templates = **MUST-BE-TRIMMED, do not run as-is**, on two fatal flaws: (1) the offline-sandbox blocker was buried at the bottom → agent would attempt live calls then hallucinate credentials/mock output; (2) no HALT boundary in the build→validate→commit loop → agent would fabricate a mock validation pass to reach the commit step. G-1's own DoD (deliver an independent audit + rewrite) is MET; the FAIL is the finding on the templates — the valuable output that feeds G-2.
- **Advancement gate:** the two findings feed G-2 (the trim).

**G-2 — Trim templates to the audit findings + record the lean pass**  ✅ _Done (validated)_
- Steps: apply the audit's accepted findings — offline-blocker to Rule #1, explicit HANDOFF (HALT) boundary, load-bearing-only, guardrails early. Mirror upstream into `SDD-repo-kit` (reusable-OS). Re-prove offline (`check_docs` + tests).
- **Validation Result:** pass — applied Gemini's two tighter rewrites to `DOCS/SESSION_PROMPT_TEMPLATE.md` (generic) + `DOCS/session-briefs/story-1.1-PROMPT.md` (instance): offline/no-live-execution constraint is now Rule #1, an explicit **HANDOFF (HALT) — STOP GENERATING** step sits in the execution loop, ~50% leaner with all load-bearing markers preserved (ExternalId, orchestrate-and-pull, member-execution-role, validate_trust_fabric, gh api, Phase-2/CloudTrail/mgmt-account scope-out, least-privilege, no-Terraform, warm-handoff). Mirrored upstream to `SDD-repo-kit`. `check_docs` PASS, 2026-09-30, confirmed by warrenrutledge64 (rewrites authored by the independent auditor, not self-certified). This clears the "prompts are optimized" gate.
- **Advancement gate:** Story 1.1's LIVE validation (VD-3) may now run against the trimmed prompts.

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
