# PDE — NIST AI RMF Profile (proposed / candidate)

> **What this is.** A **target Profile** in the sense of the NIST AI Risk Management
> Framework (AI 100-1): a tailored selection of the framework's functions applied to
> *this* use case — PDE, a validation-gated multi-account AWS delivery platform whose
> "AI" element is an **AI execution agent** driven by prompts/handoffs under the
> project-os operating model.
>
> **Posture (read this first).** Every mapping below is a **candidate — `Proposed`,
> pending ratification** by an accountable reviewer. This document does **NOT** assert
> that PDE "conforms to", "complies with", or "is aligned with" the AI RMF as
> established fact. It records *where our existing controls speak to* the framework so
> gaps are visible and coverage is claimed only when a reviewer ratifies a row. Honest
> **gaps are marked as gaps**, not papered over. (Same discipline PDE applies to all
> control mappings: proposed-at-authoring, ratified-on-review, never overclaim.)
>
> **Scope = everything in purview.** The ratified decisions RD-001…RD-008, the tracked
> debt OD-002/OD-003, the human accept/reject gate, and the orchestrate-and-pull
> control model. Sources of truth remain [`PROJECT_PLAN.md`](PROJECT_PLAN.md) (the RDs)
> and [`RUNBOOK.md`](RUNBOOK.md) (the debt registers + gates); this Profile maps to
> them, it does not restate them.

- **Framework:** NIST AI RMF (AI 100-1), functions GOVERN / MAP / MEASURE / MANAGE.
- **Profile type:** target profile (proposed).
- **Last updated:** 2026-09-30.

---

## What is the "AI system" here?

PDE itself is conventional automation (Step Functions, CodeBuild, CloudFormation) —
not a model. The AI-risk surface in purview is the **AI execution agent** that builds
the platform from written prompts/handoffs, and the **human-in-the-loop gate** that
governs what the automation is allowed to promote. So this Profile is mostly about
**governing the agent's execution and the human decision authority**, not about a
deployed ML model. That framing is itself a MAP activity (context/impact), recorded
below and honestly bounded.

---

## GOVERN — policies, accountability, culture

| AI RMF (candidate) | PDE control in purview | Evidence | Status |
|--------------------|------------------------|----------|--------|
| GOVERN-1.1 (policies/processes to manage AI risk) | The project-os operating model: binding Validation & Advancement Gate; RD-008 lean-prompts discipline; §4a independent validation. | METHODOLOGY §4/§4a/§7; RUNBOOK gate | Proposed |
| GOVERN-1.2 (accountability structures; roles) | Split-brain roles: planner vs. executor; validator authors the check, executor records, human decides. Executor never self-certifies. | METHODOLOGY §2, §4a | Proposed |
| GOVERN-2.1 (roles/responsibilities documented) | Every story has a named validator + recorded result; RD ownership; debt-register owners. | RUNBOOK Validation/Operational Debt Registers | Proposed |
| GOVERN-3.2 (human oversight of AI) | Human accept/reject on the Hub dashboard gates promotion Dev→Sandbox→Prod; the agent's recommendation is advisory, the human decision is enforced. | RD-006 (human gate); RUNBOOK | Proposed |
| GOVERN-4.1 (culture of risk identification; safety-first) | Debt is declared/tracked (neutral, owned, clear-by), never hidden; "fat causes drift/hallucination" treated as a safety property. | RD-007/RD-008; OD-002/OD-003 | Proposed |
| GOVERN-5 (decisions are documented + auditable) | Registered Decisions (RD-001…008) with rationale + date; paired-commit ledger; restore points. | PROJECT_PLAN §5; RESTORE | Proposed |
| GOVERN-6.1 (risks from third-party/reused components) | Reusable-OS-vs-instance discipline: fixes ported to `SDD-repo-kit` (source of truth); ZTIE co-existence constraints. | RD-002; OD-001 (kit fix) | Proposed |

## MAP — context, and the risks/impacts named

| AI RMF (candidate) | PDE control in purview | Evidence | Status |
|--------------------|------------------------|----------|--------|
| MAP-1.1 (establish context / intended purpose) | Project identity, non-negotiable constraints, phases; the AI element is the execution agent (see "What is the AI system"). | PROJECT_PLAN §1–3 | Proposed |
| MAP-2.2 (how the system is used; human-AI configuration) | Orchestrate-and-pull: Hub directs, member executes locally, results pulled, human accepts/rejects; Hub is not a general write-target. | RD-006 | Proposed |
| MAP-3 (benefits/costs) | Deferral decisions weigh cost/benefit explicitly (defer additive audit; settle load-bearing charter now). | RD-007 rationale | Proposed |
| MAP-5.1 (impacts / failure modes characterized) | Named AI failure modes: prompt **fat → executor drift + hallucination** (RD-008); false "done" on inference (gate); Hub-in-blast-zone (RD-006). | RD-008; METHODOLOGY §4/§7 | Proposed |

## MEASURE — evaluate, test, track

| AI RMF (candidate) | PDE control in purview | Evidence | Status |
|--------------------|------------------------|----------|--------|
| MEASURE-1.1 (appropriate methods/metrics identified) | Offline invariant validators (stdlib) as a measurable bar; the mandated **fat-audit returns a quantified tighter rewrite** (RD-008/§4a). | `infra/validate_*.py`; RD-008 | Proposed |
| MEASURE-2.7 (robustness / drift / confabulation evaluated) | The independent adversarial audit of prompts/templates targets drift + hallucination directly (fat axiom); live validation is human-run on raw output. | RD-008; §4a; VALIDATOR handover | Proposed |
| MEASURE-3 (mechanisms to track risk over time) | Validation Debt Register (open validation debt) + Operational Debt Register (tracked debt with clear-by edges). | RUNBOOK registers | Proposed |
| MEASURE-4 (feedback / independent review) | §4a independent validator authors the DoD; leanness audited independently (author cannot self-certify). | METHODOLOGY §4a | Proposed |
| **GAP** — quantitative model/output metrics | **Not yet addressed.** PDE has no deployed ML model under test; agent-output metrics (beyond leanness + live gates) are not instrumented. Revisit if/when an ML component enters scope. | — | Gap (tracked) |

## MANAGE — respond, monitor, recover

| AI RMF (candidate) | PDE control in purview | Evidence | Status |
|--------------------|------------------------|----------|--------|
| MANAGE-1.3 (risks prioritized + responded to) | Advancement gate ARMS on open validation debt; deferrals are deliberate, prioritized, and recorded (RD-007). | RUNBOOK gate; RD-007 | Proposed |
| MANAGE-2.1 (mechanisms to sustain value / go-no-go) | Human accept/reject go/no-go at each promotion; split-brain validation for production. | RD-006; Universal Criterion 2 | Proposed |
| MANAGE-2.4 (deactivate / roll back) | Restore-point discipline (code + state as one unit); backout in every LIVE-RUNBOOK; revert-don't-forward-patch. | RESTORE; LIVE-RUNBOOKs | Proposed |
| MANAGE-3.1 (third-party / reused-component risk managed) | Upstream fixes to `SDD-repo-kit`; ZTIE non-destructive co-existence (naming/tagging). | OD-001; Universal Criterion 5 | Proposed |
| MANAGE-4.1 (ongoing monitoring; incidents feed improvement) | Warm handoffs fold lessons forward; the doc-consistency gate (`check_docs`) runs on every commit. | METHODOLOGY §5; `.githooks` | Proposed |
| **GAP** — runtime AI monitoring | **Not yet addressed.** No continuous runtime monitoring of agent behavior in production (there is no production AI runtime yet). Ties to the deferred agent-activity display (OD-003) and deferred org audit (OD-002). | OD-002; OD-003 | Gap (tracked) |

---

## Honest gaps (do not claim coverage)

- **MEASURE quantitative metrics** and **MANAGE runtime monitoring** are **gaps** — PDE
  has no deployed model/AI runtime yet, so those subcategories are not meaningfully
  addressable now. They are recorded as gaps, tied to OD-002 (deferred audit) and
  OD-003 (deferred agent-activity display); revisit when an AI runtime or the dashboard
  observability lands.
- All rows are **Proposed** until an accountable reviewer ratifies them. Ratification is
  a reviewer's act (as with all PDE control mappings); the executor does not self-ratify.

## Maintenance

- When a new RD or OD is registered, add/adjust its candidate AI RMF row here.
- On ratification, change a row's Status `Proposed → Ratified` (dated, reviewer named).
- Keep this Profile **lean** (RD-008): map to the subcategories a control genuinely
  speaks to; mark honest gaps; do not add decorative rows for coverage's sake.
