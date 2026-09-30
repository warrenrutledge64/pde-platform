# Platform Delivery Engine (PDE) — Project Plan

> The **what and why**. This plan defines scope, phases, decisions, and acceptance
> criteria. The [`RUNBOOK.md`](RUNBOOK.md) tracks execution against it; the two
> must stay in sync. No phase is "done" until its live validation passes (see the
> runbook's Validation & Advancement Gate).

## 1. Project Identity

**Project Name:** Platform Delivery Engine (PDE)

**Purpose:** PDE is a disciplined, validation-gated multi-account AWS delivery
platform. It solves the critical risk of "root sprawl" by providing a
deterministic, automated path for workloads to progress from development to
production without ever touching the Organization management account.

**End State:** A foundational, self-sustaining CI/CD factory resides in the
existing `Pipeline-Hub` account alongside the active ZTIE control plane. A test
artifact can be successfully committed to the repository, deployed automatically to
`Pipeline-Dev`, manually approved/promoted to `Pipeline-Sandbox` for validation,
and ultimately released to `Pipeline-Prod`, proving the end-to-end delivery path is
fully operational.

## 2. Non-Negotiable Constraints

> The rules that hold across every phase. Any deliverable violating one is not
> done, regardless of other progress.

1. **Production-Quality:** No mock data, placeholder services, or skipped
   configurations.
2. **Validation-Gated:** Work is never inferred as "done." Every phase concludes
   with a concrete, live validation gate recorded by a human.
3. **Restore-Point Discipline:** Clean rollback states must be maintained at phase
   boundaries.
4. **Least Privilege & Zero-Trust:** IAM roles must strictly scope permissions to
   exact requirements. Split-brain validation is enforced for production
   deployments.
5. **Root Governance Only:** The Organization management account (467866449172) is
   strictly excluded from application and delivery workloads. (Note: Org-wide
   CloudTrail configuration is classed as governance.)
6. **AWS-Native & Serverless-First:** The orchestration engine will utilize AWS
   Step Functions, CodeBuild, and EventBridge (Zero-EC2). GitHub is used
   exclusively for source control, not operational deployment.
7. **Single IaC Standard:** Infrastructure is defined exclusively in standard AWS
   CloudFormation (YAML) and Python 3 (Boto3). Third-party IaC tools (e.g.,
   Terraform) are strictly prohibited.
8. **Self-Deploying Engine:** The PDE must be capable of deploying and updating its
   own architecture after the initial bootstrap.
9. **ZTIE Co-existence:** The `Pipeline-Hub` account hosts the active ZTIE control
   plane. All PDE deployments into the Hub must be strictly additive,
   namespace-isolated, and non-destructive to existing ZTIE infrastructure.

## 3. Phases & Milestones

> Ordered by dependency + reuse value. Pull genuine shared foundations forward and
> build them once. Each phase has a single, live end-of-phase validation gate.

### Phase 1 — Trust Fabric
- **Goal:** Establish the tier-1 cross-account **trust identity + direction** for the
  RD-006 **orchestrate-and-pull** model: each member (Dev/Sandbox/Prod) has a
  local **execution role the Hub can invoke/direct**, whose trust names a *specific
  Hub orchestrator role* (never the Hub account root). Execution happens locally in
  the member; the Hub directs and (later) pulls results. *(Per RD-007, the org-wide
  audit baseline that originally opened this phase is deferred to Phase 4 — see
  RD-005/RD-006/RD-007. Tight scope: the orchestration engine, the results
  data-contract, and the signed-decision machinery are Phase 2.)*
- **Gate:** From an AWS CloudShell session in the Hub account, a human operator
  performs an STS `AssumeRole` into the member execution role in Dev, Sandbox, and
  Prod sequentially, returning their Account IDs — proving the Hub can direct a
  member function and the trust direction is correct-by-construction. *(The original
  CloudTrail half of this gate moves to the Phase 4 governance gate per RD-007.)*
- **Stories:**
  - **Story 1.1:** Deploy a least-privilege **member execution role** in Dev,
    Sandbox, and Prod, invokable by a *specific* `Pipeline-Hub` (`641628980935`)
    orchestrator role (RD-006 orchestrate-and-pull; the member executes locally, the
    Hub does not push writes in). *(Re-scoped twice: from the deferred org-wide
    CloudTrail (→ `infra/deferred/`, Story 4.1), then from the initial Hub-pushes
    trust shape to this orchestrate-and-pull direction per the RD-006 amendment.)*
  - **Story 1.2:** Configure local AWS CloudShell environment with repository
    access for the initial bootstrap deployment.

### Phase 2 — PDE Control Plane (The Hub)
- **Goal:** Deploy a greenfield serverless delivery engine (Step Functions +
  CodeBuild) into the Hub account, operating safely alongside the existing ZTIE
  architecture, capable of executing cross-account CloudFormation deployments.
- **Gate:** A human operator triggers the deployed Step Function in the Hub account
  with a dummy payload, and the execution successfully reaches the "Awaiting
  Sandbox Approval" paused state without IAM or configuration errors.
- **Stories:**
  - **Story 2.1:** Author standard CloudFormation templates for the PDE CodeBuild
    projects (Linting, Deployment), enforcing standard naming prefixes to avoid
    collisions with ZTIE.
  - **Story 2.2:** Author the Step Functions state machine YAML to orchestrate the
    Dev → Sandbox → Prod promotion workflow, including manual approval gates.
  - **Story 2.3:** Bootstrap the net-new PDE infrastructure into the existing Hub
    account via CLI, ensuring IAM roles deployed are tightly scoped to PDE tasks.

### Phase 3 — The Golden Path Validation
- **Goal:** Prove the end-to-end delivery path by sending a concrete infrastructure
  artifact through the newly built PDE pipeline.
- **Gate:** The human operator queries the live AWS environment in `Pipeline-Prod`
  and successfully returns the metadata of the deployed test artifact, proving the
  Hub successfully orchestrated a cross-account production release.
- **Stories:**
  - **Story 3.1:** Author a trivial, zero-cost artifact (e.g., an empty DynamoDB
    table or SQS queue) in CloudFormation.
  - **Story 3.2:** Commit the artifact and trigger the PDE pipeline to deploy to
    `Pipeline-Dev`.
  - **Story 3.3:** Validate the Dev deployment, approve the Step Function gate, and
    promote to `Pipeline-Sandbox`.
  - **Story 3.4:** Perform split-brain validation on the Sandbox artifact, approve
    the final Step Function gate, and release to `Pipeline-Prod`.

### Phase 4 — Governance Cutover (deferred org-wide audit)
- **Goal:** Switch on the org-wide audit governance that RD-007 deferred, once the
  delivery engine is proven. Stand up the Organization-wide CloudTrail as a shared
  control-plane service administered by the Hub (RD-006), retiring the accepted
  audit debt. This is executed "when it really matters," after Phase 3.
- **Gate:** From the Hub (as the delegated CloudTrail administrator), a human
  operator confirms the org-wide trail is active (org / multi-region / log-file
  validation) **and** log files are landing for all `Pipeline-*` accounts — the
  original CloudTrail half of the old Phase 1 gate, now here.
- **Stories:**
  - **Story 4.1:** Enable CloudTrail delegated administration to the Hub
    (`register-delegated-administrator` from the Organization root — root's sole,
    one-time governance action), then deploy the org-wide CloudTrail + centralized
    S3 log bucket + KMS CMK **in the Hub** under a dedicated governance role
    (RD-006), retiring the RD-007 audit debt. *(The as-built org-trail
    CloudFormation from the original Story 1.1 is preserved at
    `infra/deferred/cloudtrail-org-baseline.yaml` as the starting point; it is
    adapted from root-hosted to Hub-delegated at this story.)*

## 4. Dependency Map

**Hard dependencies (X cannot start until Y exists):**
- **Phase 2 (Control Plane) ← Phase 1 (Trust Fabric).** The Hub cannot orchestrate
  deployments until the Spoke accounts explicitly trust specific Hub roles (RD-006).
- **Phase 3 (Golden Path) ← Phase 2 (Control Plane).** The pipeline must be fully
  deployed and paused-state verified before a real artifact can traverse it.
- **Story 1.2 (CloudShell bootstrap access) ← Story 1.1 (trust roles exist to
  assume).**
- **Story 2.3 (bootstrap PDE infra) ← Stories 2.1 + 2.2 (the CodeBuild + Step
  Functions templates it deploys).**
- **Story 3.2 ← Story 3.1** (artifact must exist before it is committed/deployed);
  **3.3 ← 3.2**, **3.4 ← 3.3** (promotion is strictly sequential Dev → Sandbox →
  Prod).
- **Phase 4 (Governance Cutover) ← Phase 3.** Per RD-007 the org-wide audit is
  switched on *after* the delivery engine is proven; Story 4.1 depends on the Hub
  being an established control plane (Phase 2) and is scheduled after Phase 3.

**Shared foundations pulled forward (multi-phase reuse):**
- **The cross-account trust roles (Story 1.1)** are the reusable substrate the Hub
  control plane assumes for *all* Dev/Sandbox/Prod deployments in Phases 2–3 —
  built once, first (tier 1).
- **The Hub as shared control plane (RD-006)** is the reusable platform capability
  every current and future product consumes; org-wide audit (Story 4.1) is added to
  it as a shared governance service.

**Deferred (accepted, tracked debt — RD-007):**
- **Org-wide audit (originally Story 1.1) → Phase 4 / Story 4.1.** Deferred in full,
  no interim baseline; the delivery engine is proven first, then audit is switched
  on. Tracked in the RUNBOOK Operational Debt Register.

**Self-Hosting Re-entry:** Once Phase 3 is complete, future updates to Phase 2
(Control Plane) components become dependent on the PDE itself, fulfilling the
"self-deploying engine" constraint.

## 5. Registered Decisions

> Durable decisions with an ID so they can be referenced and ratified, not
> re-litigated each session.

| ID | Decision | Rationale | Date | Status |
|----|----------|-----------|------|--------|
| **RD-001** | **Scope Isolation.** PDE is strictly the delivery platform. Relocating misplaced root workloads and decommissioning the Trash OU are separate, subsequent projects. | Keeps PDE's mandate crisp; avoids scope creep into remediation projects. | 2026-09-29 | Ratified |
| **RD-002** | **Account Topology.** Reuse the existing `Pipeline-Hub`, `Pipeline-Dev`, `Pipeline-Sandbox`, and `Pipeline-Prod` accounts. | Stable account IDs exist and map perfectly to the pipeline. `Pipeline-Hub` will natively host PDE alongside ZTIE. | 2026-09-29 | Ratified |
| **RD-003** | **Orchestration Tooling.** Deploy a fresh instance of AWS Step Functions and CodeBuild within the Hub account. | Meets AWS-native and Zero-EC2 constraints while providing native manual approval states for environment promotion. | 2026-09-29 | Ratified |
| **RD-004** | **IaC Standardization.** Enforce standard CloudFormation (YAML) and Python 3 (Boto3). | Satisfies the requirement for a single, strict IaC tool to prevent fragmentation. | 2026-09-29 | Ratified |
| **RD-005** | **Audit Baseline.** Establish a completely new Org-wide CloudTrail and logging bucket. | Ensures a clean, untainted governance boundary starting from Day 1 of the new platform. | 2026-09-29 | Ratified — **amended by RD-006 & RD-007** (see below). The "Day 1" timing is superseded: org-wide audit is deferred (RD-007) and, when built, is administered by the Hub as a shared service (RD-006). Retained for historical reference. |
| **RD-006** | **The Hub is the program-wide shared control plane.** `Pipeline-Hub` (`641628980935`) is a shared control-plane *service* consumed by all current and future products (ZTIE, PDE, and later products/services) — not owned by any one of them. Org-wide governance/audit administration, when enabled, is delegated to the Hub as a shared control-plane service rather than run from the Organization root. Within the Hub, each concern is a **separate, least-privilege role**, with no path from one to another's configuration. Cross-account trust names **specific Hub roles**, never the Hub account root. **Amendment (2026-09-30) — direction of control (orchestrate-and-pull):** the Hub **orchestrates and pulls**, it does not push writes into members. (1) The Hub **invokes/directs** functions that live **in the member accounts**; the *action executes locally in the member*, not by the Hub reaching in to mutate it. (2) Results flow **member → Hub** via a **contract-gated intake** (fail-closed, derived-data-only — the ZTIE RD-013 pattern); the **Hub is not a general write-target** — no one writes to the Hub except an admin on special occasions. The dashboard lives in the Hub in **near-isolation**. (3) The **human accept/reject** decision made on the Hub dashboard is enforced via a **Hub-signed decision token** that the member **verifies offline** before performing the next step (the ZTIE signed-decision pattern) — so the Hub need not reach into the member and the member need not read back into the Hub. **Scope split:** the tier-1 trust *identity + direction* (member-side execution roles the Hub can invoke; the results-intake trust direction) is settled now; the **orchestration engine (Step Functions), the intake data-contract, and the signed-token machinery are Phase 2.** | The Hub was always intended as the shared control plane, not a single-product box, and the orchestrate-and-pull direction keeps it out of the blast zone (matching the proven ZTIE topology): members hold execution + write-power locally, the Hub observes/directs and holds the human gate. Role-level separation preserves separation-of-duties without a separate account. Pinning the *direction* now (at tier 1) makes the Phase 2 orchestration + trust correct-by-construction and avoids an expensive rework of the trust model. | 2026-09-30 | Ratified (amended 2026-09-30) |
| **RD-007** | **Defer org-wide audit governance (no interim).** The org-wide CloudTrail audit baseline is deferred **in full** to a dedicated, scheduled governance story executed later ("switch it on when it really matters"), while PDE proves the delivery engine first. **No interim/throwaway audit baseline is built** — the absence of a PDE-provided org-wide audit trail during the design/build phases (1–3) is an **accepted, declared, tracked debt** (logged in the RUNBOOK Operational Debt Register), not a hidden gap. The org-wide CloudTrail is additive/non-destructive: enabling it later touches none of the delivery engine's trust roles or pipeline. The load-bearing decision (the Hub charter) is NOT deferred — that is fixed now by RD-006; only the additive audit layer is deferred. | The difficulty encountered on the "org path" was the control-plane charter, not CloudTrail itself; separating them lets the cheap, additive audit layer be deferred safely while the load-bearing charter is settled now. Deferring the audit *decision timing* to the last responsible moment means it is made with real information (after Phases 2–3 reveal how the Hub behaves). Accepted risk during design/build: no PDE org-wide audit trail for that window, and logs not captured in the gap are unrecoverable. | 2026-09-30 | Ratified |
| **RD-008** | **Lean prompts/templates — fat causes drift and hallucination.** In this operating model, **prompt and handoff templates are load-bearing execution infrastructure**, and their **leanness is a correctness and safety requirement, not a style preference.** A prompt that is too long, repetitive, or buries its guardrails causes an executor to **drift** (lose the thread, skim past a must-not-miss instruction) and to **hallucinate** (invent content to fill gaps or reconcile half-absorbed contradictions). Standing rules: (a) prompts/templates carry **load-bearing instruction only** — reference/background material is moved to linked docs the prompt points at, not inlined; (b) the **must-not-miss guardrails** (validate-live/don't-self-certify, don't-push-to-main, honor-scope, warm-handoff) appear **early and unmissable**; (c) content is **not duplicated** across brief/prompt/handover (one canonical copy, linked); (d) every re-scope must **re-trim**, not just append — accreted "one more justified paragraph" is the primary way fat enters; (e) a reusable prompt/handoff template is **independently audited for fat before it is relied on** (extends §4a — the author does not self-certify leanness), with the audit required to return a *measurably* tighter rewrite that loses zero load-bearing instruction. | Real, observed failure mode: an over-fat prompt nearly caused (or caused) executor drift. Because these templates are reused on every story, fat compounds; treating leanness as a safety property — and gating it behind independent review like code — makes drift/hallucination resistance a durable, repeatable property of the OS rather than a per-session hope. Aligns with holding management/execution artifacts to the same bar as code. Candidate NIST AI RMF mappings for this and the other decisions are recorded in [`AI_RMF_PROFILE.md`](AI_RMF_PROFILE.md) (proposed, pending ratification). | 2026-09-30 | Ratified |

## 6. Universal Acceptance Criteria

Every deliverable, in every phase, must satisfy (kept in sync with the runbook):
1. **Zero-Touch Root:** No resources are deployed in the management account
   (467866449172) other than the strictly required Org-wide CloudTrail
   configuration.
2. **Split-Brain Validation:** Production deployments must require a validation
   check executed independently from the build/deploy execution context.
3. **Static Security Passed:** All CloudFormation and Python code must pass static
   analysis (cfn-lint, cfn-guard, Bandit, Checkov) before execution.
4. **Clean State Rollback:** Any failed step during bootstrap or deployment leaves
   behind documentation or an automated method to cleanly revert the state.
5. **Non-Destructive Integration:** Deployments into `Pipeline-Hub` must utilize
   strict resource tagging and naming prefixes to avoid altering existing ZTIE
   operations.
