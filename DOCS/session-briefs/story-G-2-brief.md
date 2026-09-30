# Session Brief — Story G-2: Trim templates to the audit findings + record the lean pass

> Populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md) (Governance G- series).
> Lean by design (RD-008). Depends on G-1's audit findings.

## Story G-2 — Trim templates to the audit findings + record the lean pass

| Field | Value |
|-------|-------|
| **Type** | Governance (G-series) — OS-quality/tooling |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Session goal** | Apply G-1's accepted findings — trim the templates to load-bearing-only — mirror upstream, and record the lean pass that clears the "prompts are optimized" gate. |

### Objective & Value
- **Objective:** trimmed prompt/handoff templates (instance + upstream `SDD-repo-kit`)
  reflecting the audit's accepted findings, plus a **recorded lean pass**.
- **Why:** this is the gate Story 1.1's live validation waits on (RD-008/§4a; AI RMF
  MEASURE-2.7). Once recorded, the templates are trusted for real work.

### Scope, Dependencies & Position
- **In scope:** apply accepted trims (cut to load-bearing-only, move reference to linked
  docs, guardrails early, de-dupe across brief/prompt/handover); mirror upstream; re-prove.
- **Out of scope:** anything the auditor did NOT flag (don't over-trim into losing a
  guardrail); Story 1.1 live work.
- **Depends on:** G-1 ✅ (findings exist). **Unblocks:** Story 1.1's live validation.

### Definition of Done / Validation Gate
- **Done means:** trimmed templates on `main` (instance + upstream) AND a recorded lean
  pass — the accepted findings are applied, `check_docs` + tests green, and the
  reduction is recorded (quantified, zero load-bearing loss). Satisfies RD-008/§4a.
- **Validated by:** the stakeholder confirms the trims match the accepted findings
  (ideally a quick re-audit or the auditor's sign-off on the rewrite).
- **Validation Result:** `pending`.
- **On pass:** record it; set G-2 ✅. This clears the leanness gate → Story 1.1's live
  validation may proceed.
- **On fail:** stay on G-2; adjust the trims.

### Risks & Watch-Items
- **Don't over-trim.** A guardrail the auditor said to keep-but-shorten must stay —
  shorter and earlier, not gone.
- **Mirror upstream** (`SDD-repo-kit`) or the reusable layer drifts from the instance.
- Update AI RMF Profile MEASURE-2.7 evidence with the recorded pass if warranted.

### Lessons Learned / Carry-Forward *(fill from G-1)*
- Fold in what G-1's audit actually found (the specific fat, the reduction achieved,
  any guardrail that was buried), so this trim is grounded in the real findings.
