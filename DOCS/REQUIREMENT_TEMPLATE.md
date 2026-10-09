Author-Seat: Planner / Validator (Gemini)

# Requirement — TEMPLATE (the Planner's story output)

> **`Author-Seat:` (first line — do NOT delete or change the seat).** This requirement
> is authored by the **Planner** seat and is read-only to the Builder (AGENTS.md §3 /
> §4.1). The `scripts/check_docs.py` CHECK Q authorship-barrier gate HARD-fails a
> `*-requirement.md` whose `Author-Seat:` is anything other than the Planner — the
> mechanical guard that the thing-under-test never frames its own judgment. Keep the
> line; only the Planner changes what follows it.
>
> **Purpose.** The standardized output of the **Planner / Validator seat (Gemini)**
> acting *as Planner* — the one-page requirement that tells the Builder what a story
> must achieve and why, and gives the Human the anchor they later restate in their
> own words. One per story, stored under `session-briefs/` alongside the brief.
> See [`../governance/AGENTS.md`](../governance/AGENTS.md) §2.1 / §3 for the seat and
> authority.
>
> **Who fills this in.** The **Planner (Gemini)**, from `PROJECT_PLAN.md` + the
> story's place in `RUNBOOK.md`. Fill every `[[ ... ]]`, then delete these
> instruction blockquotes.
>
> **Information barrier (non-negotiable — [`../governance/AGENTS.md`](../governance/AGENTS.md) §4.1).**
> A requirement states *what* and *why*; it is **NOT** a Definition of Done and
> **NOT** a pass/fail rubric. The independent Validator authors the DoD **blind**
> from this requirement + the raw change ([`VALIDATOR_BRIEF_TEMPLATE.md`](VALIDATOR_BRIEF_TEMPLATE.md)).
> Do not write "how to grade it" here, and do not let the Builder edit this file —
> that would let the thing-under-test frame its own judgment.
>
> **KEEP IT LEAN — fat causes drift and hallucination (RD-008 / METHODOLOGY §7).**
> When filled this document is **~30 lines**: one Objective paragraph, 3–5 criteria,
> a tight scope split, and the dependency/rationale lines. Carry load-bearing
> content only; link `PROJECT_PLAN.md`/`RUNBOOK.md` rather than restating them. On
> re-scope, re-trim — never just append.

---

## Story [[ STORY_ID ]] — [[ STORY_TITLE ]]

### Objective

[[ ONE paragraph (3–5 sentences): what this story delivers, concretely, and the
   capability gained or risk reduced. Enough footing for a newcomer; no implementation
   detail — that is the Builder's. ]]

### Acceptance Criteria

> 3–5 **objective, testable** conditions. Each is a fact a skeptic can confirm from
> the real system — observable and binary, not a task list. These are inputs the
> Validator derives its DoD from; they are not themselves the DoD.

- [[ Criterion 1 — observable, binary (e.g. "resource X exists in account N with property P") ]]
- [[ Criterion 2 ]]
- [[ Criterion 3 ]]
- [[ Criterion 4 — optional ]]
- [[ Criterion 5 — optional ]]

### Scope

- **In:** [[ the concrete deliverable(s) this story produces ]]
- **Out:** [[ explicitly what this story does NOT do / what a later story owns ]]

### Dependencies & Validation Rationale

- **Depends on:** [[ prior stories / restore points that must be ✅ first ]]
- **Unblocks:** [[ downstream stories this enables ]]
- **Validation rationale:** [[ 1–2 sentences: why proving this matters for the
  project's quality/security posture — the skeptic's reason to validate it live ]]
- **Compliance mapping (optional, candidate — pending ratification):** [[ framework /
  control ID(s), or "none" ]]
