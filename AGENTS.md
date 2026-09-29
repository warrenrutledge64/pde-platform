# AGENTS.md — How to work in this repository

> **You are an AI assistant with access to this repository. Read this file fully
> before doing anything else.** It defines the *way of working* this project
> requires — a validation-gated, one-story-at-a-time discipline. It is not
> optional style advice; it is how work is planned, executed, proven, and handed
> off here. Following it is part of the job.
>
> This convention file is read automatically by many AI coding tools. If yours
> does not read it automatically, the human has pointed you here.

> **Using an AI that doesn't auto-read repo files?** (a plain chat window, or a
> tool with no project-rules feature) — paste this one-liner to onboard it, then
> paste the contents of this file:
>
> > *"You are working in a repository governed by `AGENTS.md`. Read it in full and
> > follow it exactly — especially: nothing is 'done' until it is validated live
> > and recorded, work one story at a time, and never push to `main`. Here is
> > `AGENTS.md`: …"*

## The one rule that governs everything

**"Done" means validated, not merged.** A task is complete only when its result
is checked live and that result is recorded in `governance/RUNBOOK.md`. A command
exiting without error is **not** proof. "It should work" is never a status. If you
have not recorded a confirmed live pass, the work is still in progress.

## What to read first (in order)

1. **`governance/METHODOLOGY.md`** — the full *why and how* of this operating
   system. Read it once, completely.
2. **`governance/RUNBOOK.md`** — the **source of truth for status**. It holds the
   story ledger and the *binding* Validation & Advancement Gate. Every decision
   about "what's next" and "is this done" is answered here.
3. **`governance/PROJECT_PLAN.md`** — the scope, phases, and registered decisions
   (the *what/why*).
4. **`governance/BOM.md`** and **`governance/RESTORE.md`** — the inventory of what
   exists and the restore-point (revert) procedure.

If these files still contain `{{placeholders}}`, the project has not been set up
yet — go to "First-time setup" at the bottom (it's **Story 0**, guided by
[`BOOTSTRAP.md`](BOOTSTRAP.md)) and ask the human before proceeding.

## The session ritual (do this EVERY session, before new work)

This is the enforced open-middle-close shape from the methodology:

**A. OPEN — the Validation & Advancement Gate comes first:**
1. **Close out the prior story.** Read `governance/RUNBOOK.md`. If the previous
   story is 🟡 (in progress, pending validation), get the human's live result.
   - On **pass** → record its dated `Validation Result` line and flip its status
     🟡 → ✅ (per the runbook's Story Close-Out Procedure).
   - On **fail / incomplete** → keep it 🟡 and **re-focus this session on fixing
     and re-validating that story**. Do **not** move on.
2. **Check the advancement gate.** The story you intend to work **cannot begin**
   until **every** story in its `Depends on` column is ✅. If any dependency is not
   ✅, **stop and tell the human** — do not start anyway. (No override.)

**B. MIDDLE — one story to completion:**
- Take exactly **one** story. Design → build → **validate live** → you **record**
  the result in the runbook → only then flip the status.
- **You do not grade your own paper.** As the builder, you must NOT author the
  pass/fail check or seal the verdict for your own work. The Definition of Done and
  the live steps are authored by an **independent validator** (a fresh chat / a
  second AI / the human) using
  [`DOCS/VALIDATOR_BRIEF_TEMPLATE.md`](DOCS/VALIDATOR_BRIEF_TEMPLATE.md); the human
  runs the steps on the real system and reads the raw output. You record the sealed
  verdict — you never self-certify (see `governance/METHODOLOGY.md` §4a).
- Push work to a **branch and open a pull request**; **never push to the protected
  main line directly**. Merging code does **not** make a story done.
- Keep it real: no mock data or placeholder services standing in for real ones
  unless the human explicitly agrees.

**C. CLOSE — the warm handoff (mandatory, never skip):**
- Author the **next** story's brief and prompt under `DOCS/session-briefs/`
  (from the templates in `DOCS/`), including a **Lessons Learned / Carry-Forward**
  section with what *actually* happened this session: bugs and their fixes,
  decisions that mattered, the corrected true state of the system, and watch-items.
  A handoff with an empty lessons section is incomplete.

## Hard rules (do not violate)

- **Never self-certify a story as done.** The human is the validator; you record
  the result. No recorded, confirmed pass → the story stays 🟡.
- **Never advance past a failed or unproven story.** Fix and re-validate it first.
- **Never start a story whose dependencies are not all ✅.**
- **Never push to `main` directly** or force-push it. Branch + PR only.
- **Verify the deployed/produced artifact, not just the local file.** After a
  change, confirm the thing that actually runs contains the change.
- **State your operational context on every command block** (environment / account
  / region), and confirm the target before any destructive action.
- **Build from a known-good point; revert, don't forward-patch.** When a slice goes
  bad, return to the last restore point (see `governance/RESTORE.md`).
- **Keep the ledger honest.** Status changes ride their own small commits; if the
  main line and a status disagree, the main line wins — reconcile it.

## Keeping the docs consistent (enforcement)

This repo ships gates that a pre-commit hook (and CI) run for you:

- **`scripts/check_docs.py`** — fails if the governance docs drift: the RUNBOOK and
  PLAN disagree on the story set, a ✅ story has no recorded validation line, a
  referenced decision ID doesn't exist, a stray `{{placeholder}}` is left in a
  living doc, or a doc links to a missing file.
- **`scripts/check_repo_map.py`** — keeps `docs/REPO_MAP.md` (the structure map)
  accurate; the hook regenerates it for you on each commit.

Run `python3 scripts/check_docs.py` before you consider a status change complete.
If a gate fails, fix the cause — do not bypass it.

## First-time setup (only if this repo is not set up yet)

If the governance files still have `{{placeholders}}`, the project hasn't been
initialized. **This is Story 0 — see [`BOOTSTRAP.md`](BOOTSTRAP.md) for the full
procedure.** In short, and in this order (PLAN first, RUNBOOK second):

1. **The planner produces `governance/PROJECT_PLAN.md`** — the *what/why* comes from
   the strategic side of the brain. The human feeds
   [`DOCS/PLANNER_BRIEF_TEMPLATE.md`](DOCS/PLANNER_BRIEF_TEMPLATE.md) to a planner AI
   (e.g. Gemini) and iterates until the plan is well-formed. **If the plan is still
   the blank template, stop and ask the human to run this first — do not invent the
   plan yourself.**
2. **You (the executor) derive `governance/RUNBOOK.md` from the plan** — one row per
   story, `Depends on` set, all ⬜, each phase Gate copied in. **Keep the Validation
   & Advancement Gate and Story Close-Out sections verbatim.**
3. Replace remaining `{{placeholders}}` across `governance/`; tailor `RESTORE.md` +
   `BOM.md` to this project's tech.
4. Validate Story 0: `python3 scripts/check_docs.py` must PASS and a human confirms
   the runbook mirrors the plan. Record it, flip Story 0 ✅.
5. `git config core.hooksPath .githooks`, then author Story 1's warm handoff.

The Story 0 brief + prompt ship ready-to-use at
`DOCS/session-briefs/story-0-bootstrap.md` and `story-0-PROMPT.md`. Then run Story 1
using the session ritual above.

---

*This project uses the "work-like-this" operating system from
[SDD-repo-kit](https://github.com/warrenrutledge64/SDD-repo-kit). The discipline —
not the tooling — is what makes progress real.*
