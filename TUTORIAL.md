# Tutorial — run a project the disciplined way (with the TinyLink example)

> A hands-on walkthrough. It teaches the whole workflow by pointing at a **real,
> filled-in example project — TinyLink** — that ships in this kit at
> [`example-project/`](example-project/). Read a step, then open the example file it names to see
> exactly what "good" looks like.
>
> **Time:** ~20 minutes to read; you can follow along in a scratch repo.
> **You need:** Git and Python 3 (`python3 --version`). Nothing to install.

---

## The one idea this whole system protects

**"Done" means validated, not merged.** A task is finished only when its result is
checked on the live system and that result is *written down*. Everything below is
machinery to make that habit automatic. Keep it in mind and the rest follows.

---

## Part 1 — The vocabulary (2 minutes)

Four words appear everywhere:

- **Story** — the smallest useful, separately-checkable slice of work (e.g. "add
  the redirect endpoint"). You do **one at a time**.
- **Phase** — a group of stories that reaches a milestone (e.g. "Foundation").
- **Validation** — a human running a real check on the live system and confirming
  the outcome. Not "the tests pass locally" — an actual check of the real thing.
- **Restore point** — a labelled known-good state (code + deployed state) you can
  return to instead of forward-patching a broken build.

Two roles do the work:

- **Planner** — decides *what's next and why* (can be you, or an AI like Gemini).
- **Executor** — builds exactly one story and reports back (usually an AI).

They hand off through **one written brief + prompt per story**.

---

## Part 2 — Meet the example

Open [`example-project/README.md`](example-project/README.md). TinyLink is a tiny URL-shortener
API, deliberately captured **mid-flight** so you see the system in a *real* state,
not a polished-finished one:

- **Phase 1 (Foundation)** — ✅ done and validated.
- **Phase 2 (Shorten & Redirect)** — 🟡 in progress: one story done, one pending,
  one not started.

The five files that *are* the project's memory:

| File | It answers |
|---|---|
| [`example-project/governance/PROJECT_PLAN.md`](example-project/governance/PROJECT_PLAN.md) | What are we building, in what order, and what did we decide? |
| [`example-project/governance/RUNBOOK.md`](example-project/governance/RUNBOOK.md) | What's the status of every story? What's next? Is it *really* done? |
| [`example-project/governance/BOM.md`](example-project/governance/BOM.md) | What exists / is deployed, and which restore point does it map to? |
| [`example-project/governance/RESTORE.md`](example-project/governance/RESTORE.md) | How do we return to a known-good state? |
| [`example-project/DOCS/session-briefs/`](example-project/DOCS/session-briefs/) | The per-story briefs + prompts, including the warm handoff. |

---

## Part 3 — How to read the RUNBOOK (the heart of it)

Open [`example-project/governance/RUNBOOK.md`](example-project/governance/RUNBOOK.md) and find the
Phase 2 table:

```
| 2.1 | POST /shorten          | 1.2 | ✅ | 2026-01-12 | |
| 2.2 | GET /{code} redirect   | 2.1 | 🟡 |            | |
| 2.3 | Abuse protection       | 2.2 | ⬜ |            | |
```

Read it like this:

- **2.1 is ✅** — scroll to its detail block. It has a **`Validation Result:` line
  that is dated and confirmed**: *"pass — live `POST /shorten` returned a 7-char
  code … 2026-01-12, confirmed by maintainer."* **That line is what makes the ✅
  legitimate.** No line → no ✅.
- **2.2 is 🟡** — its `Validation Result` says **`pending`**. The work may even be
  written, but until a human validates it live and records the result, it stays
  🟡. This is the system refusing to lie.
- **2.3 is ⬜** and **depends on 2.2**. Because of the **advancement gate**, 2.3
  *cannot start* until 2.2 is ✅. (It's also waiting on decision RD-003 to be
  ratified — see the plan.)

That's the entire status model, visible in five lines.

---

## Part 4 — Walk one story end-to-end (2.2, the redirect)

This is the loop you'll repeat for every story. Follow it against the example.

### Step 0 — Open the session: the gate comes first

Before touching new work, the executor does two checks (from `AGENTS.md`):

1. **Close out the prior story.** Is 2.1 ✅ with a recorded pass? Yes (2026-01-12).
   Nothing owed.
2. **Advancement gate.** Does 2.2's dependency (2.1) show ✅? Yes → clear to start.
   *(If it weren't, the executor stops and says so — it does not start anyway.)*

### Step 1 — Read the brief you were handed

Open [`example-project/DOCS/session-briefs/story-2.2-redirect.md`](example-project/DOCS/session-briefs/story-2.2-redirect.md).
Notice it was **written during the *previous* session** (while closing 2.1) — that's
the *warm handoff*. Its **Lessons Learned** section carries real context forward:
"idempotency (RD-002) was almost missed in 2.1 — watch for decisions that live in
the plan but not yet in the code." The next session starts warm, not cold.

The matching executor prompt is
[`story-2.2-PROMPT.md`](example-project/DOCS/session-briefs/story-2.2-PROMPT.md) — the tight,
operational version you'd paste to an AI to start the session.

### Step 2 — Build it (one story, to completion)

The executor builds `GET /{code}`: 301 to the original URL, 404 for an unknown
code, plus CI tests. It pushes to a **branch and opens a pull request** — it does
**not** push to `main`. Merging that PR does **not** make the story done.

### Step 3 — Validate, live (and independently)

Look at the brief's Definition of Done: *"create a code via `POST /shorten`, then
`GET /{code}` live returns a 301 to the original URL; an unknown code returns
404."* The **maintainer runs that real check** against the running service and
confirms the outcome. This is the step no test suite can substitute for.

Crucially, **the builder does not grade its own paper.** The pass/fail check should
be authored by an *independent* validator — a fresh chat, a second AI (e.g. the
planner brain / Gemini), or you — using
[`DOCS/VALIDATOR_BRIEF_TEMPLATE.md`](DOCS/VALIDATOR_BRIEF_TEMPLATE.md). You paste it
the requirement (in your own words) and the raw change, and it authors the
Definition of Done and the live steps *blind*, then seals PASS / FAIL /
INCONCLUSIVE from the raw output you run. Why: whoever frames what gets tested holds
the real power — if the executor writes its own rubric, a green result only proves
it agreed with itself (`METHODOLOGY.md` §4a).

### Step 4 — Record the result, then flip the status

Only now does the executor edit the runbook, in a **small dedicated commit**:

- On **pass** → replace 2.2's `pending` line with a dated one
  (`pass — GET /{code} 301'd to the original URL; unknown code 404; …, <date>,
  confirmed by maintainer`) and change 2.2's row and detail header 🟡 → ✅.
- On **fail** → change nothing to ✅. Keep it 🟡, record `FAIL — <what failed>,
  <date>`, and the **next session re-focuses on 2.2**, not 2.3.

*(Work and status are separate commits on purpose: the code rides one PR, the
status flip rides its own small, fast-merging PR, so the main line never claims
something is done before it is.)*

### Step 5 — Close the session: write the next warm handoff

Before stopping, the executor authors **2.3's** brief + prompt, including a Lessons
Learned section from *this* session — and flags that 2.3 is blocked until decision
RD-003 is ratified. A session that ends without the next handoff is incomplete.

That's one full turn of the loop. Every story is the same shape:
**gate → brief → build → validate live → record → warm handoff.**

---

## Part 5 — Restore points (when a phase closes)

Look at the bottom of Phase 1 in the runbook, and at
[`example-project/governance/BOM.md`](example-project/governance/BOM.md) section 4:

```
| restore/phase-1-green | 1 | 2026-01-09 | a1b2c3d | manifests/phase-1.json | Foundation validated … |
```

When Phase 1's end-of-phase check passed, three things happened together: a
`restore/phase-1-green` tag was cut at the validated commit, a state manifest was
captured, and the inventory row was added. Now, if Phase 2 goes sideways, you can
**return to that known-good point** — code *and* deployed state — instead of piling
fixes onto a broken base. The procedure is in
[`example-project/governance/RESTORE.md`](example-project/governance/RESTORE.md).

---

## Part 6 — Now do it for real (your project)

The foundational documents come *first*, and they come from **two sides of the
brain**. This is **Story 0** — its own guide is [`BOOTSTRAP.md`](BOOTSTRAP.md). The
short version:

1. **Install the kit** into your repo (see the [README](../README.md) quick start),
   then turn on the hook: `git config core.hooksPath .githooks`.
2. **The PLAN comes from the *planner* (the other brain).** Fill in
   [`DOCS/PLANNER_BRIEF_TEMPLATE.md`](DOCS/PLANNER_BRIEF_TEMPLATE.md) and paste it to
   a planning AI (e.g. Gemini). Iterate until it produces a well-formed
   `governance/PROJECT_PLAN.md` — use the TinyLink plan as your "what good looks
   like." (Why the other brain: planning is strategic work — scope, sequencing,
   risk — kept deliberately separate from execution.)
3. **The RUNBOOK is derived by the *executor* from that plan** — one row per story,
   dependencies set, all ⬜, gate sections kept verbatim. **Plan first, runbook
   second, always.** (Story 0's brief + prompt ship ready-to-use at
   `DOCS/session-briefs/story-0-bootstrap.md` and `story-0-PROMPT.md`.)
4. **Validate Story 0:** `python3 scripts/check_docs.py` must pass and you confirm
   the runbook mirrors the plan. Record it → Story 0 is ✅.
5. **Then run Story 1** using the loop from Part 4 — build, validate live, record,
   warm handoff.

> The checker has your back throughout: commit, and if you left a `{{placeholder}}`
> or marked a story ✅ with no recorded validation, `scripts/check_docs.py` (run by
> the pre-commit hook) blocks it and tells you what to fix.

---

## Cheat sheet

- One story at a time, to completion.
- A story goes ✅ **only** with a dated, confirmed `Validation Result` in the runbook.
- A story can't start until its `Depends on` are all ✅.
- Never push to `main`; branch + PR. Work and status flips are separate commits.
- Fail → stay on the story; don't advance.
- End every session by writing the next story's brief + prompt (with real lessons).
- Phase close → cut a restore point + update the inventory.

Everything here is enforced or documented in `AGENTS.md`, the RUNBOOK's binding
gate, and the pre-commit gates. The discipline — not the tooling — is what makes
progress real.
