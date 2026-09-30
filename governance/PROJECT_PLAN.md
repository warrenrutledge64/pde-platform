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

### Phase 1 — Governance Baseline & Trust Fabric
- **Goal:** Establish a fresh, untainted audit logging baseline across the
  Organization, then deploy the foundational cross-account IAM trust relationships
  from the Hub to the Spoke accounts.
- **Gate:** From an AWS CloudShell session in the Hub account, a human operator
  executes a Boto3 script that successfully performs an STS `AssumeRole` into Dev,
  Sandbox, and Prod sequentially, returning their Account IDs, **and** verifies the
  new CloudTrail bucket has begun receiving log files for those accounts.
- **Stories:**
  - **Story 1.1:** Deploy a net-new Organization-wide CloudTrail, including a new
    centralized S3 logging bucket and KMS encryption key, ensuring all `Pipeline-*`
    accounts are captured.
  - **Story 1.2:** Deploy cross-account IAM execution roles in Dev, Sandbox, and
    Prod that explicitly trust the Hub account for deployment operations.
  - **Story 1.3:** Configure local AWS CloudShell environment with repository
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

## 4. Dependency Map

**Hard dependencies (X cannot start until Y exists):**
- **Phase 2 (Control Plane) ← Phase 1 (Governance & Trust).** The Hub cannot
  orchestrate deployments until the Spoke accounts explicitly trust it, and no
  actions should be taken until the new CloudTrail baseline is actively recording.
- **Phase 3 (Golden Path) ← Phase 2 (Control Plane).** The pipeline must be fully
  deployed and paused-state verified before a real artifact can traverse it.
- **Story 1.2 (cross-account trust roles) ← Story 1.1 (CloudTrail baseline).** No
  trust-fabric actions until the clean audit baseline is actively recording.
- **Story 1.3 (CloudShell bootstrap access) ← Story 1.2 (trust roles exist to
  assume).**
- **Story 2.3 (bootstrap PDE infra) ← Stories 2.1 + 2.2 (the CodeBuild + Step
  Functions templates it deploys).**
- **Story 3.2 ← Story 3.1** (artifact must exist before it is committed/deployed);
  **3.3 ← 3.2**, **3.4 ← 3.3** (promotion is strictly sequential Dev → Sandbox →
  Prod).

**Shared foundations pulled forward (multi-phase reuse):**
- **The clean CloudTrail audit baseline (Story 1.1)** underpins every subsequent
  cross-account action in Phases 2 and 3 — it is built once, first, so every later
  deployment is captured from Day 1.
- **The cross-account trust roles (Story 1.2)** are the reusable substrate the Hub
  control plane assumes for *all* Dev/Sandbox/Prod deployments in Phases 2–3.

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
| **RD-005** | **Audit Baseline.** Establish a completely new Org-wide CloudTrail and logging bucket. | Ensures a clean, untainted governance boundary starting from Day 1 of the new platform. | 2026-09-29 | Ratified |

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
