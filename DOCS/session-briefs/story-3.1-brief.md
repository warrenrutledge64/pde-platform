# Session Brief — Story 3.1: Author a trivial, zero-cost Golden-Path artifact (opens Phase 3)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Story 3.1 is the FIRST brick of Phase 3 (The Golden Path Validation).** It is a
> small, offline-provable authoring story — the payload that Stories 3.2–3.4 will send
> through the now-deployed PDE pipeline. Build tier 5 — a tier advance over Phase 2
> (tier 4); re-confirm the full dependency set at start.

## Story 3.1 — Author a trivial, zero-cost artifact (empty DynamoDB table or SQS queue) in CloudFormation

| Field | Value |
|-------|-------|
| **Phase** | 3 — The Golden Path Validation |
| **Build tier** | 5 (depends on the Phase 2 gate ✅ — a tier advance over tier 4) |
| **Date** | 2026-10-03 (authored; awaiting independent validation) |
| **Status** | 🟡 In Progress (built + offline-proven; VD-8 open) |
| **Builds from restore point** | `restore/phase-2-green` (Phase 2 close) |
| **Session goal** | Author a minimal, zero-cost CloudFormation artifact (e.g. an empty on-demand DynamoDB table OR an SQS queue) that will serve as the Golden-Path payload traversing the PDE pipeline Dev→Sandbox→Prod. Offline-prove it (lint clean, single trivial resource, `pdlv-`/`Project=PDE`). Nothing is deployed in 3.1. |

---

### Background & Context

Phase 2 is closed (`restore/phase-2-green`, Story 2.3 sealed PASS 2026-10-02): the Hub
control plane is live — the `pdlv-promotion-pipeline` Step Functions state machine +
`pdlv-lint`/`pdlv-deploy` CodeBuild projects, all least-privilege and ZTIE-safe. Phase 3
proves the **end-to-end delivery path** by sending a real (but trivial) infrastructure
artifact through that pipeline. Story 3.1 authors that artifact; 3.2 commits + deploys it
to Dev; 3.3 promotes to Sandbox; 3.4 releases to Prod.

### Objective & Value

- **Objective:** author a tiny, zero-cost CloudFormation template describing a SINGLE
  trivial resource (an empty on-demand `AWS::DynamoDB::Table` with `PAY_PER_REQUEST`, or an
  `AWS::SQS::Queue`) — the Golden-Path test payload. Offline-prove it (cfn-lint clean; the
  template describes exactly one trivial resource; `pdlv-` naming + `Project=PDE` tags).
- **Why it matters:** a minimal, zero-cost artifact de-risks the first real end-to-end run
  (3.2–3.4) — if the pipeline mis-deploys, the blast radius is one empty table/queue, and
  there is no standing cost.

### Scope, Dependencies & Position

- **In scope:** the artifact CloudFormation template + its offline proof (a stdlib
  invariant checker in the `infra/validate_*.py` style, or cfn-lint, per the validator's
  DoD). Choosing DynamoDB-table vs SQS-queue is a small design call — pick the cheaper/
  simpler; both are zero-cost at rest on-demand.
- **Out of scope:** committing/triggering the pipeline (3.2); any deploy to Dev/Sandbox/
  Prod (3.2–3.4); changes to the Phase-2 control plane; the management account.
- **Depends on:** **Phase 2 gate ✅** (Story 2.3 sealed PASS). _Advancement gate satisfied._
- **Unblocks:** Story 3.2 (commit the artifact + trigger the pipeline to deploy to Dev).
- **Roadmap position:** first Phase-3 story; **tier 5 — a tier advance over Phase 2
  (tier 4)** AND the **P2→P3 phase transition**. Announce both at handoff.

### Approach & Constraints

- **Approach:** author `infra/<artifact>.yaml` (one trivial resource, `pdlv-`-prefixed
  name, `Project=PDE` tag); offline-prove it (no deploy). Keep it genuinely zero-cost
  (on-demand/`PAY_PER_REQUEST`; no provisioned capacity, no streams, no KMS CMK needed).
- **Hard constraints:** CloudFormation (YAML) + Python 3 only — no Terraform (RD-004);
  AWS-native + serverless (RD-003); `pdlv-` namespace, ZTIE-safe (RD-009 — never `pde-*`);
  strictly additive (Universal Criterion 5); zero-touch management account `467866449172`.

### Validation Rationale & Compliance Mapping (optional)

- **Rationale:** a minimal, offline-provable payload is the safest possible first subject
  for the end-to-end Golden-Path run — correctness of the pipeline is tested, not the
  payload.
- **Audit evidence produced:** the artifact template + its offline-proof output (the live
  deploy evidence comes in 3.2–3.4).

### Change & Rollback

- **Change type:** standard, author-only (offline; nothing deployed in 3.1).
- **Restore point this builds from:** `restore/phase-2-green`.
- **Backout plan:** author-only — revert the branch; no live state to roll back. (When
  3.2 deploys it, backout is `delete-stack` on the single trivial artifact stack.)

### Definition of Done / Validation Gate

- **Done means:** the artifact template exists, lints clean (cfn-lint), describes exactly
  ONE trivial zero-cost resource, carries `pdlv-` naming + `Project=PDE`, and its offline
  checker (if authored) passes with a `--self-test`. **Validated by an INDEPENDENT
  validator** (not the builder) via `DOCS/session-briefs/story-3.1-VALIDATOR-HANDOVER.md`.
- **Validation Result:** `pending`.
- **On pass:** record it, flip 3.1 → ✅; author Story 3.2's warm handoff. _(Does NOT close
  Phase 3 — 3.2–3.4 remain; the Phase 3 gate is the live Prod artifact-metadata query.)_
- **On fail:** stays 🟡; fix (fix-then-validate-once) and re-run.
- **Advancement gate:** Story 3.2 cannot begin until 3.1 is ✅.

### Risks & Watch-Items

- **Keep it genuinely zero-cost.** On-demand DynamoDB (`PAY_PER_REQUEST`) or a plain SQS
  queue; no provisioned throughput, no streams, no CMK — the point is a free, disposable
  payload.
- **This is author-only — do NOT deploy in 3.1.** The first live deploy of the artifact is
  Story 3.2 (through the pipeline, not by hand).
- **Match any offline checker's tool scope** (the 2.2 lesson): if you add a CI/static step,
  scope it consistently to the active artifact.
- **ZTIE-safe (RD-009).** `pdlv-` only; never a `pde-*` name.

### Lessons Learned / Carry-Forward *(authored at the end of Story 2.3 — actual lessons)*

- **Phase 2 took 10 live attempts to a sealed PASS — every durable lesson is now an
  offline invariant** in `infra/validate_state_machine.py` (62 invariants + `--self-test`;
  the 62nd is the OD-012 justified `checkov:skip=CKV_AWS_111:` on the AWS-mandated
  `events:Put*` `Resource "*"`, added when the CI static bar surfaced that latent finding).
  The real deliverable defects were all one class: **AWS service-delivery actions that
  reject a resource-scoped IAM grant and require `Resource "*"`** — the EventBridge `.sync`
  managed-rule (`events:PutRule/PutTargets/DescribeRule`) and CloudWatch Logs
  `logs:PutResourcePolicy`. Scope the *write* actions (`CreateLogStream`/`PutLogEvents`),
  but grant those service-delivery actions on `"*"`. If 3.x adds any Step Functions /
  service-integration IAM, expect this and consult AWS's published IAM template rather than
  tightening the resource by instinct.
- **A dummy/gate run cannot perform a real cross-account assume** (member trust is the
  Phase-3/VD-3b `pde-hub-orchestrator` path). Phase 2's gate was proven by a SEPARATE,
  structurally non-promoting `pdlv-gate-probe` (no deploy state; `Fail` terminal; publish+
  logs-only role) so the production pipeline carries **no bypass branch**. For Phase 3's
  real runs, the member trust / `pde-hub-orchestrator` + the live cross-account assume
  (**VD-3b**) is the thing to stand up — a dummy run through the real pipeline WILL fail at
  `DeployDev` until that exists. Expect to address VD-3b as part of 3.2's real Dev deploy.
- **IAM `Description` must be plain ASCII** (an em-dash broke `CreateRole`); now guarded
  offline. Watch pasted text for smart quotes / em-dashes in any new IAM resource.
- **Operational: a dead `ROLLBACK_COMPLETE`/`REVIEW_IN_PROGRESS` stack blocks re-deploy** —
  the LIVE-RUNBOOK STEP 1a name-agnostic sweep clears any dead `pdlv-` stack first; and
  always capture the CFN `CREATE_FAILED` `ResourceStatusReason` (STEP 3a) rather than
  diagnosing from "it rolled back".
- **Current true state at handoff:** Phase 1 ✅ (`restore/phase-1-green`); Phase 2 ✅
  CLOSED (`restore/phase-2-green`); 2.1/2.2/2.3 all ✅; the Validation Debt Register is
  **empty**, the gate is **DISARMED**, and 3.1's advancement gate (Phase 2 gate passed) is
  **satisfied**. 3.1 is tier 5 — a tier advance over Phase 2 (tier 4) and the P2→P3 phase
  transition.
- **Account topology (authoritative):** Hub `641628980935`; members Dev `946509368326`,
  Sandbox `586917955591`, Prod `466494951534`; management/root `467866449172` zero-touch;
  Pipeline-Forensics `360999005254` is **ZTIE's**, not PDE.
- **VD-3b carries into Phase 3.** The live Hub→member `sts:AssumeRole`
  (`python3 scripts/phase1_gate.py`) runs once `pde-hub-orchestrator` exists — most likely
  needed for 3.2's real Dev deploy.
- **User notes:** _(open for the user)_
