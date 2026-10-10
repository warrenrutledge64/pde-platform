# Troikauge 3.0 — Dependency-Ordered Master Execution Runbook

> **Status: PROPOSED; all TG stories remain ⬜ NOT STARTED until validated evidence says otherwise.** PDE and ZTIE are Human-paused. Companion: [master project plan](TROIKAUGE_3_PROJECT_PLAN.md). This runbook is authoritative only for **TG onboarding stories**, NOT for PDE or ZTIE original stories, which keep their canonical ledgers.
>
> **Execution ordering:** An open story is ready only after every TG dependency is independently recorded complete. In parallel, the product-specific hard validation-debt and phase gates remain binding. A written design, code merge, Copilot gate-green, or dry run is never equivalent to a live product acceptance pass.

## 1. Master story ledger

| Tier | ID | Workstream | Story | Depends on | Priority | State | Evidence / Human gate |
|---|---|---|---|---|---|---|---|
| 0 | TG-01 | Seat 4 | Product ledger baseline / dependency inventory | — | **P0** | ⬜ Proposed | Pending |
| 1 | TG-02 | Seat 4 | Transfer bookkeeping ownership from Kiro | TG-01 | **P0** | ⬜ Proposed | Pending |
| 1 | TG-03 | Board Automation | Board field + source contract | TG-01 | **P0** | ⬜ Proposed | Pending |
| 2 | TG-04 | Board Automation | Read-only sync/dry-run implementation | TG-03 | **P0** | ⬜ Proposed | Pending |
| 2 | TG-07 | Copilot | Independent Moderator onboarding and gate rehearsal | TG-02 | **P1** | ⬜ Proposed | Pending |
| 2 | TG-09 | Seat 4 | Independent AWS account design only | TG-02 | **P2** | ⬜ Proposed | Pending |
| 3 | TG-05 | Board Automation | Project V2 permissioned writer, off by default | TG-04, TG-02 | **P1** | ⬜ Proposed | Pending |
| 3 | TG-08 | Master | Complete seat handoff rehearsal | TG-07, TG-02 | **P1** | ⬜ Proposed | Pending |
| 4 | TG-06 | Board Automation | Controlled, independently validated board write | TG-05 | **P1** | ⬜ Proposed | Pending |
| 4 | TG-10 | PDE + ZTIE | Existing technical debt/readiness review | TG-08, TG-01 | **P1** | ⬜ Proposed | Pending |
| 5 | TG-11 | Human | Project-specific resumption decision | TG-10 | **P1** | ⬜ Proposed | Pending |

**Next eligible work:** TG-01. After TG-01 acceptance, TG-02 and TG-03 can proceed independently. Once TG-03 is accepted, TG-04 dry run is eligible. **No story here is marked DONE.**

## 2. Story cards: deliverable, acceptance and failure handling

### TG-01 — Baseline inventory (Seat 4)
**Precondition:** access to permitted PDE/ZTIE plans and runbooks. **Produce:** dated, link-only snapshot of each project's story/status, open validation debt, phase-gate state, relevant PRs and restore/BOM references, with missing/contradictory evidence flagged. **Exit:** Human confirms that nothing was silently reclassified. **Failure:** preserve conflicting entries as unresolved; do not invent state.

### TG-02 — Bookkeeping transfer
**Precondition:** TG-01 accepted. **Produce:** role/authority matrix and procedure assigning future routine status/evidence/decision/handoff record updates to Seat 4; Kiro keeps code/tests/implementation evidence and cannot write Copilot or Validator run verdicts. **Exit:** Human approves the ownership transfer in the record and verifies private Seat 4 access stays restricted. **Failure:** hold status updates until provenance is established.

### TG-03 — Source/field mapping
**Precondition:** TG-01 accepted. **Produce:** inventory of GitHub Project item IDs, permitted API field IDs, Workstream/Priority/Status mapping, source precedence, "manual order" preservation policy, and no-duplicate key rule. **Exit:** Human and independent reviewer approve exact allowed write scope; dry-run remains read-only. **Estimate:** ~1–1.5 h (part of synchronizer estimate). **Failure:** ambiguous fields/permissions halt writer design.

### TG-04 — Deterministic dry-run synchronizer
**Precondition:** TG-03. **Produce:** version-controlled stdlib-first tool/utility that reads approved story/issue sources and returns deterministic proposed inserts, no-ops and updates; supports missing/duplicated/inconsistent items; no write-capable API calls in dry-run. **Exit:** reproducible offline fixtures, one sample mapped to actual issues, diff reviewed by Seat 4 and independent reviewer. **Estimate:** ~2–3.5 h; dry run ~3–5 h cumulative with TG-03. **Failure:** any proposed approval/status override, duplicate or accidental write = FAIL.

### TG-05 — Projects V2 API writer
**Preconditions:** TG-04 and TG-02. **Produce:** narrowly scoped, disabled-by-default GraphQL writer; token never checked in or exposed to production-seat repositories/Actions; idempotency, bounded retries, permission-denied handling, audit trace, explicit allow-list of Project/fields. **Exit:** offline simulated mutation tests and live permission check read-only, no live board mutation. **Estimate:** ~1–2 h. **Failure:** lack of safe credential control or missing fields blocks activation.

### TG-06 — Controlled activation/validation
**Precondition:** TG-05. **Produce:** Human-reviewed exact write plan, small reversible sample board update and repeat sync proof (second run no-op), documented rollback; verify manual drag order isn't auto-reset. **Exit:** independent verifier confirms board state and Human signs activation. **Estimate:** ~1–2 h. **Failure:** stop and reconcile; no silent retries of destructive writes. **No recurring schedule by default.**

### TG-07 — Copilot Moderator online
**Precondition:** TG-02. **Produce:** Copilot's own four-gate offline attestation for a pinned harmless test, including target lock, non-deployed-code/absent-secret refusal simulation, and negative test of Builder-generated gate packet. **Exit:** moderator authenticity verified and Human accepts onboarding. **Failure:** remain blocked; green Moderator never means Validator PASS.

### TG-08 — Whole-system handoff rehearsal
**Preconditions:** TG-07, TG-02. **Produce:** immutable links to independent Planner requirement, Kiro build evidence, Copilot gate run, blind Gemini Validator verdict, Human seal, and Seat 4 ledger update. **Exit:** no role-leak/confidentiality violation and each participant authored only its own lane. **Failure:** stop; no product features marked complete.

### TG-09 — Seat 4 AWS authorization-gate design
**Precondition:** TG-02. **Produce:** reviewed separate-account design aligned with Issue #81, org admin custody/SCP enforceability, MFA-backed callback, atomic replay, audit, negative tests, token-domain compatibility. **Exit:** Human decision on design-only matters. **Failure:** no account creation, role/credential provisioning, merge or activation without separate approval.

### TG-10 — PDE/ZTIE readiness and debt
**Preconditions:** TG-08, TG-01. **Produce:** dated blocker report from the actual canonical product ledgers and validation debt, including ZTIE's in-progress 2.6R and other security/control-plane work and PDE's documented phase gates. **Exit:** Human accepts priority recommendation; technical remediation begins only on separately authorized resumption under existing dependencies. **Failure:** outstanding debt remains, never waived or silently green.

### TG-11 — Human project resumption
**Precondition:** TG-10. **Produce:** explicit, independent decisions for PDE and ZTIE, with restrictions, next authorized story and evidence required. **Exit:** signed Human authorization and unchanged product advancement semantics. **Failure:** both remain paused.

## 3. Engineering effort and validation debt

The first board-sync dry run (TG-03 + TG-04) is estimated **3–5 cumulative engineering hours**. Through controlled initial sync (TG-03 through TG-06), **6–10 cumulative hours**. TG-01/TG-02, Copilot and Seat 4 AWS design work are separate, not concealed inside that estimate. All durations are provisional until the repo/API access and schema are pinned.

**TG validation debt:** None can be cleared through self-certification; every TG row remains ⬜ until its own acceptance is recorded. If a TG implementation is built but validation fails/incomplete, record 🟡/⛔ with a specific clearing action. Never replace the product runbooks' debt registers.

## 4. Bookkeeping updates and board behavior

- Seat 4 is responsible for updating this TG ledger on independently evidenced milestone completion, preserving the full dated result and Human decision. Kiro supplies technical evidence; Copilot its per-run record; Gemini Validator its verdict.
- Board automation maps TG stories to separate project items after Human approval; [Issue #97](https://github.com/warrenrutledge64/pde-platform/issues/97) is the parent tracker. The GitHub Projects V2 connector currently does **not** permit direct field mutations; a separately authorized API writer is required.
- Never create a second maintained PDE/ZTIE story-status ledger here. Deep links to each canonical story and issue are preferred.
- Preserve manual reorder in Board view: do **not** force re-sorting on each sync. Workstream/priority tags are distinct from actual execution-authority or acceptance state.
- [PDE Issue #81](https://github.com/warrenrutledge64/pde-platform/issues/81) is architecture-approved, implementation-blocked. [PDE PR #87](https://github.com/warrenrutledge64/pde-platform/pull/87) remains required to stay draft/unmerged.

## 5. First operational check

**Start with TG-01**, a read-only inventory comparing [PDE's RUNBOOK](RUNBOOK.md) and [ZTIE's RUNBOOK](https://github.com/warrenrutledge64/ZTIE-Issues/blob/main/RUNBOOK.md) to this proposed TG queue. Review contradictions with the Human. Then TG-02 and TG-03 are ready; no AWS account is needed for the board-sync dry run.
