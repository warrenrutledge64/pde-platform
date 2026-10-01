# Platform Delivery Engine (PDE) — Inventory (Bill of Materials)

> **Living document.** The authoritative inventory of everything this project is
> made of — every deployed AWS resource, dependency, pinned version — and the
> human-readable form of the restore-point state manifest. Updated at **every
> end-of-phase validation**, with each entry tied to the restore point (git tag)
> under which it was captured.
>
> **Rule:** if it is deployed/produced, it is in this inventory. If it is in this
> inventory, it maps to a restore point. This is the defense against
> code-vs-deployed drift.

- **Environment / target:** Multi-account AWS Organization — management/root
  account `467866449172` (governance/CloudTrail only), `Pipeline-Hub` (PDE control
  plane, co-resident with ZTIE), `Pipeline-Dev`, `Pipeline-Sandbox`,
  `Pipeline-Prod` (deployment targets). **Home region: `us-east-1`** (pinned at
  Story 1.1; the org trail is multi-region but delivers to this home region).
- **Last updated:** 2026-10-01 (Story 1.2 authored + offline-proven; awaiting live Option-B validation)
- **Current restore point:** none yet (`restore/phase-1-green` is cut when Story 1.2's live pass closes Phase 1)

---

## 1. Dependencies & Versions

| Component | Type | Version | Notes |
|-----------|------|---------|-------|
| `infra/member-execution-role.yaml` | CloudFormation template | Story 1.1 | Orchestrate-and-pull trust fabric — member exec role the Hub *orchestrator* invokes (RD-006 amended). Offline-proven (21 invariants). Not yet deployed. |
| `scripts/phase1_gate.py` | Python 3 / Boto3 script | Story 1.2 | Phase-1 gate — Hub (as `pde-hub-orchestrator`) assumes each `pde-member-execution-<env>` role (Dev→Sandbox→Prod) with the ExternalId and prints the returned account ids. Offline-proven (24 invariants). Its live cross-account run is the deferred VD-3b (Phase 2). |
| `scripts/test_phase1_gate.py` | Python 3 (stdlib) checker | Story 1.2 | Offline proof bar for the Phase-1 gate script — 24 source + behaviour invariants against a fake STS stub (no AWS / no network). |
| `DOCS/CLOUDSHELL_BOOTSTRAP.md` | Operator runbook | Story 1.2 | Reproducible Pipeline-Hub CloudShell bootstrap — credential-helper repo clone (no token in URL), explicit feature-branch checkout, AWS CLI / Python 3 / Boto3 / cfn-lint tooling, ExternalId-as-env-var, gate-script usage. |
| `scripts/bootstrap_launchpad.sh` | Bash bootstrap script | Story 1.2 | One named command that stands up + VERIFIES the Hub launch pad (Hub-account check, credential-helper PAT, clean clone + `feature/story-1.2` checkout, fail-loud launch-pad VERIFY). Removes the copy-paste-a-stale-block failure mode (attempts 1–2). |
| `infra/deferred/spoke-execution-role.push-model.yaml` | CloudFormation template (retired) | — | First trust-fabric attempt (Hub-pushes-into-Spoke); superseded by the orchestrate-and-pull model. Preserved for historical reference; do not deploy. |
| `infra/deferred/cloudtrail-org-baseline.yaml` | CloudFormation template (deferred) | Story 4.1 | Org-wide CloudTrail baseline — **deferred** per RD-007; preserved for historical reference; adapted to Hub-delegated at Phase 4. |
| AWS CloudFormation | IaC engine | YAML (native) | Sole IaC standard (RD-004); no Terraform. |
| Python | runtime | 3 (Boto3) | Bootstrap + validation scripting (RD-004). |
| cfn-lint | static analysis | pinned at first use | CloudFormation linting (Universal Criterion 3). |
| cfn-guard | policy-as-code | pinned at first use | CloudFormation policy checks. |
| Checkov | static analysis | pinned at first use | IaC security scanning. |
| Bandit | static analysis | pinned at first use | Python security scanning. |
| AWS Step Functions | orchestration | n/a (managed) | Promotion workflow engine (RD-003). |
| AWS CodeBuild | build/deploy | n/a (managed) | Lint + deploy projects (RD-003). |
| AWS EventBridge | eventing | n/a (managed) | Serverless triggers (Zero-EC2). |

> Versions are pinned as each tool is first introduced by a story; "pinned at
> first use" marks tools not yet exercised.

## 2. Deployed / Produced Artifacts

| Artifact | Type | Name / ID | Phase | Restore point |
|----------|------|-----------|-------|---------------|
| _(none yet — pending Phase 1)_ | | | | |

> Track here the resource classes relevant to PDE: CloudFormation stacks, the
> Org-wide CloudTrail + its S3 log bucket + KMS CMK, cross-account IAM execution
> roles, the Step Functions state machine, CodeBuild projects, and the Golden-Path
> test artifact.

## 3. Components (reusable units)

| Component | Purpose | Version | Interface / contract | Reused by | Restore point |
|-----------|---------|---------|----------------------|-----------|---------------|
| _(none yet)_ | | | | | |

## 4. Restore Points

| Tag | Phase | Date | Code (git SHA) | State manifest | Notes |
|-----|-------|------|----------------|----------------|-------|
| _(none yet — first tag at the Phase 1 gate)_ | | | | | |

---

### Maintenance procedure

1. At each **end-of-phase validation that passes**:
   - Capture the live state via the restore-point state-capture step
     (see [`RESTORE.md`](RESTORE.md)).
   - Update sections 1–3 with any new/changed items.
   - Add a row to section 4 with the git tag + SHA + manifest path.
2. Commit the inventory update as part of the phase-closing commit.
3. The `restore/phase-N-green` git tag and the section-4 row must always agree.
