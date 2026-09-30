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
- **Goal:** Deploy the foundational cross-account IAM trust relationships from the
  Hub to the Spoke accounts, built to the RD-006 shared-control-plane charter
  (Spokes trust *specific Hub roles*, least-privilege). *(Per RD-007, the org-wide
  audit baseline that originally opened this phase is deferred in full to the
  Phase 4 governance story — see RD-005/RD-006/RD-007.)*
- **Gate:** From an AWS CloudShell session in the Hub account, a human operator
  executes a Boto3 script that successfully performs an STS `AssumeRole` into Dev,
  Sandbox, and Prod sequentially, returning their Account IDs. *(The original
  CloudTrail half of this gate moves to the Phase 4 governance gate per RD-007.)*
- **Stories:**
  - **Story 1.1:** Deploy cross-account IAM execution roles in Dev, Sandbox, and
    Prod whose trust policy names specific `Pipeline-Hub` (`641628980935`) roles for
    deployment operations (least-privilege; RD-006). *(Re-scoped from the deferred
    org-wide CloudTrail — that work is preserved for historical reference in
    `infra/deferred/` and scheduled as Story 4.1.)*
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
| **RD-006** | **The Hub is the program-wide shared control plane.** `Pipeline-Hub` (`641628980935`) is a shared control-plane *service* consumed by all current and future products (ZTIE, PDE, and later products/services) — not owned by any one of them. Org-wide governance/audit administration, when enabled, is delegated to the Hub as a shared control-plane service rather than run from the Organization root. Within the Hub, each concern is a **separate, least-privilege role**: tenant *deploy/execution* roles (e.g. the PDE deployer) are distinct from *governance/audit* administration roles, with no path from a deploy role to the audit configuration. Cross-account trust from the Spokes names **specific Hub roles**, never the Hub account root. | The Hub was always intended as the shared control plane for the program, not a single-product box. Centralizing control-plane responsibilities (including governance administration) in the Hub is repeatable and reusable across products; role-level separation preserves audit/deploy separation-of-duties without a separate account. Deciding this now (at tier 1) makes the Phase 2 IAM/trust fabric correct-by-construction and avoids an expensive later rework of the trust model. | 2026-09-30 | Ratified |
| **RD-007** | **Defer org-wide audit governance (no interim).** The org-wide CloudTrail audit baseline is deferred **in full** to a dedicated, scheduled governance story executed later ("switch it on when it really matters"), while PDE proves the delivery engine first. **No interim/throwaway audit baseline is built** — the absence of a PDE-provided org-wide audit trail during the design/build phases (1–3) is an **accepted, declared, tracked debt** (logged in the RUNBOOK Operational Debt Register), not a hidden gap. The org-wide CloudTrail is additive/non-destructive: enabling it later touches none of the delivery engine's trust roles or pipeline. The load-bearing decision (the Hub charter) is NOT deferred — that is fixed now by RD-006; only the additive audit layer is deferred. | The difficulty encountered on the "org path" was the control-plane charter, not CloudTrail itself; separating them lets the cheap, additive audit layer be deferred safely while the load-bearing charter is settled now. Deferring the audit *decision timing* to the last responsible moment means it is made with real information (after Phases 2–3 reveal how the Hub behaves). Accepted risk during design/build: no PDE org-wide audit trail for that window, and logs not captured in the gap are unrecoverable. | 2026-09-30 | Ratified |

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
