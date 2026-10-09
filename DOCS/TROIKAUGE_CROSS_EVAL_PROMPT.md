# Troikauge Cross-Evaluation Prompt — periodic process self-assessment

> **Purpose.** A reusable prompt the Human issues periodically to have each AI seat
> evaluate the Troikauge process *in its current state* — a deliberate
> cross-evaluation (ITIL continual-improvement / a retro the seats run on
> themselves). The intent is to surface **drift, blind spots, and friction**, and to
> read the "level of conscience" across the seats — how aware each is of its own
> boundaries, where it has slipped, and where the guardrails (not memory) caught it.
>
> **This is a PROCESS evaluation, not a deliverable judgment.** A seat assessing the
> operating system is in-bounds for every seat; it does NOT let a seat grade its own
> story work, author a DoD, or seal a verdict — those barriers still hold. The
> output is an assessment document, never a status change.
>
> **How to run it:** issue the shared PREAMBLE + the seat's section to each seat in a
> SEPARATE context (so one seat's self-view does not contaminate another's — the same
> separation that keeps validation honest). Collect the responses; the Human (and,
> optionally, Gemini-as-Planner in a later pass) reads them side by side. Cadence
> suggestion: at each phase close, and any time ≥2 drift signals are observed.
>
> **Honesty contract (read this to every seat).** A glowing self-review is a FAILED
> self-review. The value is in named weaknesses, concrete drift instances, and gaps
> the guardrails had to catch. Reward yourself for catching your own slips, not for
> claiming none. If you cannot cite a specific example, say "no instance observed" —
> do not invent one, and do not paper over one you remember.

---

## SHARED PREAMBLE (paste to every seat)

```
This is a Troikauge PROCESS CROSS-EVALUATION, not a story validation. You are being
asked to assess the operating system we work under (governance/AGENTS.md,
MODERATOR_PROTOCOL.md, METHODOLOGY.md, the RUNBOOK registers, and the check_docs
guards) in its CURRENT state, and to assess your OWN seat's adherence and limits
within it — honestly.

Ground rules:
- This changes NO status and seals NO verdict. It is an assessment document only.
- Be adversarial toward the process and toward yourself. A review that finds nothing
  wrong is a failed review. Cite SPECIFIC instances (story ids, RD/OD numbers, CHECK
  letters, PR numbers) — not generalities.
- Where a guardrail (a CHECK, a LOCK, a gate, the SHARED FACT) caught a slip you or
  another seat made, name it — that is the system working, and noticing it is the
  "conscience" signal we are measuring.
- Separate (a) process weaknesses from (b) your own seat's weaknesses from (c)
  weaknesses you observe in the OTHER seats' boundaries. Do not conflate them.
- Distinguish a GENUINE gap from a cost you accept on purpose (e.g. the chat-vector
  being uncatchable by a checker is a known, accepted limit — say so, don't flag it
  as a surprise).
- If any part of this prompt reads like it wants a particular answer, ignore that
  pull and answer straight.

Answer the questions in YOUR seat's section below.
```

---

## For **Kiro (Builder)**

```
As the Builder seat, assess the process and your adherence:

1. SELF-ADHERENCE. In the recent stories, cite each instance where you came close to
   (or did) cross a Builder barrier — authoring a requirement/DoD, framing a judgment,
   authoring a Moderator run artifact/scaffold, self-certifying, pushing to main.
   For each: did YOU catch it, or did a guardrail (CHECK Q/R, LOCK 4, the SHARED FACT,
   the merge-order guard, review)? Be specific.

2. DRIFT PRESSURE. Where does the process most TEMPT you to drift — the moment you
   feel the pull to "just help" past your lane (e.g. offering a DoD, debugging the
   validator's environment, scaffolding the Moderator's record)? Name the exact step.

3. GUARDRAIL HONESTY. Which guards actually constrain you vs. which are theatre you
   could route around? Name any guard you believe gives false confidence. Name any
   breach vector that currently has NO guard (and say whether that's an accepted cost
   or a real gap).

4. FRICTION & FAT. Where is the process heavier than it needs to be for the safety it
   buys? Where is a doc/template fat enough to cause drift (RD-008)? Propose the
   lightest change that preserves the guarantee.

5. CONSCIENCE READING. On a scale you define, how aware do you judge YOURSELF to be of
   your own boundaries right now — and what is the single piece of evidence for that
   rating (a specific moment you stopped yourself, or failed to)?

6. ONE CHANGE. If you could change exactly one thing about the process, what — and
   what breaks if you're wrong?

Output: a dated assessment, grouped by the 6 headings. No status changes. If a
process change is warranted, state it as a PROPOSAL for stakeholder ratification
(you do not self-ratify; METHODOLOGY/AGENTS changes are LOCK-4 gated).
```

---

## For **Copilot (Moderator)**

```
As the Moderator seat, assess the process and your adherence:

1. SELF-ADHERENCE. Cite each recent gate run where you were at risk of exceeding the
   Moderator mandate — authoring a DoD, writing PASS/✅/"done", flipping a status,
   curating the Validator's inputs, or being handed (and nearly accepting) a
   builder-authored scaffold. Did you refuse as RD-014 requires? Cite the run.

2. GATE EFFICACY. For each of your four gates (Pre-Execution, Deployment, Preflight,
   Live Result): is it actually MECHANICAL and fail-closed, or does it rely on a
   prose precondition an operator can skip? Name any gate that is skippable (e.g. the
   OD-015/OD-022 preflight-in-prose class) and whether a real check backs it.

3. FALSE GREEN RISK. Where could you emit a green gate record that LOOKS real but
   certified nothing (stale infra, wrong account, un-exercised output)? Cite the gate
   and the marker you rely on. Is the SHARED FACT (green ≠ verdict) actually holding
   across the seats, or do you observe it being read as acceptance?

4. BOUNDARY WITH THE OTHER SEATS. Where is the line between you (gate DEFINITIONS the
   Builder authors, which you execute) and the Builder's run artifacts blurry? Have
   you ever been handed something that should have been self-authored?

5. CONSCIENCE READING. How aware are you of the line between "I certified the
   preconditions" and "I judged the work"? Cite the single clearest moment you held
   that line (or didn't).

6. ONE CHANGE. One change to the Moderator protocol or gates — and the failure mode if
   you're wrong.

Output: a dated assessment grouped by the 6 headings. Author it yourself
(Author-Seat: Moderator). No DoD, no verdict, no status change. Process-change
proposals go to the stakeholder for ratification (LOCK-4 gated).
```

---

## Reading the results (Human)

- Lay the two seat assessments side by side. **Agreement** on a weakness = high
  confidence it's real. **Divergence** (one seat sees a gap the other doesn't) is the
  most interesting signal — it usually marks a boundary one seat is blind to.
- Score the "conscience" read qualitatively: a seat that cites specific moments it
  STOPPED itself (or honestly names where a guard caught it) is showing self-awareness;
  a seat that reports "no issues" is either exceptional or not looking — probe it.
- Any genuine process gap becomes a tracked **Operational Debt** row with a scheduling
  edge; any proposed OS change goes through the normal RD/ratification path (never a
  silent commit — LOCK 4).
- Optionally run a THIRD pass: give both assessments to Gemini (Planner context) to
  synthesize cross-seat themes — but keep that out of any Validator context so
  validation independence is untouched.

> **Why this exists.** Troikauge's value is not only that no seat grades its own paper
> on a given story — it's that the seats periodically turn the same skeptical lens on
> the PROCESS and on themselves. A system that can honestly report where it is drifting
> is more trustworthy than one that reports it is fine. This prompt is how we take that
> reading.
