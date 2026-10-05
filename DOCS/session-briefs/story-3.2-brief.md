# Session Brief — Story 3.2: Commit the artifact + trigger the pipeline to deploy to Pipeline-Dev

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Story 3.2 is the SECOND Phase-3 (Golden Path) story and the FIRST real end-to-end
> pipeline run.** It takes the Story 3.1 zero-cost artifact and drives it through the
> live Phase-2 control plane into `Pipeline-Dev`. Build tier 6 (depends on 3.1 ✅) —
> stays within Phase 3 (no phase transition); it is a tier advance 5→6.

## Story 3.2 — Commit the artifact and trigger the PDE pipeline to deploy to `Pipeline-Dev`

| Field | Value |
|-------|-------|
| **Phase** | 3 — The Golden Path Validation |
| **Build tier** | 6 (depends on Story 3.1 ✅ — a tier advance over tier 5, within Phase 3) |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Builds from restore point** | `restore/phase-2-green` (@ `8f85740`, the gate-passing commit) |
| **Session goal** | Commit the Story 3.1 Golden-Path artifact and trigger the live `pdlv-promotion-pipeline` Step Functions state machine so the Hub orchestrates a cross-account CloudFormation deploy of that artifact into `Pipeline-Dev` (`946509368326`). This is the FIRST real pipeline run — it exercises the live Hub→member cross-account assume (VD-3b). Done when the artifact stack is deployed in Dev and `describe-stacks`/`describe-table` confirms the live `pdlv-golden-path-artifact` table, recorded by an INDEPENDENT validator. |

---

### Background & Context

Phase 2 is ✅ CLOSED (`restore/phase-2-green` @ `8f85740`): the Hub control plane is live
— the `pdlv-promotion-pipeline` STANDARD state machine (Dev→Sandbox→Prod with native
`.waitForTaskToken` approval pauses before Sandbox and before Prod, each promotion starting
the `pdlv-deploy` CodeBuild project via `codebuild:startBuild.sync`) + the `pdlv-lint` /
`pdlv-deploy` CodeBuild projects, all least-privilege and ZTIE-safe. The Phase 2 gate was
proven with a SEPARATE, structurally non-promoting `pdlv-gate-probe` (it reaches the
approval pause but can NEVER deploy) — so the production pipeline carries **no bypass
branch** and has **never actually deployed anything cross-account**. Story 3.1 authored the
payload (`infra/golden-path-artifact.yaml` — one empty on-demand DynamoDB table, sealed PASS
2026-10-04). **Story 3.2 is the first time the real pipeline does a real cross-account
deploy.**

### Objective & Value

- **Objective:** commit the artifact into the location/trigger the pipeline consumes, start
  the `pdlv-promotion-pipeline` execution, and let the Hub orchestrate a cross-account CFN
  deploy of the artifact into `Pipeline-Dev`. The DeployDev stage must succeed and the live
  `pdlv-golden-path-artifact` DynamoDB table must exist in Dev.
- **Why it matters:** this is the first proof that the orchestrate-and-pull control plane
  can actually deliver an artifact into a member account end-to-end — the whole point of the
  Golden Path. Everything before this was authored + statically/probe-proven; 3.2 is the
  first real delivery.

### Scope, Dependencies & Position

- **In scope:** committing the artifact so the pipeline consumes it; starting the pipeline
  execution; **standing up VD-3b** — the live Hub→member trust so the Hub orchestrator role
  (`pdlv-hub-orchestrator`, the RD-009-clean rename of the colliding legacy
  `pde-hub-orchestrator`) can `sts:AssumeRole` into the `pde-member-execution-dev` role with
  the ExternalId, and the member role deploys the artifact LOCALLY in Dev (RD-006
  orchestrate-and-pull); verifying the live Dev deploy (`describe-stacks` + `describe-table`).
- **Out of scope:** the Dev→Sandbox approval + promotion (Story 3.3); Sandbox→Prod (3.4);
  any change to the artifact template itself (frozen from 3.1 unless a real defect forces a
  fix-then-validate-once); the management account (`467866449172`, zero-touch).
- **Depends on:** **Story 3.1 ✅** (sealed PASS 2026-10-04). _Advancement gate satisfied._
- **Unblocks:** Story 3.3 (validate Dev, approve the gate, promote to Sandbox).
- **Roadmap position:** second Phase-3 story; **tier 6 — a tier advance over 3.1 (tier 5),
  WITHIN Phase 3 (no phase transition).** Announce the tier advance at handoff.

### Approach & Constraints

- **Approach:** the Hub orchestrator assumes the member execution role in Dev and the deploy
  runs locally in the member (RD-006). The `pdlv-deploy` CodeBuild project is the deploy
  mechanism the state machine starts per environment. Keep the artifact genuinely zero-cost.
- **Hard constraints:** CloudFormation (YAML) + Python 3 only — no Terraform (RD-004);
  AWS-native + serverless (RD-003); `pdlv-` Hub namespace, ZTIE-safe (RD-009 — never
  `pde-*` for Hub resources; the MEMBER roles keep their `pde-member-execution-<env>` names,
  which is correct — they live in the member accounts, no Hub collision); strictly additive
  (Universal Criterion 5); least privilege (no wildcard/admin; cross-account power is ONLY
  `sts:AssumeRole` into the specific member role); zero-touch management `467866449172`.

### Validation Rationale & Compliance Mapping (optional)

- **Rationale:** a live `describe-stacks` showing the Dev artifact stack `CREATE_COMPLETE`
  plus a `describe-table` returning the live `pdlv-golden-path-artifact` table is the
  skeptical proof the pipeline really delivered cross-account — not a green execution line.
- **Audit evidence produced:** the pipeline execution ARN + history, the Dev stack events,
  and the live table description. (Compliance mappings proposed at authoring, ratified on
  review.)

### Change & Rollback

- **Change type:** standard — FIRST live cross-account deploy (member-account state created).
- **Restore point this builds from:** `restore/phase-2-green` (@ `8f85740`).
- **Backout plan:** `delete-stack` the single trivial artifact stack in `Pipeline-Dev`
  (`946509368326`) — it is one empty, free DynamoDB table, so the blast radius is minimal.
  Any dead `ROLLBACK_COMPLETE`/`*_FAILED` `pdlv-` stack must be swept before a re-deploy
  (the LIVE-RUNBOOK carries the name-agnostic self-heal sweep from the Phase-2 lessons).

### Definition of Done / Validation Gate

- **Done means:** the pipeline executed, the Hub assumed the Dev member role (VD-3b proven
  live — succeeds WITH the ExternalId), the artifact stack deployed `CREATE_COMPLETE` in
  `Pipeline-Dev`, and `describe-table` returns the live `pdlv-golden-path-artifact` table
  (on-demand, `Project=PDE`). **Validated by an INDEPENDENT validator** (not the builder) via
  `DOCS/session-briefs/story-3.2-VALIDATOR-HANDOVER.md`.
- **Validation Result:** `pending`.
- **On pass:** record it, flip 3.2 → ✅; author Story 3.3's warm handoff. _(Does NOT close
  Phase 3 — 3.3/3.4 remain; the Phase 3 gate is the live Prod artifact-metadata query.)_
- **On fail:** stays 🟡; fix (fix-then-validate-once) and re-run.
- **Advancement gate:** Story 3.3 cannot begin until 3.2 is ✅.

### Risks & Watch-Items

- **VD-3b is the likely first blocker.** The production pipeline has never done a real
  cross-account assume (the Phase-2 gate used the non-promoting `pdlv-gate-probe`). The Hub
  orchestrator role (`pdlv-hub-orchestrator`) + the member trust (`pde-member-execution-dev`
  trusting that specific role with the ExternalId) must exist and align, or DeployDev fails
  with an AssumeRole/AccessDenied. Stand this up FIRST and prove the assume live. _(The
  orchestrator was renamed from the colliding legacy `pde-hub-orchestrator` to the clean
  `pdlv-hub-orchestrator` — Q1 decision 2026-10-05 — so the deploy is collision-proof.)_
- **Least-privilege service-delivery actions (the Phase-2 lesson).** If any Step Functions /
  service-integration IAM is touched, certain AWS service-delivery actions reject a
  resource-scoped grant and need `Resource "*"` (the EventBridge `.sync` managed-rule;
  CloudWatch Logs `PutResourcePolicy`). Consult AWS's published IAM template; don't tighten
  the resource by instinct.
- **IAM `Description` must be plain ASCII** (an em-dash broke `CreateRole` in Phase 2; now
  guarded offline). Watch pasted text for smart quotes / em-dashes.
- **Dead-stack sweep before re-deploy.** A dead `ROLLBACK_COMPLETE`/`REVIEW_IN_PROGRESS`
  `pdlv-` stack blocks re-deploy — sweep it first (name-agnostic, `pdlv-*` only, never
  `pde-*`/ZTIE/management); always capture the CFN `CREATE_FAILED` `ResourceStatusReason`
  rather than diagnosing from "it rolled back."
- **Verify the LIVE result, not the green line.** A green `UPDATE_COMPLETE`/execution
  `SUCCEEDED` can hide a stale-checkout or wrong-account deploy — confirm the actual live
  Dev table + its account/tags after the run.
- **ZTIE-safe (RD-009).** `pdlv-` for Hub resources; the member roles correctly keep
  `pde-member-execution-<env>`. Never create a `pde-*` Hub resource.

### Lessons Learned / Carry-Forward *(authored at the end of Story 3.1 — actual lessons)*

- **Story 3.1 sealed PASS 2026-10-04 (Independent Validator), PR #41 head `d88c604`.** The
  Golden-Path payload is `infra/golden-path-artifact.yaml` — a SINGLE empty on-demand
  `AWS::DynamoDB::Table` (`PAY_PER_REQUEST`; one `id` string HASH key; no provisioned
  capacity, stream, GSI, CMK or PITR), `pdlv-`-named via `${NamePrefix}${ArtifactName}`,
  `Project=PDE`-tagged, exports `pdlv-golden-path-artifact-table-{name,arn}`. The two
  unavoidable DynamoDB findings (CKV_AWS_119 CMK + CKV_AWS_28 PITR) carry **justified
  `checkov:skip`** (both add cost for a disposable, zero-data payload). This is the artifact
  3.2 deploys — do NOT change it unless a live defect forces fix-then-validate-once.
- **Design note (DynamoDB over SQS):** checkov's CloudFormation CKV_AWS_27 does not
  recognize SSE-SQS (`SqsManagedSseEnabled`), so an SQS queue would force a CMK or a skip
  anyway — the on-demand table was the cleaner genuinely-zero-cost single resource.
- **Offline proof:** `infra/validate_golden_path_artifact.py` (27 invariants + `--self-test`),
  wired into `.github/workflows/static-bar.yml`. In the build sandbox PyPI is BLOCKED, so
  cfn-lint/Checkov run in CI on the PR head — NOT locally.
- **CI workflow lesson (from 3.1):** the static bar now runs the **merge-order guard LAST**
  (`if: always()`). The guard legitimately turns a deliverable PR RED the whole time the
  story is in validation (gate ARMED); running it last means cfn-lint / Checkov / the
  offline checkers still produce their (green) evidence on the PR head for the validator to
  read, while the guard still fails the job until the close-out disarms the gate at head.
  Expect the same red-until-close-out pattern on 3.2's PR; it is correct, not a defect.
- **VD-3b carries into 3.2 (the first real cross-account assume).** Phase 2 deliberately
  proved its gate with the non-promoting `pdlv-gate-probe`, so the live Hub→member assume
  has NEVER run in production. 3.2's real Dev deploy will fail at DeployDev until
  `pdlv-hub-orchestrator` (Hub; renamed from the colliding legacy `pde-hub-orchestrator`) +
  the `pde-member-execution-dev` trust (member, trusting that specific role + ExternalId)
  exist and align. Treat standing up + proving VD-3b as the
  first task.
- **Current true state at handoff:** Phase 1 ✅ (`restore/phase-1-green`); Phase 2 ✅ CLOSED
  (`restore/phase-2-green` @ `8f85740`); 2.1/2.2/2.3 ✅; **Story 3.1 ✅** (sealed PASS
  2026-10-04, VD-8 CLEARED); the Validation Debt Register is **empty**, the gate is
  **DISARMED**, and 3.2's advancement gate (3.1 ✅) is **satisfied**. 3.2 is tier 6 — a tier
  advance over 3.1 (tier 5), within Phase 3.
- **Account topology (authoritative):** Hub `641628980935`; members Dev `946509368326`,
  Sandbox `586917955591`, Prod `466494951534`; management/root `467866449172` zero-touch;
  Pipeline-Forensics `360999005254` is **ZTIE's**, not PDE.
- **Completeness item (not a 3.2 blocker):** **OD-010** — the paired Phase-2 restore-point
  STATE MANIFEST (RESTORE.md rule 4) is still owed; tracked, not a behavioural blocker.
- **User notes:** _(open for the user)_
