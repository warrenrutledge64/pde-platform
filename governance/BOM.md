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
- **PDE Hub namespace:** **`pdlv-`** (RD-009). The `pde-*` namespace in the Hub is
  **ZTIE's**, not PDE's — see §2.1 Known co-occupants.
- **Last updated:** 2026-10-02 (Phase 2 CLOSED — Story 2.3 sealed PASS at `d19f92c`; `restore/phase-2-green` cut; Hub control plane `pdlv-codebuild` + `pdlv-promotion-pipeline-stack` + the non-promoting `pdlv-gate-probe` deployed + inventoried in §2)
- **Current restore point:** `restore/phase-2-green` — the validated Phase-2 close (Story 2.3: Hub control plane deployed, IAM least-privilege, the `pdlv-gate-probe` reached the approval pause). Git SHA pinned in §4. (Prior: `restore/phase-1-green`.)

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
| PDE member execution role (Dev) | IAM role (CFN stack `pde-trust-fabric`) | `pde-member-execution-dev` in `946509368326` | 1 | `restore/phase-1-green` |
| PDE member execution role (Sandbox) | IAM role (CFN stack `pde-trust-fabric`) | `pde-member-execution-sandbox` in `586917955591` | 1 | `restore/phase-1-green` |
| PDE member execution role (Prod) | IAM role (CFN stack `pde-trust-fabric`) | `pde-member-execution-prod` in `466494951534` | 1 | `restore/phase-1-green` |
| Hub operator launch pad (CloudShell) | Documented environment (not a deployed resource) | Pipeline-Hub `641628980935` CloudShell — token-auth clone + tooling + committed Phase-1 gate script | 1 | `restore/phase-1-green` |
| PDE Lint CodeBuild project | CodeBuild project (CFN stack `pdlv-codebuild`) | `pdlv-lint` in `641628980935` | 2 | `restore/phase-2-green` |
| PDE Deploy CodeBuild project | CodeBuild project (CFN stack `pdlv-codebuild`) | `pdlv-deploy` in `641628980935` | 2 | `restore/phase-2-green` |
| PDE CodeBuild service role | IAM role (CFN stack `pdlv-codebuild`) | `pdlv-codebuild-service-role` in `641628980935` (+ managed policies `pdlv-codebuild-logs`, `pdlv-codebuild-assume-member`) | 2 | `restore/phase-2-green` |
| PDE promotion state machine | Step Functions state machine (CFN stack `pdlv-promotion-pipeline-stack`) | `pdlv-promotion-pipeline` in `641628980935` | 2 | `restore/phase-2-green` |
| PDE promotion state-machine role | IAM role (CFN stack `pdlv-promotion-pipeline-stack`) | `pdlv-promotion-pipeline-role` in `641628980935` (+ managed policies `pdlv-sfn-start-deploy`, `pdlv-sfn-sync-events`, `pdlv-sfn-publish-approval`, `pdlv-sfn-logs`) | 2 | `restore/phase-2-green` |
| PDE promotion approval topic | SNS topic (CFN stack `pdlv-promotion-pipeline-stack`) | `pdlv-promotion-approval` in `641628980935` (SSE `alias/aws/sns`) | 2 | `restore/phase-2-green` |
| PDE promotion execution log group | CloudWatch Logs group (CFN stack `pdlv-promotion-pipeline-stack`) | `/aws/vendedlogs/states/pdlv-promotion-pipeline` in `641628980935` | 2 | `restore/phase-2-green` |
| PDE Phase-2 gate probe state machine | Step Functions state machine (CFN stack `pdlv-promotion-pipeline-stack`) | `pdlv-gate-probe` in `641628980935` — structurally non-promoting (no deploy state; Fail terminal); proves the approval pause | 2 | `restore/phase-2-green` |
| PDE gate-probe role | IAM role (CFN stack `pdlv-promotion-pipeline-stack`) | `pdlv-gate-probe-role` in `641628980935` (+ managed policies `pdlv-gate-probe-publish`, `pdlv-gate-probe-logs`) — publish + own-logs only | 2 | `restore/phase-2-green` |
| PDE gate-probe log group | CloudWatch Logs group (CFN stack `pdlv-promotion-pipeline-stack`) | `/aws/vendedlogs/states/pdlv-gate-probe` in `641628980935` | 2 | `restore/phase-2-green` |

> The three member roles trust the specific Hub role `pde-hub-orchestrator` + an
> `sts:ExternalId` (Story 1.1, RD-006). They retain the `pde-member-execution-<env>`
> names (member accounts, not the Hub — no `pdlv-` rename needed; RD-009). The Hub
> orchestrator role itself is Phase-2 work (then VD-3b runs the gate script live).

> Track here the resource classes relevant to PDE: CloudFormation stacks, the
> Org-wide CloudTrail + its S3 log bucket + KMS CMK, cross-account IAM execution
> roles, the Step Functions state machine, CodeBuild projects, and the Golden-Path
> test artifact.

### 2.1 Known co-occupants of the Hub (NOT PDE-owned — environment fact)

> These are recorded for drift-defense and namespace awareness, **not** as PDE
> artifacts (PDE does not own, deploy, or restore them). Discovered live 2026-10-01
> during the Story 1.2 gate; they drove **RD-009** (PDE uses `pdlv-`, not `pde-`) and
> are tracked as **OD-004** (namespace) / **OD-005** (untagged). PDE must never
> deploy, modify, or tear these down (Universal Criterion 5 — non-destructive).

| Occupant | Owner | Account | Notes |
|----------|-------|---------|-------|
| 18 × `pde-*` CloudFormation stacks | **Unattributed shadow footprint** (descriptions mix ZTIE + PDE concepts; in NEITHER project's BOM — OD-005) | `Pipeline-Hub` `641628980935` | Created Jun–Aug 2026, **untagged**. `pde-ztie-websocket-api`, `pde-intake-gateway`(+`-production`), `pde-intake-broker`, `pde-ingestion-vault`, `pde-vault-writer`, `pde-hub-synthesis-parser`, `pde-hub-identity-stack`, `pde-ui-hosting-stack`, `pde-compliance-dashboard`, `pde-compliance-heatmap`, `pde-governance-pipeline`, `pde-remediation-statemachine`, `pde-eventbridge-approval-rule`, `pde-event-trigger-foundation`, `pde-artifact-store`, `pde-codebuild-foundation`, `github-oidc-pde-burn`. **Not in the governed ZTIE BOM** (which tracks CDK `Ztie*` stacks, tagged `Project=ZTIE`) and not PDE's — a pre-existing hand-rolled effort outside the BOM discipline. Point-in-time snapshot; reconciliation is a program-level decision (RD-001 — not PDE's to fix). |

## 3. Components (reusable units)

| Component | Purpose | Version | Interface / contract | Reused by | Restore point |
|-----------|---------|---------|----------------------|-----------|---------------|
| _(none yet)_ | | | | | |

## 4. Restore Points

| Tag | Phase | Date | Code (git SHA) | State manifest | Notes |
|-----|-------|------|----------------|----------------|-------|
| `restore/phase-1-green` | 1 | 2026-10-01 | `7bd6358` (validated commit; annotated tag) | _live-state manifest to be captured by the operator via the RESTORE.md read-only Boto3 capture from Hub CloudShell (Dev/Sandbox/Prod member-role projections + Hub launch-pad); path recorded here on capture_ | Phase 1 close — Story 1.2 sealed PASS (operator launch pad proven live) + Story 1.1 trust fabric. Live cross-account `AssumeRole` deferred (VD-3b, Phase 2). | |
| `restore/phase-2-green` | 2 | 2026-10-03 (re-cut) | **RE-CUT to `8f85740`** — the PR #37 Phase-2 close-out merge commit on `main`, the gate-passing CI-green baseline (carries the CKV_AWS_111 reconciliation + root RESTORE.md pointer + the Phase 2 ✅ ledger). _Supersedes the original annotated tag at `3c42d03` (PR #31 merge, validated `d19f92c`), which lacked the CI-green reconciliation and failed the static bar — see OD-012._ | _live-state manifest to be captured by the operator via the RESTORE.md read-only Boto3 capture from Hub CloudShell: the `pdlv-codebuild` + `pdlv-promotion-pipeline-stack` CFN stacks (template_sha256/params/tags), the `pdlv-promotion-pipeline` + `pdlv-gate-probe` state-machine definition SHAs, and the `pdlv-*` IAM roles (trust + attached least-privilege policies); path recorded here on capture — **OWED as OD-010**_ | Phase 2 CLOSE — end-of-phase gate SEALED PASS (Independent Validator, 2026-10-03): live `pdlv-promotion-pipeline-stack` tagged `Project=PDE` (live==IaC), the non-promoting `pdlv-gate-probe` reached/held `AwaitSandboxApproval` under least-privilege IAM, 62 offline invariants + self-test. The §2 inventory above maps to this restore point. |

---

### Maintenance procedure

1. At each **end-of-phase validation that passes**:
   - Capture the live state via the restore-point state-capture step
     (see [`RESTORE.md`](RESTORE.md)).
   - Update sections 1–3 with any new/changed items.
   - Add a row to section 4 with the git tag + SHA + manifest path.
2. Commit the inventory update as part of the phase-closing commit.
3. The `restore/phase-N-green` git tag and the section-4 row must always agree.
