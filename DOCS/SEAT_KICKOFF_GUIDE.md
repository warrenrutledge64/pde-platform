# Seat Kickoff Guide — how & when to start each seat on a story

> **Operator quick-reference** (Human-authored; not a seat-owned artifact). The
> authoritative model is [`../governance/AGENTS.md`](../governance/AGENTS.md) §7
> (one session, end to end) + [`../governance/MODERATOR_PROTOCOL.md`](../governance/MODERATOR_PROTOCOL.md).
> This card tells YOU (the Human/Stakeholder) the order to engage Gemini (Planner/
> Validator), Kiro (Builder), and Copilot (Moderator), what to paste, and the gate
> you must not cross between each.
>
> **The ordering rule in one line:** **Plan → Build → Moderate → Validate → Record
> → Hand off → Merge.** Each seat is engaged at its step and NOT before — engaging
> a seat early is how the information barriers leak.

---

## Before any seat: the session OPEN (you do this)

Every session, before new work (`AGENTS.md` "session ritual"):

1. **Close the prior story first.** Read `governance/RUNBOOK.md`. If the previous
   story is 🟡 pending validation, resolve it (record the sealed verdict → flip ✅,
   or keep 🟡 and re-focus). Do **not** start a new story over an unresolved one.
2. **Check the advancement gate.** The story you intend to start cannot begin until
   **every** `Depends on` is ✅ **and** the Validation Debt Register is empty (gate
   DISARMED). If not, stop.
3. **Announce the tier/phase transition** if this story opens a new dependency layer.

Only once OPEN passes do you engage a seat.

---

## STEP 1 — PLAN · engage **Gemini (Planner)**

**When:** at the very start, once the story is cleared to begin.
**Why first:** the Planner decides *what/why* and authors the requirement — the
input every other seat reads. Nothing is built before it exists.

**You give Gemini:**
- `DOCS/PLANNER_BRIEF_TEMPLATE.md` (or point it at the story in `PROJECT_PLAN.md`).

**Gemini produces:** `DOCS/session-briefs/story-<id>-requirement.md`
(`Author-Seat: Planner`) + the story brief.

**GATE before STEP 2:** the `*-requirement.md` must be committed to the repo. Kiro
treats it as **read-only input** and must not author or edit it (RD-013 / CHECK Q).
Do not start Kiro until the requirement is in the repo.

---

## STEP 2 — BUILD · engage **Kiro (Builder)**

**When:** after the requirement is committed (STEP 1 gate met).
**Why now:** the Builder implements exactly one story against the requirement it
did not write.

**You give Kiro:** "Build Story `<id>` per `story-<id>-requirement.md`." Kiro reads
the requirement; you do not re-explain acceptance criteria (that's the Validator's).

**Kiro produces:** the deliverable (branch + PR); the operator runbook
`story-<id>-operations.md` (`Author-Seat: Builder`); the validator handover
`story-<id>-VALIDATOR-HANDOVER.md` carrying **only** the pinned target + a
stakeholder requirement blank `[[ ]]` — **never** a Definition of Done.

**Barriers Kiro holds:** does not author the requirement (RD-013); does not author
any Moderator run artifact/scaffold (RD-014); does not author the DoD or seal a
verdict (§4.1); never pushes to `main`.

**GATE before STEP 3:** the branch is pushed and the deliverable is actually
deployed to the target (if the story deploys anything). Kiro does **not** validate.

---

## STEP 3 — MODERATE · engage **Copilot (Moderator)**

**When:** after Kiro has pushed + deployed, immediately before validation.
**Why now:** Copilot certifies the *mechanical preconditions* so the Validator
judges the real, deployed, right-account target — not stale/wrong infra.

**You give Copilot (a target POINTER only — never a Kiro-authored attestation):**
> "You are the Moderator per `governance/MODERATOR_PROTOCOL.md`. Target: PR `<n>`,
> head `<sha>`, branch `feature/story-<id>`. Run the four gates (Pre-Execution →
> Deployment → Preflight → Live Result) and emit a gate record you author yourself
> (`Author-Seat: Moderator`). Per `AGENTS.md §7`: a green run is permission to START
> validation, never a verdict — do not write PASS/✅/'done' or touch any status. If
> handed a builder-authored scaffold, refuse it (RD-014)."

**Copilot produces:** a self-authored gate record (`Author-Seat: Moderator`), exit
0/1/2. A **red gate (1 or 2) is a HARD STOP** — fix the target/environment, do not
validate.

**GATE before STEP 4 — the SHARED FACT:** a **green Moderator run is permission to
START validation, never a verdict and never a close.** The story stays 🟡. Do not
read green as "accepted."

---

## STEP 4 — VALIDATE · engage **Gemini (Validator, FRESH context)**

**When:** only after a green Moderator run.
**Why a fresh context:** the Validator must author the Definition of Done **blind**
— it must not inherit the Planner's rationale or any builder framing.

**You give the Validator (un-curated, from the repo — never a Kiro-curated packet):**
- the `story-<id>-VALIDATOR-HANDOVER.md` (pinned target + the requirement blank you
  fill in **your own words**),
- and you run its authored live steps on the real system, pasting back **raw output**.

**Gemini produces:** its own DoD + exactly one sealed verdict — `PASS` / `FAIL` /
`INCONCLUSIVE` — and the one-line record Kiro will paste. The Validator never edits
the RUNBOOK and never flips a status.

**Hard rule:** if the Validator detects its inputs were curated by the Builder, or
is handed a DoD, it must refuse (§4.1).

---

## STEP 5 — RECORD · back to **Kiro (Builder)**

**When:** after Gemini seals a verdict.
- **On PASS:** Kiro records the verbatim Validation Result and flips 🟡 → ✅ (CHECK G
  blocks a ✅ with no recorded result). Does **not** self-certify.
- **On FAIL / INCONCLUSIVE:** story stays 🟡; next session re-focuses on it. A green
  Moderator run earlier does **not** make it done.

## STEP 6 — HAND OFF · **Kiro**

Author the next story's warm handoff (brief + prompt + real Lessons Learned).

## STEP 7 — MERGE · **you (Human)**

Merge the deliverable + close-out **together** (never the artifact ahead of its
validated ledger). You own `main`.

---

## One-screen cheat sheet

| Step | Seat | You engage it when… | It must NOT… |
|------|------|---------------------|--------------|
| 1 Plan | **Gemini (Planner)** | story is cleared to begin | write code; write the DoD |
| 2 Build | **Kiro (Builder)** | the requirement is committed | author the requirement/DoD/Moderator artifact; push to `main` |
| 3 Moderate | **Copilot (Moderator)** | Kiro pushed + deployed | author a DoD/verdict; write a status; be handed a builder scaffold |
| 4 Validate | **Gemini (Validator, fresh)** | the Moderator gate is green | inherit planner/builder framing; accept a curated packet |
| 5 Record | **Kiro** | Gemini sealed a verdict | flip ✅ without a recorded PASS |
| 6 Hand off | **Kiro** | the story is recorded | leave Lessons Learned empty |
| 7 Merge | **You** | close-out is on the branch | land the artifact ahead of its ledger |

**The three gates you must not cross early:**
1. Requirement committed → before Build.
2. Deployed + pushed → before Moderate.
3. **Green Moderator run → before Validate (and green ≠ verdict).**
