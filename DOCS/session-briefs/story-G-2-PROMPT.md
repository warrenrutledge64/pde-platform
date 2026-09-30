# Session Prompt — Story G-2 (executor-facing)

> Source of truth: [`story-G-2-brief.md`](story-G-2-brief.md). Lean by design (RD-008).

```
You are the execution agent for the Platform Delivery Engine (PDE) project. This is a
GOVERNANCE story (G-2), not pipeline work. Read this fully before acting.

# FIRST — close out G-1
Read RUNBOOK.md. G-1 must be ✅ with a recorded independent audit verdict + findings.
If G-1 is not done, STOP — G-2 needs the findings. (No override.)

# OBJECTIVE
Apply G-1's ACCEPTED findings: trim the prompt/handoff templates to load-bearing-only,
move reference material to linked docs, put must-not-miss guardrails early, de-duplicate
across brief/prompt/handover. Mirror the accepted trims UPSTREAM into SDD-repo-kit
(reusable-OS). Record the LEAN PASS (RD-008/§4a; AI RMF MEASURE-2.7).

# GUARDRAILS
- Apply only what the auditor flagged + the stakeholder accepted. DON'T over-trim: a
  guardrail marked keep-but-shorten stays (shorter + earlier, not gone).
- Instance AND upstream (SDD-repo-kit) — keep them in sync or the reusable layer drifts.
- Branch + PR; never push to main. check_docs + tests green before PR.

# DEFINITION OF DONE — a PASS/FAIL GATE
- Done = trimmed templates on main (instance + upstream) AND a recorded lean pass
  (reduction quantified, zero load-bearing loss; stakeholder confirms trims match the
  accepted findings). Set G-2 ✅.
- This CLEARS the "prompts are optimized" gate → Story 1.1's LIVE validation may proceed.

# THEN
- Update AI RMF Profile MEASURE-2.7 evidence with the recorded pass if warranted.
- Warm handoff: confirm Story 1.1's LIVE-RUNBOOK + validator handover are current
  against the trimmed templates, so 1.1's live validation starts clean.
```
