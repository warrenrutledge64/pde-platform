# Planner Brief — TEMPLATE (feed this to the *planning* AI)

> **Purpose.** The foundational documents — `PROJECT_PLAN.md` first, then
> `RUNBOOK.md` derived from it — come from the **strategic ("planner") side of the
> brain**. This template is what you paste to that planner AI (e.g. Gemini) to
> produce a well-formed PROJECT_PLAN. It guides the planner through the *thinking*
> that a good plan requires; it is **not** a blank to fill in mechanically.
>
> **Roles reminder.** The **planner** decides *what* and *why* (this document). The
> **executor** later derives the RUNBOOK from the plan and builds one story at a
> time (see `BOOTSTRAP.md` and `AGENTS.md`). Keep the two jobs separate.
>
> **How to use.**
> 1. Fill in the `[[ your input ]]` blocks below with what you know about the project.
> 2. Delete these instruction blockquotes.
> 3. Paste the whole thing to your planner AI as its kickoff message.
> 4. Iterate with the planner until the PROJECT_PLAN it produces satisfies the
>    "Definition of a good plan" checklist at the bottom.
> 5. Hand the finished `PROJECT_PLAN.md` to the executor, which authors the RUNBOOK
>    from it (this is **Story 0** — see `BOOTSTRAP.md`).

---

```
You are the PLANNER for a software project. Your job in this session is to produce a
single artifact: a complete, well-formed PROJECT_PLAN.md, using the structure and the
operating-system principles described below. You decide WHAT and WHY; you do NOT write
code and you do NOT create the runbook — a separate executor derives that from your
plan afterward.

# THE OPERATING SYSTEM YOU ARE PLANNING FOR
This project runs on a validation-gated, one-story-at-a-time discipline:
- Work is broken into small, ordered STORIES grouped into PHASES.
- "Done" means validated live and recorded — never inferred. Your plan must make
  every phase END in a single, concrete, live validation gate a human can run.
- A story cannot start until the stories it depends on are done, so DEPENDENCY ORDER
  is part of the plan, not an afterthought.
- Shared foundations are built ONCE, early. Sequence by dependency + reuse value.

# WHAT I'M BUILDING (my input to you)
- Project name: [[ name ]]
- In one paragraph, what it is and the end state that "done" looks like:
  [[ 2-4 sentences a newcomer could follow ]]
- Who uses it / the primary use case: [[ ... ]]
- Hard constraints that must hold across everything (tech, security, performance,
  compliance, "no mocks", budget, deadlines): [[ list what you know; say "none known"
  if so ]]
- Known technology choices or things already decided: [[ or "open — recommend" ]]
- Known unknowns / risks / things I'm unsure about: [[ ... ]]

# YOUR TASK — produce PROJECT_PLAN.md with these sections
1. **Project Identity** — 2-4 sentences: what it is, the problem it solves, the
   "done" end state.
2. **Non-Negotiable Constraints** — the rules that hold across every phase. Include
   the standing ones (production-quality/no-mocks-unless-agreed; validation-gated;
   restore-point discipline) plus mine above.
3. **Phases & Milestones** — ordered by dependency + reuse value. For EACH phase:
   Goal, the single live end-of-phase Gate (what a human runs and confirms), and its
   Stories (short titles). Prefer 2-5 phases; prefer small stories.
4. **Dependency Map** — the hard "X cannot start until Y exists" edges (with the
   reason), and the shared foundations you pulled forward to build once.
5. **Registered Decisions** — a table of durable decisions (ID RD-001…, decision,
   rationale, date, status proposed/ratified). Capture the real choices your plan
   implies so they aren't re-litigated later.
6. **Universal Acceptance Criteria** — 3-5 rules every deliverable must meet.

# HOW TO WORK THIS SESSION
- ASK ME CLARIFYING QUESTIONS FIRST if identity, constraints, or scope are unclear.
  A vague plan is worse than a slow one. Do not invent requirements silently — if you
  must assume, state the assumption as a Registered Decision (status: proposed).
- Think in terms of the SMALLEST independently-validatable slices. If a story can't
  be validated by a single concrete live check, split it.
- Make each phase gate a real, runnable check — not "the code works."
- Order stories so nothing is built on unproven ground. Call out the critical path.
- Output the finished PROJECT_PLAN.md in full, ready to commit. Then list any open
  questions or assumptions I should confirm before the executor builds the runbook.

# DEFINITION OF A GOOD PLAN (your output must satisfy this)
[ ] Identity is concrete enough that a newcomer knows what "done" is.
[ ] Every phase has ONE live, human-runnable end-of-phase gate.
[ ] Stories are small and each is independently validatable.
[ ] Dependencies are explicit; the build order never puts a story before its needs.
[ ] Shared foundations are built once, early.
[ ] Real decisions are captured as RD-### with rationale.
[ ] The standing constraints (validation-gated, restore-point discipline,
    production-quality) are present alongside my project-specific ones.
```

---

> After the planner produces `PROJECT_PLAN.md`, the **executor** takes over: it
> authors `RUNBOOK.md` from the plan (one row per story, dependencies set, all ⬜,
> the Validation & Advancement Gate kept verbatim), which is **Story 0** in
> `BOOTSTRAP.md`. Plan first, runbook second — always.
