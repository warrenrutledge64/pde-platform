# Session Brief — Story G-1: Independent fat-audit of the prompt/handoff templates

> Populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md) (Governance G- series).
> Lean by design (RD-008): this brief links its sources; it does not restate them.

## Story G-1 — Independent adversarial fat-audit of the prompt/handoff templates

| Field | Value |
|-------|-------|
| **Type** | Governance (G-series) — OS-quality/tooling |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Session goal** | Get an independent, adversarial audit of the prompt/handoff templates against "fat causes drift and hallucination," returning findings + a measurably tighter rewrite. |

### Objective & Value
- **Objective:** an independent auditor (fresh chat / Gemini — not the author) attacks
  `SESSION_PROMPT_TEMPLATE`, `SESSION_BRIEF_TEMPLATE`, `VALIDATOR_BRIEF_TEMPLATE` + the
  Story-1.1 filled instances, and returns a sealed findings report + a proposed
  tighter rewrite (quantified reduction, zero load-bearing loss).
- **Why:** RD-008/§4a now *mandate* an independent leanness pass before these templates
  are relied on — and Story 1.1's live validation uses the validator-handover template.
  Auditing the tool before use.

### Scope, Dependencies & Position
- **In scope:** running the audit (the prompt is authored at
  [`story-G-1-fat-audit-prompt.md`](story-G-1-fat-audit-prompt.md)); capturing the verdict.
- **Out of scope:** applying the trims — that is **G-2**. No Story 1.1 live work.
- **Depends on:** nothing (ready now). **Unblocks:** G-2, then Story 1.1's live validation.

### Definition of Done / Validation Gate
- **Done means:** the independent auditor delivers a sealed findings report + a proposed
  measurably-tighter rewrite. The party that built the templates does NOT self-certify.
- **Validated by:** the stakeholder, by running the audit prompt against a fresh validator.
- **Validation Result:** `pending`.
- **On pass:** record the dated result + verdict; set G-1 ✅; hand findings to G-2.
- **On fail / inconclusive:** re-run or refine the audit inputs; stay on G-1.

### Risks & Watch-Items
- Keep the audit itself lean — don't hand the auditor a fat curated packet; give it the
  requirement + pointers to the raw templates (§4a).
- If the auditor is a fresh session of the same model, it shares blind spots — prefer a
  different model (Gemini) for true independence; a fresh-self pass is a weaker first cut.

### Lessons Learned / Carry-Forward
- Authored alongside the anti-fat baseline (RD-008) + AI RMF Profile (MEASURE-2.7). This
  audit is the first exercise of that mandated gate.
