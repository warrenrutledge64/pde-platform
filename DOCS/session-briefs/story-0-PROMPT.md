# Session Prompt — Story 0 (executor-facing, ships filled-in)

> Paste this to the executor AI to run Story 0. It assumes the planner has already
> produced a PROJECT_PLAN (via `DOCS/PLANNER_BRIEF_TEMPLATE.md`). See `BOOTSTRAP.md`.

```
You are the execution agent for this project. This is STORY 0: stand up the
foundational documents. Read this fully before acting.

# WHAT STORY 0 IS
Turn the planner's PROJECT_PLAN into a validated governance baseline. You do NOT
write feature code this session — you produce documents and prove they are consistent.

# PLAN FIRST, RUNBOOK SECOND (do not reorder)
1. Obtain governance/PROJECT_PLAN.md from the planner. If it is still the blank
   template (contains {{placeholders}}), STOP: the planner must produce it first
   using DOCS/PLANNER_BRIEF_TEMPLATE.md. Do not invent the plan yourself.
2. Derive governance/RUNBOOK.md FROM the plan:
   - one row per story the plan lists, in the plan's dependency order;
   - set each story's "Depends on" from the plan's dependency map;
   - all statuses ⬜ (nothing is done yet);
   - copy each phase's end-of-phase Gate from the plan;
   - KEEP the "Validation & Advancement Gate" and "Story Close-Out Procedure"
     sections of the runbook VERBATIM — they are the engine; do not reword them.
3. Replace every remaining {{placeholder}} across governance/ (project name, phases,
   etc.). Tailor RESTORE.md + BOM.md to this project's technology (define what a
   "state manifest" means here).

# DEFINITION OF DONE — a PASS/FAIL GATE
Run:  python3 scripts/check_docs.py
It must PASS: no {{placeholder}} left in a living governance doc, PLAN and RUNBOOK
agree on the story set, every referenced RD-### exists, no dangling links. Then a
human reads the plan and confirms the runbook mirrors it. Record that dated result
in the runbook's Story 0 entry and set it ✅. If check_docs FAILS, fix what it names
and re-run — do not mark done.

# THEN
- git config core.hooksPath .githooks   (turn on the pre-commit gate)
- Optionally cut the first restore point once committed + green (see RESTORE.md).
- WARM HANDOFF (mandatory): author Story 1's brief + prompt from the DOCS/ templates,
  with a Lessons Learned section. Story 1 is the first story of Phase 1 in the plan.

# WORKING AGREEMENT
- Branch + PR; never push to main directly. Status flip rides its own small commit.
- Never mark Story 0 ✅ without the recorded check_docs PASS + human confirmation.
```
