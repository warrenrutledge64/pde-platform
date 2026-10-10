# Troikauge 3.0 — Master Integration Runbook (PDE · ZTIE · Copilot · Seat 4)

> **Status: PROPOSED / DRAFT.** Human-directed preparation of a consolidated, cross-project operating view. PDE and ZTIE development are PAUSED by the Human Stakeholder. This runbook does **not** authorize feature work, deployments, GitHub permission changes, secret provisioning, merges, or live Seat 4 activation.
>
> **Purpose:** one dependency-ordered coordination view for improving both unfinished products by bringing the Copilot Moderator and Human+ChatGPT Seat 4 Bookkeeper online. **Do not create a second authoritative story-status ledger.** The per-product runbooks retain their own story statuses, validation debt, and recorded verdicts; this master is a referenced index and cross-project handoff register.

## 1. Sources of truth and ownership

| Scope | Authoritative source | Ownership and safeguards |
|---|---|---|
| PDE story status / phase closure / validation debt | [PDE RUNBOOK](https://github.com/warrenrutledge64/pde-platform/blob/main/governance/RUNBOOK.md) and [PLAN](https://github.com/warrenrutledge64/pde-platform/blob/main/governance/PROJECT_PLAN.md) | Existing validation and advancement gates remain binding |
| ZTIE story status / phase closure / validation debt | [ZTIE RUNBOOK](https://github.com/warrenrutledge64/ZTIE-Issues/blob/main/RUNBOOK.md) and [PLAN](https://github.com/warrenrutledge64/ZTIE-Issues/blob/main/PROJECT_PLAN.md) | Master table, CHECK A/C, and Validation Debt Register remain binding |
| Moderator gate specification | [PDE MODERATOR_PROTOCOL](https://github.com/warrenrutledge64/pde-platform/blob/main/governance/MODERATOR_PROTOCOL.md) | Copilot authors **run-specific** gate records, Kiro does not |
| Seat authority model | [PDE AGENTS](https://github.com/warrenrutledge64/pde-platform/blob/main/governance/AGENTS.md) | Gemini Planner and Validator contexts separated; Kiro Builder; Copilot Moderator; Human + ChatGPT Seat 4 |
| Cross-project coordination and decisions | This master document + linked governance issues and project board | **Seat 4 Bookkeeper** reconciles, links, and records; Human ratifies; never substitutes AI claims for independent verdicts |
| Seat 4 private assessments/provenance | Human-restricted private storage, outside production-seat access | Never expose raw private records or credentials through production-seat repositories or connectors |
| Seat 4 AWS gate architecture | [PDE Issue #81](https://github.com/warrenrutledge64/pde-platform/issues/81) | Dedicated-account architecture approved **for design only**; implementation blocked |

**Record ownership transfer:** For *future* work, Kiro relinquishes routine status updates, decision ledger maintenance, handoff bookkeeping, and cross-project synchronization to Seat 4, while retaining technical implementation notes, code, tests, and evidence submission. Seat 4 submits status changes only on independently verified evidence and applicable Human decision, using each repository's existing runbook conventions and checker. Historical artifacts remain untouched. Human-approved changes may be proposed in PRs; a proposal is not an approved new operating-system rule.

## 2. Cross-project priority queue (the next-work answer)

These **M0–M6** are *cross-project onboarding milestones*, **not** new PDE/ZTIE story IDs and not `✅` completion markers. Each remains *proposed / not validated* until its evidence is recorded. The governance onboarding work can proceed while feature work stays paused; no milestone overrides an existing product validation-debt gate.

| Priority | Master milestone | Primary owner | Prerequisites | Exit evidence / gate |
|---|---|---|---|---|
| **M0 · NOW** | Seat 4 takes over bookkeeping: establish links to both authoritative ledgers, enumerate in-flight work/validation debt, preserve baseline and changes | Seat 4 + Human | Current plan/runbook snapshot | Reconciled dated index, ownership matrix; no retroactive status flips |
| **M1** | Bring **Copilot Moderator** online with read-only, minimum-necessary source access and the four mechanical gates (Pre-Execution → Deployment → Preflight → Live Result). Test its refusal of Builder-produced gate-run scaffolds | Copilot, with independent provenance check | M0; existing `MODERATOR_PROTOCOL.md` | Copilot-self-authored offline negative/positive gate records, pinned source; no AWS deployment |
| **M2** | Rehearse strict handoff across **Gemini Planner → Kiro Builder → Copilot Moderator → independent Gemini Validator → Human seal → Seat 4 Bookkeeper** | Each seat only in its own lane | M1 | Reproducible harmless offline rehearsal, successful refusal tests and evidence-index update; green Moderator ≠ independent PASS |
| **M3** | Verify Seat 4's private-record and distinct-identity boundary; finalize dedicated-account gate **design** without provisioning | Human + Seat 4; Kiro consults on neutralized engineering evidence | M0; Issue #81 | Human-reviewed design, denial-test plan, organizational admin/break-glass model; implementation remains separately gated |
| **M4** | Reconcile and triage *existing* product technical / validation blockers, prioritizing security-boundary debt before any new feature | Seat 4 bookkeeping; Kiro remediation; independent Validator | M2 and explicit permission for bounded remediation | No inferred closure; exact product-specific validation results and Human approval |
| **M5** | Human decision to resume **PDE** and/or **ZTIE** work independently | Human | M2 + relevant product gates and blockers assessed | Explicit project-specific authorization recorded; proceed by original runbook dependency order |
| **M6 · LATER** | ZTIE→PDE integration and unified dashboard demonstration | Product Builders / validators | Both products' required phases and their published handoff contract complete | ZTIE G-6 / PDE Phase 5 independent integration validation; Human seal |

**Immediate sequencing recommendation:** M0 → M1 → M2; M3 design work may proceed in parallel under private-boundary restrictions. M4/M5 must not silently bypass product-specific validation debt. M6 is not a prerequisite for onboarding.

## 3. Verified work-in-progress checkpoints (references, not a status mirror)

- **PDE:** The [RUNBOOK](https://github.com/warrenrutledge64/pde-platform/blob/main/governance/RUNBOOK.md) already contains the Troikauge governance core (`G-3`), mechanical authorship barriers (`G-5`), in-progress template modernization (`G-4`), and proposed derived board (`G-7`). The existing phase/dependency path must be consulted live at resumption; do not assign `Done` from a draft PR or repository existence.
- **ZTIE:** The [RUNBOOK master story table](https://github.com/warrenrutledge64/ZTIE-Issues/blob/main/RUNBOOK.md) records an in-progress **2.6R** SFN false-green security correction, **4.10** post-ACCEPT Forensics retention remediation, **G-5** governance-gate work; its **4.4** Human accept/reject interface is not started. Prior `✅` entries reflect recorded project history only, not whole-product completion.
- **Dependency rule:** ZTIE's existing hard pause on open validation debt remains. PDE retains its own phase-validation gates. Seat 4 does not reinterpret either ledger or independently waive them.
- **Architecture separation:** ZTIE artifact ACCEPT/REJECT and PDE promotion approval remain their product domains unless the Human explicitly ratifies a redesign. Seat 4 governs Troikauge administration; dedicated account architecture is design-approved, not provisioned.

## 4. Moderator introduction checklist (Copilot)

1. Human authorizes the smallest source access needed; verify no Seat 4 private repo access and no secret exposure.
2. Copilot reads the canonical `AGENTS.md`, `MODERATOR_PROTOCOL.md`, and pinned source/requirements **directly**; never relies on a Builder-made gate attestation or curated packet.
3. Copilot independently runs/records four gate outcomes on a harmless offline sample, including a deliberately failing precondition and a target-lock check. No pretend AWS deployment or live PASS.
4. Gemini Validator, separately contextualized, receives only authorized uncurated evidence and produces its own verdict. The Human alone seals an approval; Seat 4 files its provenance and the canonical runbook updates.
5. The dry run does **not** turn any previously open PDE or ZTIE story green.

## 5. Seat 4 Bookkeeper checklist

1. Maintain a dated cross-project **link-only** work register: project / canonical story ID / status source / owner / dependency / validation debt / issue or PR / most recent independent verdict / Human decision.
2. Accept implementation evidence from Kiro without letting it define Planner requirements, Validator rubrics, or Copilot's run records.
3. Reconcile each project's plan↔runbook↔BOM/restore references using that project's checker before proposing a status or sequencing edit; leave original status and decision history intact.
4. Keep Human-only assessments and raw reviews outside production seats, public issues, chat handoffs, and production connectors.
5. Link the master board item and Issue #81; maintain an explicit `design approved / implementation blocked` distinction.
6. Never call a story Done without the applicable independent live result, recorded evidence, and Human seal.

## 6. Governance board representation

**Preferred board:** [Troikauge 3.0 — Seat 4 Governance & Integration](https://github.com/users/warrenrutledge64/projects/1). Add a **Master Integration Runbook / Copilot + Seat 4 Onboarding** tracking issue as the parent coordination card, with this file and the two product onboarding proposal PRs linked.

**Suggested project views/fields** (configure only with Human permission): Workstream = Master / PDE / ZTIE / Copilot / Seat4; Priority = M0..M6; Status = Proposed / Ready / In Progress / Blocked / Verified / Human Approved; Blocked By; Evidence link; Human decision. These are **board presentation fields**, not replacements for the authoritative product story state machines. If fields are unavailable, use an ordinary issue checklist and GitHub links; do not invent project status.

## 7. Security, non-goals, and change control

- **No production changes from this document.** PDE and ZTIE remain paused until the Human explicitly resumes them.
- **No private Seat 4 repo access by Kiro/Copilot or shared GitHub connector.** No secret provisioning, cross-account administration, or AWS deployment.
- **No bypass of independent testing.** Offline rehearsals prove the process only; product acceptance needs its own live validation.
- **PR #87** ([offline exchange checker](https://github.com/warrenrutledge64/pde-platform/pull/87)) remains **draft and unmerged** pending its separate test, dependency, and authorization gates.
- Documentation proposed here is a **reviewable draft**, not a change to ratified PDE/ZTIE decisions. Any conflict must be surfaced for Human disposition; Kiro can advise but cannot adjudicate governance authority.

## 8. First action

**Seat 4 (M0)** reconciles both runbooks and open validation debt, creates/links the master governance tracking issue, and requests **Copilot's own** onboarding/preflight rehearsal plan. The next Human review is of this master runbook and its project-board representation — not an infrastructure activation decision.
