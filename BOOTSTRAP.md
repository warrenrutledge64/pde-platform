# Bootstrap — Day 0: create the foundational documents

> Before any feature work, a project needs its two foundational documents:
> **`governance/PROJECT_PLAN.md`** (the *what/why*) and **`governance/RUNBOOK.md`**
> (the *do-it-and-track-it* ledger). This guide is how they come into existence —
> and, importantly, it treats their creation as the project's **first validated
> story (Story 0)**, not a pre-game afterthought.
>
> **Golden rule of order: PLAN first, RUNBOOK second.** The runbook is *derived
> from* the plan. Never seed the runbook before the plan exists.

---

## Who authors what (split-brain)

The foundational docs come from **two different sides of the brain**, deliberately:

| Document | Authored by | Using |
|---|---|---|
| `PROJECT_PLAN.md` | the **planner** (strategic AI, e.g. Gemini — or you) | [`DOCS/PLANNER_BRIEF_TEMPLATE.md`](DOCS/PLANNER_BRIEF_TEMPLATE.md) |
| `RUNBOOK.md` | the **executor** (the AI working in this repo) | the plan above + the blank `governance/RUNBOOK.md` template |

The planner decides *what and why*; the executor turns that into a trackable ledger
and then runs it. Keeping the jobs separate is what stops the roadmap and the
implementation from quietly drifting into one blurred thing.

---

## Story 0 — "Author the foundational documents"

Creating the plan and runbook is itself a story, run through the normal ritual, so
the foundation is created deliberately and *validated* like everything else.

### Step 1 — Planner produces the PROJECT_PLAN (the other brain)

1. Open [`DOCS/PLANNER_BRIEF_TEMPLATE.md`](DOCS/PLANNER_BRIEF_TEMPLATE.md).
2. Fill in the `[[ your input ]]` blocks with what you know about the project.
3. Paste it to your **planner AI** (e.g. Gemini). Answer its clarifying questions.
4. Iterate until the plan meets the template's "Definition of a good plan" checklist.
5. Save the result as `governance/PROJECT_PLAN.md` (replacing the blank template).

> Why the other brain: the plan is *strategic* work — scope, sequencing, risk,
> decisions. Doing it with the planner keeps it distinct from execution and gives
> the executor a clean spec to build against.

### Step 2 — Executor derives the RUNBOOK from the plan

Hand the finished plan to the **executor** working in this repo. It:

1. Reads `governance/PROJECT_PLAN.md`.
2. Fills `governance/RUNBOOK.md` from it: one row per story the plan lists,
   `Depends on` set from the plan's dependency map, **all statuses ⬜**, each phase's
   **Gate** copied from the plan.
3. **Keeps the "Validation & Advancement Gate" and "Story Close-Out Procedure"
   sections of the runbook verbatim** — those are the engine; do not reword them.
4. Replaces every remaining `{{placeholder}}` across `governance/` (name, phases,
   etc.), and tailors `RESTORE.md` + `BOM.md` to the project's technology (what a
   "state manifest" means here).

### Step 3 — Validate Story 0 (the foundation is checkable too)

Story 0's Definition of Done is a real, runnable check:

```
python3 scripts/check_docs.py
```

It must PASS — meaning: no `{{placeholder}}` left in a living governance doc, the
PLAN and RUNBOOK agree on the story set, every referenced decision (RD-###) exists,
and there are no dangling links. A human confirms the plan reads correctly and the
runbook faithfully mirrors it. **That confirmation is the validation** — record it,
and Story 0 is ✅.

### Step 4 — Turn on the guardrails and capture the starting point

1. `git config core.hooksPath .githooks` (the pre-commit gate: map refresh +
   `check_docs`).
2. Optionally cut your first restore point once the plan/runbook are committed and
   green (see `governance/RESTORE.md`).

### Step 5 — Warm handoff into Story 1

As with any story, close Story 0 by authoring **Story 1's** brief + prompt (from the
templates in `DOCS/`), so the first real feature session starts warm. Then run
Story 1 using the loop in [`TUTORIAL.md`](TUTORIAL.md) Part 4.

---

## What "good" looks like

You don't have to imagine it — the kit ships a filled-in example. Compare:

- **Blank templates:** `governance/PROJECT_PLAN.md`, `governance/RUNBOOK.md` (full of
  `{{placeholders}}`).
- **Filled result:** [`example-project/governance/PROJECT_PLAN.md`](example-project/governance/PROJECT_PLAN.md)
  and [`example-project/governance/RUNBOOK.md`](example-project/governance/RUNBOOK.md) — the TinyLink
  project, showing exactly the level of detail Story 0 should produce (real phases, a
  dependency map, RD-### decisions, and a runbook that mirrors the plan).

---

## Checklist — Day 0 done

- [ ] `PROJECT_PLAN.md` authored by the planner from `PLANNER_BRIEF_TEMPLATE.md`, no
      placeholders, meets the "good plan" checklist.
- [ ] `RUNBOOK.md` derived from the plan: one row per story, deps set, all ⬜, gate
      sections kept verbatim.
- [ ] `RESTORE.md` + `BOM.md` tailored to this project's tech; no stray placeholders.
- [ ] `python3 scripts/check_docs.py` PASSES; a human has read the plan and confirmed
      the runbook mirrors it (Story 0 validated → ✅).
- [ ] `git config core.hooksPath .githooks` set.
- [ ] Story 1's brief + prompt authored (warm handoff).

Now you're ready to build. Everything from here follows the loop in the tutorial.
