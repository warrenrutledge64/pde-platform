# Session Brief — Story 3.2 · Attempt 6: Trigger the pipeline to deploy to Pipeline-Dev

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Story 3.2 is the SECOND Phase-3 (Golden Path) story and the FIRST real end-to-end
> pipeline run.** It takes the Story 3.1 zero-cost artifact and drives it through the
> live Phase-2 control plane into `Pipeline-Dev`. Build tier 6 (depends on 3.1 ✅) —
> stays within Phase 3 (no phase transition); it is a tier advance 5→6.
>
> **Attempt 6 restart (lean, schema-shaped handoff).** Attempts 1-5 all failed as
> environment/execution/collision misses — none judged the deliverable (stale infra,
> then a name collision, then misnamed `pdlv-` stacks holding resource-name leases). The
> environment preconditions are now the loud `##1` of the PROMPT (reconcile the `pdlv-`
> namespace by NAME → deploy all four branch stacks from inside the clone → pass the
> preflight → only then trigger), not buried in carry-forward. Status unchanged: 3.2
> stays 🟡, VD-9 OPEN, gate ARMED; the sealed attempt verdicts are frozen history.

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
- **Troikauge Moderator gates precede validation.** The live run must pass the four
  Moderator gates in order — Pre-Execution (STEP 0) → Deployment (STEP 2/2d) → Preflight
  (`preflight_story_3_2.py` PASS) → Live Result (STEP 5) — BEFORE the independent
  Validator judges anything (`../../governance/MODERATOR_PROTOCOL.md`;
  `../../governance/AGENTS.md`). The seven non-judging attempts were all gate-class misses.

### Lessons Learned / Carry-Forward *(schema-shaped — pass state, not history)*

> Lean, delta-only. Attempts 1-5 all failed as ENVIRONMENT/execution/collision misses
> (none judged the deliverable), which is exactly the fat/buried-root-cause problem this
> restart fixes: the preconditions that matter are now `##1` of the PROMPT, not here.

- **current_state:** Phase 1 ✅ (`restore/phase-1-green`); Phase 2 ✅ CLOSED
  (`restore/phase-2-green` @ `8f85740`); 2.1/2.2/2.3 ✅; **Story 3.1 ✅** (sealed PASS
  2026-10-04, VD-8 CLEARED). **Story 3.2 is 🟡, VD-9 OPEN, gate ARMED** — the branch
  `feature/story-3.2` is offline+CI green and grep-proven correct, awaiting a clean
  Attempt-6 live run. The two-hop chain is `pdlv-codebuild-service-role` →
  `pdlv-hub-orchestrator` → `pde-member-execution-dev`. The frozen artifact is Story
  3.1's `infra/golden-path-artifact.yaml` (one empty on-demand DynamoDB table,
  `Project=PDE`) — do NOT change it unless a live defect forces fix-then-validate-once.
- **delta (what Attempt 6 must do):** every attempt 1-5 was an ENVIRONMENT miss, never a
  deliverable defect — attempts 1-3 ran OUTSIDE the clone (branch stacks never deployed →
  stale infra); attempt 4 hit the legacy `pde-hub-orchestrator` NAME COLLISION (resolved
  by the Q1 rename → `pdlv-hub-orchestrator`); attempt 5 was blocked by MISNAMED `pdlv-`
  stacks (`pdlv-codebuild-projects`, `pdlv-state-machine`) holding the resource-NAME
  LEASES → `ResourceExistenceCheck`. Attempt 6 MUST, from inside the `~/pde-platform`
  clone on the branch, in order: (a) RECONCILE the `pdlv-` namespace BY NAME (LIVE-RUNBOOK
  STEP 1 — delete any `pdlv-` stack outside the canonical set {`pdlv-hub-orchestrator`,
  `pdlv-codebuild`, `pdlv-promotion-pipeline-stack`}, including healthy-but-misnamed
  strays; `pdlv-*` only, never `pde-*`/mgmt/Forensics); (b) pass the STEP 0 launch-pad
  lock + populate the two `/pdlv/` SecureStrings; (c) deploy all four branch stacks and
  VERIFY each live resource changed; (d) run `scripts/preflight_story_3_2.py` to a
  printed PASS; and only THEN trigger the pipeline. Verify the live Dev table, never the
  green line.
- **pending_blockers:** 3.2's own live validation (owed — the whole point of Attempt 6);
  **OD-010** (the paired Phase-2 restore-point STATE MANIFEST, RESTORE.md rule 4) remains
  OPEN — tracked, not a 3.2 blocker.
- **story_local_context (3.2-specific must-knows):**
  - **VD-3b** is proven live by 3.2's first real Dev deploy; it fails at DeployDev unless
    `pdlv-hub-orchestrator` + the `pde-member-execution-dev` trust exist and align.
  - **Least-privilege service-delivery actions:** if you touch Step Functions /
    service-integration IAM, certain AWS actions reject a resource-scoped grant and need
    `Resource "*"` (EventBridge `.sync` managed-rule; CloudWatch Logs `PutResourcePolicy`)
    — consult AWS's published IAM template, don't tighten by instinct.
  - **IAM `Description` must be plain ASCII** (an em-dash broke `CreateRole`; now guarded).
  - **Namespace reconcile by NAME, not just status (the Attempt-5 lesson).** A
    HEALTHY but MISNAMED `pdlv-` stack from a prior run (e.g. `pdlv-codebuild-projects`,
    `pdlv-state-machine`) holds the real resource-NAME LEASE and collides at deploy with
    `ResourceExistenceCheck` — a status-only sweep (ROLLBACK/*_FAILED) misses it. Sweep
    by NAME+membership: delete any `pdlv-` stack outside the canonical set, `pdlv-*` ONLY,
    never `pde-*`/ZTIE/mgmt; capture the CFN `CREATE_FAILED` `ResourceStatusReason`.
  - **CI pattern:** the static bar runs the merge-order guard LAST (`if: always()`); a
    deliverable PR stays RED (gate ARMED) during validation while the other evidence is
    still produced — correct, not a defect.
  - **RD-009:** `pdlv-` for Hub resources; the member roles correctly keep
    `pde-member-execution-<env>`. Never create a `pde-*` Hub resource.
- **User notes:** _(open for the user)_
