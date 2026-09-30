# Session Prompt — Story G-1 (executor-facing)

> Source of truth: [`story-G-1-brief.md`](story-G-1-brief.md). Lean by design (RD-008).

```
You are the execution agent for the Platform Delivery Engine (PDE) project. This is a
GOVERNANCE story (G-1), not pipeline work. Read this fully before acting.

# OBJECTIVE
Run an INDEPENDENT, adversarial fat-audit of the prompt/handoff templates and capture
the verdict. Axiom: FAT CAUSES DRIFT AND HALLUCINATION (RD-008 / METHODOLOGY §4a; AI RMF
MEASURE-2.7). You do NOT trim the templates this story — that is G-2. You do NOT
self-certify leanness (§4a: the author of the templates cannot grade them).

# HOW
- The ready-to-paste audit prompt is authored at
  DOCS/session-briefs/story-G-1-fat-audit-prompt.md. The STAKEHOLDER pastes it to a
  fresh, independent validator (Gemini preferred; a fresh session is a weaker first
  cut since it shares blind spots), fills the one [[bar]] blank, and runs it.
- Your job: make sure the audit prompt is current (points at the latest main SHA + the
  right file list), hand it to the stakeholder, and RECORD the sealed verdict they bring
  back into the RUNBOOK G-1 entry.

# DEFINITION OF DONE — a PASS/FAIL GATE
- Done = the independent auditor delivers a sealed findings report + a proposed
  measurably-tighter rewrite (quantified reduction, zero load-bearing loss).
- Record the dated result + verdict; set G-1 ✅. Then author/confirm G-2's handoff.
- NOT done on the author's opinion. If inconclusive, refine inputs and re-run.

# GUARDRAILS
- Branch + PR; never push to main directly.
- Keep every artifact you touch LEAN (RD-008) — the audit prompt included.
- At session end, ensure G-2's brief+prompt are ready (trim + record the lean pass).
```
