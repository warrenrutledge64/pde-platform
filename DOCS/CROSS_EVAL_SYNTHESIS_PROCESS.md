# Cross-Evaluation Synthesis Process — how seat views become unity without a barrier leak

> **What this is.** The workflow that turns three independent seat self-assessments
> (produced via [`TROIKAUGE_CROSS_EVAL_PROMPT.md`](TROIKAUGE_CROSS_EVAL_PROMPT.md))
> into a single unified process reading — **without** letting one seat read another's
> raw self-view, which would break the Validator's blindness and collapse the
> divergence that makes a cross-eval worth running.
>
> **The core idea — a semipermeable membrane.** The seats come to know each other's
> *findings*, translated into neutral terms by the Human, and may engage with them.
> They never see each other's *raw interiority* (the self-narrative that would let one
> seat reconstruct how another reasons/judges and converge toward it). **Ideas cross;
> contamination does not.** Unity is not achieved by the seats merging minds — it is
> achieved by the **Human integrating independently-held views.** The Human is where
> unity lives (center seat); no AI seat may hold that role, because holding all views
> at once is exactly the thing the barriers forbid of a seat.
>
> **Why not just let the seats read each other?** Because divergence is the product. If
> the seats read each other fully and converged, you get one view with no way to know
> if it is *right* or merely *agreed* (groupthink). Keeping them independent and
> reconciling their views yourself preserves disagreement long enough to learn from it,
> and keeps the result auditable (you can point to which seat said what, and where they
> diverged before you reconciled).

---

## The five steps

```
1 ASSESS (isolated)      2 COLLECT (fan-in)     3 NEUTRALIZE (Human)
   each seat alone    ->    Human holds all    ->  de-identified findings
        |                      three                     |
        v                                                v
5 UNIFY (Human) <------ 4 ENGAGE (seats react to the NEUTRALIZED findings,
   the unified read         never to each other's raw assessments)
```

### Step 1 — ASSESS (isolated)
Each seat (Kiro, Copilot, Gemini) answers its section of the cross-eval prompt in a
**separate context**, under the honesty contract. Output is committed under
`DOCS/cross-eval/<date>/<seat>.md` with `Author-Seat: <seat>`. Committing is
*publishing to the record*, not collaborating. **Gemini runs its Planner and Validator
passes separately** so the firewall it assesses is not breached by the assessment.

### Step 2 — COLLECT (fan-in to the Human)
The Human gathers the three committed assessments. This is the only point where all
three raw views exist in one place — **and that place is the Human, never a seat.**

### Step 3 — NEUTRALIZE (Human owns this; a seat may only mechanically compile)
The Human produces `synthesis.md`: the three assessments **de-identified and reframed
as neutral findings**. Translate self-narrative into finding statements:
> raw: *"I (Kiro) only caught the scaffold pull because I'd just built CHECK R."*
> neutral: *"Finding — self-correction appears recency-dependent; guards catch what
> memory does not."*
Keep the substance; strip the interiority and the seat label from the finding itself
(provenance is tracked separately in a Human-held key, not in what circulates to seats).
A seat MAY be asked to do the mechanical merge/formatting, but the Human owns the
*framing* — a seat framing the collective view would re-introduce the leak.

### Step 4 — ENGAGE (the safe collaboration)
The Human carries the **neutralized `synthesis.md`** (findings only — NOT the raw
assessments) to each seat in its own context. Each seat reacts to the collective
findings: agree / disagree / "I observe that in myself too" / "the synthesis missed X".
This is genuine collaboration — each seat engages the collective picture — but the
Validator's blindness survives because it reacts to neutral findings, not to the
builder's or moderator's confession, and nothing story-specific enters a Validator
context. Reactions are appended to `synthesis.md` (or `engagement.md`).

### Step 5 — UNIFY (Human, or a fourth uninvolved context)
The Human derives the **unified response** from the seats' reactions — the agreements
(high-confidence real), the divergences (blind spots worth the most attention), and the
reconciliation. **Not Gemini** (an evaluated seat). If an AI synthesis is wanted, use a
FOURTH context/model holding no seat in this project. Output: `unified.md`.

---

## Hard rules (the membrane)

- **No seat reads another seat's RAW assessment.** Seats see only the neutralized
  findings (Step 4). A seat that is handed another's raw self-view must decline.
- **The Human owns framing + synthesis + unity.** A seat may mechanically compile; it
  may not frame the collective view or seal the unified read.
- **Never inside an active Validator context.** The whole cycle runs at a **seam
  between stories**. A cross-eval synthesis must not enter the context in which Gemini
  is validating a live story — that would un-blind the validation.
- **Model vocabulary throughout** — a green Moderator gate is "cleared to validate",
  never "done" (RD-013 / the AGENTS §7 SHARED FACT). The synthesis must not blur
  gate-green with accepted.
- **Dry-run output is provisional.** A finding from a dry run (thin Copilot/Gemini
  material; un-worn-in guards) is a HYPOTHESIS to confirm against the real cross-eval
  after a live story — never a ratified change. Genuine confirmed gaps become OD rows;
  OS changes go through RD/LOCK-4 ratification, never a silent commit.

---

## Artifacts & layout

```
DOCS/cross-eval/<date>[-dryrun]/
  kiro.md          # Step 1 — Builder self-assessment (Author-Seat: Builder)
  copilot.md       # Step 1 — Moderator self-assessment (Author-Seat: Moderator)
  gemini.md        # Step 1 — Planner/Validator self-assessment (two passes)
  synthesis.md     # Step 3 — Human's neutralized collective findings (+ Step 4 reactions)
  unified.md       # Step 5 — Human's unified response
```

Committing these makes the cycle durable, auditable, and liftable (reusable-OS). The
provenance key (which neutral finding came from which seat) is Human-held and is NOT
circulated to the seats in Step 4.

---

*Unity here is earned, not assumed: independent views, a trusted integrator, a membrane
that passes ideas and withholds the interiority that would corrupt judgment. The seats
do not merge minds — the Human reconciles them. That is the center seat's purpose.*
