# Session Brief — Story 0: Author the foundational documents

> **This ships filled-in** (unlike the other templates) because Story 0 is the same
> for every project: turn a planner-produced PROJECT_PLAN into a seeded RUNBOOK and
> validated governance baseline. Adjust only the specifics in brackets.

## Story 0 — Author the foundational documents (PLAN + RUNBOOK)

| Field | Value |
|-------|-------|
| **Phase** | 0 — Bootstrap |
| **Status** | In Progress |
| **Builds from restore point** | none yet (this creates the baseline) |
| **Session goal** | Stand up `PROJECT_PLAN.md` (from the planner) and derive `RUNBOOK.md`, validated. |

### Background & Context

This is a fresh repo with the kit installed; the governance docs are still blank
templates. Before any feature work, the project needs its foundation: the plan (the
*what/why*) and the runbook (the ledger derived from it). See [`BOOTSTRAP.md`](../../BOOTSTRAP.md).

### Objective & Value

- **Objective:** a committed `governance/PROJECT_PLAN.md` (authored by the planner)
  and a `governance/RUNBOOK.md` derived from it — one row per story, dependencies
  set, all ⬜, gate sections verbatim — passing `check_docs.py`.
- **Why it matters:** every later story depends on this. Nothing can be sequenced,
  validated, or tracked without it.

### Scope, Dependencies & Position

- **In scope:** the plan (from the planner), the seeded runbook, tailoring
  `RESTORE.md` + `BOM.md` to this project's tech, turning on the hook.
- **Out of scope:** any feature code. Story 0 produces documents, not features.
- **Depends on:** the planner having produced a PROJECT_PLAN (via
  [`PLANNER_BRIEF_TEMPLATE.md`](../PLANNER_BRIEF_TEMPLATE.md)).
- **Unblocks:** Story 1 and everything after.

### Approach & Constraints

- **Approach:** (1) obtain the planner's `PROJECT_PLAN.md`; (2) derive the runbook
  from it; (3) replace all `{{placeholders}}`; (4) keep the Validation & Advancement
  Gate + Story Close-Out sections verbatim; (5) `git config core.hooksPath .githooks`.
- **Hard constraints:** PLAN first, RUNBOOK second. Do not invent scope the plan
  doesn't contain — if the plan is unclear, go back to the planner.

### Definition of Done / Validation Gate

- **Done means:** `python3 scripts/check_docs.py` PASSES (no stray placeholders in
  living docs, PLAN↔RUNBOOK story sets agree, all RD-### referenced exist, no
  dangling links) **and** a human has read the plan and confirmed the runbook
  faithfully mirrors it.
- **Validated by:** the maintainer (reads the plan; runs `check_docs.py`).
- **Validation Result:** _pending — run `check_docs.py`; confirm the runbook mirrors
  the plan._
- **On pass:** record the dated result, flip Story 0 → ✅; optionally cut the first
  restore point.
- **On fail:** stays 🟡; fix the flagged inconsistency and re-validate.

### Lessons Learned / Carry-Forward

- **Must-know for Story 1:** the plan's phase/story order is now the schedule; Story
  1 is the first story of Phase 1. Keep the gate sections of the runbook untouched.
- **Watch-item:** any assumption the planner marked "proposed" (RD-### proposed) must
  be ratified before a story that depends on it can start.
