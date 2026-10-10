# Troikauge 3.0 — Cross-Project Integration Project Plan

> **PROPOSED, 2026-10-10.** This plan governs introduction of Copilot Moderator, Seat 4 Bookkeeper, and GitHub board synchronization for the unfinished **PDE** and **ZTIE** projects. Both product development streams remain Human-paused. Approval of this document is separate from authorization to resume features, deploy infrastructure, create a Seat 4 AWS account, or merge other PRs.
>
> **Separation of facts:** The product plans and runbooks remain the authority for each product's story state and validation debt. [PDE plan](PROJECT_PLAN.md) / [runbook](RUNBOOK.md); [ZTIE plan](https://github.com/warrenrutledge64/ZTIE-Issues/blob/main/PROJECT_PLAN.md) / [runbook](https://github.com/warrenrutledge64/ZTIE-Issues/blob/main/RUNBOOK.md). This document owns the *cross-project onboarding scope and dependencies* only; companion [master runbook](TROIKAUGE_3_DEPENDENCY_RUNBOOK.md) owns onboarding story execution state.

## 1. Outcome and constraints

**Goal:** Improve design/build performance on PDE and ZTIE by bringing Copilot's independent mechanical moderation and ChatGPT-assisted Seat 4 bookkeeping online, with automation that eliminates routine manual GitHub Project administration. Preserve Gemini's separated Planner and Validator roles, Kiro's Builder remit, independent verdicts and Human ratification.

**Outcomes:**
1. One authoritative, dependency-ordered, cross-project onboarding queue with inspectable provenance.
2. Copilot produces independent per-run Moderator gate artifacts (never supplied by Kiro).
3. Seat 4 handles routine status/evidence/decision bookkeeping previously carried by Kiro, without grading or self-approving work.
4. GitHub Project Board can be reconciled and synchronized automatically from authorized issue/runbook sources; the Human can manually reorder tasks without an automation overwriting their intent.
5. PDE and ZTIE resume independently, only on explicit Human approval and satisfaction of their existing validation gates.

**Hard constraints:** No automatic story ✅, validator verdict, GitHub PR merge, production deployment, approval token, or Human ratification. Read-only/dry run first; live Project V2 writes require separate authorization and credential/permission verification. No production-seat access to private Seat 4 assessments or credentials. Seat 4 dedicated AWS account **design** approved in Issue #81; **account creation and gate activation blocked**. PR #87 stays draft/unmerged.

## 2. Role allocation

| Role | Accountable output | Cannot substitute for |
|---|---|---|
| Gemini Planner (isolated from Validator context) | Requirement / what and why / acceptance envelope | Builder implementation |
| Kiro Builder | Engineering design, code, tests, uncurated technical evidence | Independent Validator or Copilot run attestations or Seat 4 ledger |
| Copilot Moderator | Self-authored four-gate run checks: Pre-Execution, Deployment, Preflight, Live Result | Independent test PASS, Human seal |
| Gemini Validator (separate context) | Independent verdict based on pinned target and uncurated evidence | Human approval |
| Human + ChatGPT Seat 4 | Decision/evidence/status bookkeeping and cross-project index; independent Human deliberation | Production-seat execution, self-certification; Human controls all authority |

## 3. Dependency-ordered stories

The IDs **TG-01 ... TG-11** are proposed *master onboarding stories*, not new PDE or ZTIE feature IDs. All are **Not Started / Proposed**, independent of pre-existing product story completion. Each story must exit via its own recorded evidence and Human review.

| Tier | Story | Name | Depends on | Owner | Acceptance/exit | Estimate |
|---|---|---|---|---|---|---|
| 0 | **TG-01** | Baseline / authoritative ledger inventory | — | Seat 4 | Links + snapshots of product story states and validation debt; discrepancy log | 0.5–1 h |
| 1 | **TG-02** | Bookkeeper ownership and access matrix | TG-01 | Seat 4 + Human | Transfer of *future* recordkeeping documented; privacy + role boundaries | 0.5–1.5 h |
| 1 | **TG-03** | Define board-sync source/field contract | TG-01 | Seat 4 / Kiro advice | Mapped issue identity, priority, Workstream, Status policy, manual-order policy, dry-run output | 1–1.5 h¹ |
| 2 | **TG-04** | Board-sync inventory & deterministic dry-run prototype | TG-03 | Kiro Builder, Seat 4 bookkeeping | Read source records; report create/update/no-op and conflicts; zero write calls | 2–3.5 h¹ |
| 3 | **TG-05** | Projects V2 permissioned writer | TG-04, TG-02 | Kiro Builder | Idempotent, least-privilege writer with field mapping, retries, no unsafe status mutations; feature disabled by default | 1–2 h¹ |
| 4 | **TG-06** | Board sync independent validation and controlled activation | TG-05 | Copilot Moderator + Gemini Validator + Human | Dry-run comparison, authorized small write, audit/re-run no-op, rollback plan; explicit Human activation | 1–2 h¹ |
| 2 | **TG-07** | Copilot Moderator onboarding | TG-02 | Copilot | Direct pinned-source access and self-authored four gate demo incl. refusal/negative tests | TBD |
| 3 | **TG-08** | Full four-seat handoff rehearsal | TG-07, TG-02 | All seats, Human seal | Planner → Kiro → Copilot → blind Validator → Human → Seat 4 record, harmless offline target | TBD |
| 2 | **TG-09** | Seat 4 dedicated-account authorization-gate design | TG-02 | Seat 4 / Kiro consult | Reviewed architecture, org authority, MFA/replay/audit negative plan, no resources | TBD |
| 4 | **TG-10** | PDE/ZTIE debt and next-story readiness review | TG-08, TG-01 | Seat 4 / Kiro consult / Validator | Independent, linked prioritization of open blockers (e.g. ZTIE 2.6R), preserve individual product gates | TBD |
| 5 | **TG-11** | Human-controlled project resumption decision | TG-10 | Human | Separate PDE and ZTIE decisions; original dependencies and validation debt honored | Human decision |

¹ **Board synchronizer estimate:** TG-03–TG-06 total approximately **6–10 hours of engineering effort**, including a first dry run at roughly **3–5 cumulative hours** (scope and API access dependent). TG-01/TG-02 are bookkeeping/onboarding preparations **outside** that estimate. These are engineering estimates, not wall-clock completion promises; API permissions may add effort.

**Dependency graph:**
```text
TG-01 baseline ───┬── TG-02 ownership ──┬── TG-07 Copilot ── TG-08 rehearsal ── TG-10 readiness ── TG-11 Human resume
                  │                     ├── TG-09 Seat 4 security DESIGN (parallel, not production activation)
                  │                     └────────────────┐
                  └── TG-03 mapping ── TG-04 dry run ── TG-05 writer ── TG-06 authorized sync
```
TG-05 also depends on TG-02; TG-10 also depends on TG-01. TG-06 is **not a gate on resuming product feature work** unless the Human decides it is.

## 4. Board-sync design decisions to ratify before writing

- **Source of truth:** product RUNBOOK statuses + corroborating evidence; TG onboarding status from the master execution runbook. Board fields are *derived display*, never a replacement.
- **Priority vs manual drag:** GitHub Project Board may be manually ordered. Auto-updating a Priority field should **not** continually rewrite the user's card order. Offer an explicit `apply-priority-order` action only if requested; otherwise preserve manual item ordering.
- **Project API:** GitHub Projects V2 GraphQL scoped access (read first); discover project and field IDs; select narrowest feasible permissions; no token in Actions or repository code. Connection capabilities currently lack Projects field writes.
- **Safe updates:** Match by stable issue URL/node identity; dry-run every mutation; update only permitted fields (Workstream, Priority, optionally board intake), not product acceptance Status, with idempotency and audit logs; unauthorized or ambiguous records are skipped and reported.

## 5. Delivery and approval gates

**Gate A** — Baseline accepted: TG-01/02 decisions and source inventory documented.

**Gate B** — Dry-run accepted: TG-03/04 correctly identify existing issues, board settings, duplicates, missing metadata, and no unexpected writes; independent review.

**Gate C** — Controlled activation (optional): TG-05/06 requires Human permission for specific project, fields, credential scope and first actual write; rollback demonstrated. No background schedule unless separately requested.

**Gate D** — Copilot/seat work validated: TG-07/08 independently evidenced; no Builder-provided Moderator run packet.

**Gate E** — Product resume: TG-10 readiness plus separate Human decisions; original PDE/ZTIE advancement gates binding.

## 6. Reference links

- [Master tracking Issue #97](https://github.com/warrenrutledge64/pde-platform/issues/97)
- [Troikauge board](https://github.com/users/warrenrutledge64/projects/1)
- [PDE onboarding draft PR #95](https://github.com/warrenrutledge64/pde-platform/pull/95)
- [ZTIE onboarding draft PR #226](https://github.com/warrenrutledge64/ZTIE-Issues/pull/226)
- [Earlier master-runbook draft PR #96](https://github.com/warrenrutledge64/pde-platform/pull/96)
- [Seat 4 authorization account Issue #81](https://github.com/warrenrutledge64/pde-platform/issues/81)

**Change control:** Proposed document only. Reconcile with #95/#226/#96 before any merge; no claim that this supersedes an existing ratified source.