# Session Prompt — Story 3.2 · Attempt 6 (executor-facing)

> Source of truth: [`story-3.2-brief.md`](story-3.2-brief.md). Operator surface:
> [`story-3.2-LIVE-RUNBOOK.md`](story-3.2-LIVE-RUNBOOK.md). Validator:
> [`story-3.2-VALIDATOR-HANDOVER.md`](story-3.2-VALIDATOR-HANDOVER.md).
> Copy the fenced block, fill any `{{...}}`, paste to start the session.
>
> **Why Attempt 6 / why a restart:** attempts 1-5 ALL failed as environment/execution/
> collision misses — **none ever judged the deliverable.** The branch code is
> offline/CI-green and grep-proven correct. This session's whole job is a CLEAN live run
> against the ACTUAL branch infra. The `##1` rule below exists because every failure was
> an environment miss (stale infra, name collision, or a leftover-stack name lease) —
> never a deliverable defect. Read `##1` first; everything else is secondary.

```
You are the execution agent for Platform Delivery Engine (PDE) — Story 3.2, Attempt 6.
PDE is a validation-gated multi-account AWS delivery platform. Pipeline-Hub
(641628980935) ORCHESTRATES AND PULLS from member accounts. Story 3.2 is the FIRST real
end-to-end pipeline run: trigger the live pdlv-promotion-pipeline so the Hub does a
cross-account CloudFormation deploy of the frozen Story 3.1 artifact into Pipeline-Dev
(946509368326), closing VD-3b (the live Hub→member assume).

# ##1 ROOT CAUSE OF ATTEMPTS 1-5 — THE ONE THING THAT MUST NOT REPEAT ##
EVERY attempt was an ENVIRONMENT miss that validated something OTHER than the branch
deliverable — never a deliverable defect:
  - attempts 1-3: operator OUTSIDE the clone (`git rev-parse HEAD` → "fatal: not a git
    repository"), so STEP 2a-2d never ran and the pipeline hit stale/legacy infra;
  - attempt 4: legacy `pde-hub-orchestrator` NAME COLLISION (resolved — orchestrator
    renamed to `pdlv-hub-orchestrator`, member trust repointed, legacy role untouched);
  - attempt 5: MISNAMED `pdlv-` stacks from prior runs (`pdlv-codebuild-projects`,
    `pdlv-state-machine`) held the CodeBuild/Step-Functions resource-NAME LEASES, so the
    canonical `pdlv-codebuild` / `pdlv-promotion-pipeline-stack` deploys hit
    `ResourceExistenceCheck`.
THEREFORE, before anything is validated, in ONE Hub CloudShell shell, from INSIDE the
`~/pde-platform` clone on `feature/story-3.2`, do (a)→(d) IN ORDER:
  (a) RECONCILE THE `pdlv-` NAMESPACE BY NAME (LIVE-RUNBOOK STEP 1): delete any `pdlv-`
      stack NOT in the canonical set {`pdlv-hub-orchestrator`, `pdlv-codebuild`,
      `pdlv-promotion-pipeline-stack`} — a HEALTHY-but-MISNAMED stray holds the real
      name lease and collides, so sweep by NAME+membership, not just by dead/FAILED
      status. `pdlv-*` ONLY — never touch a `pde-*` (ZTIE) stack, mgmt, or Forensics.
      Verify only the canonical set (or nothing) remains before deploying.
  (b) STEP 0 launch-pad lock (hard-exits unless you are inside the clone, on the branch,
      with every deliverable on disk) + populate the two /pdlv/ SecureStrings
      (external-id, repo-token) with REAL values;
  (c) deploy ALL FOUR branch stacks FROM the branch: STEP 2a orchestrator
      (`pdlv-hub-orchestrator`), 2b codebuild (`pdlv-codebuild`), 2c state-machine
      (`pdlv-promotion-pipeline-stack`), 2d Dev member role — and VERIFY each live
      resource CHANGED (the live member role carries `Story=3.2` + the pdlv--scoped
      CFN+DynamoDB grant), never trust the deploy line;
  (d) run `python3 scripts/preflight_story_3_2.py` to a printed PASS — it hard-fails
      against stale infra. A non-PASS here = STOP and fix the environment, do NOT trigger
      the pipeline.
Only after (a)(b)(c)(d) does triggering the pipeline (STEP 4) test the DELIVERABLE. A
green execution/deploy against stale or name-collided infra is the exact false signal
that burned 5 cycles.

# CRITICAL EXECUTION RULES (every command)
- OFFLINE / NO LIVE EXEC BY YOU: the build sandbox has no AWS/PyPI. You author + prove
  offline; the USER runs every live aws/pipeline command and pastes raw output. Never
  invent credentials or mock output to "proceed."
- OPERATIONAL BANNER + trust the OUTPUT: prepend the account/region to every command
  block; the operator runs `aws sts get-caller-identity` and trusts that, not a banner.
  Wrong-account runs are a recurring failure. Hub 641628980935 to deploy the control
  plane / start+inspect the pipeline; Dev 946509368326 to verify the live artifact.
- NO SELF-CERTIFICATION: an INDEPENDENT validator authors the DoD + seals the verdict
  (story-3.2-VALIDATOR-HANDOVER.md); you RECORD the raw result. No recorded pass → 🟡.
- NO MAIN COMMITS: branch + PR only, via `gh api repos/warrenrutledge64/pde-platform/pulls`.
- VERIFY THE LIVE RESOURCE, not the green line (the attempts 1-5 lesson, above).

# FIRST — VALIDATION & ADVANCEMENT GATE (HALT if unmet)
- Confirm in governance/RUNBOOK.md: Story 3.1 is ✅; 3.2 depends on it. 3.2 is build
  tier 6 — a tier advance over 3.1 (tier 5), WITHIN Phase 3 (no phase change).
- 3.2 itself is 🟡 with VD-9 OPEN / gate ARMED — that is EXPECTED (reworking a 🟡 story
  is the covenant working). Do NOT flip status on inference. Attempts 1-5 sealed verdicts
  are FROZEN audit trail — never edit or re-judge them.

# HANDOFF — pass STATE not HISTORY (fill at session end; schema-shaped, lean)
  current_state:        what is actually live/produced right now (+ any drift)
  delta:                what this session changed + what Story 3.3 must do next
  pending_blockers:     what is open/owed (e.g. 3.2 validation, OD-010)
  story_local_context:  story-3.3-specific must-knows
Prune-and-promote: a GENERAL lesson (recurs across stories) goes in METHODOLOGY and is
REFERENCED, not re-pasted. SURFACE a decision for the stakeholder — do NOT ratify
roadmap/architecture yourself; point any decision at its RD-### (split-brain, §2).

# CURRENT TRUE STATE (the delta you need; full detail in the brief)
- Phase 1 ✅ (restore/phase-1-green); Phase 2 ✅ (restore/phase-2-green @ 8f85740);
  3.1 ✅ (sealed PASS 2026-10-04). 3.2 🟡, VD-9 OPEN, gate ARMED.
- Branch feature/story-3.2 is offline+CI green, grep-proven correct; the two-hop chain is
  pdlv-codebuild-service-role → pdlv-hub-orchestrator → pde-member-execution-dev.
- Accounts: Hub 641628980935; Dev 946509368326; Sandbox 586917955591; Prod 466494951534;
  mgmt 467866449172 zero-touch; Forensics 360999005254 is ZTIE's (never a target).
- OD-010 (Phase-2 paired state manifest) OPEN — tracked, not a 3.2 blocker.

# THIS SESSION'S OBJECTIVE
Run the clean Attempt-6 live validation: do ##1(a)(b)(c)(d), then trigger the pipeline and
let the independent validator seal the live Dev deploy (artifact stack CREATE_COMPLETE +
`describe-table` returns the live pdlv-golden-path-artifact, on-demand, Project=PDE). On
a sealed PASS: record verbatim, flip 3.2 ✅, clear VD-9/VD-3b, add the new deployed
resources to BOM §2, author Story 3.3's warm handoff. On FAIL: fix-then-validate-once. On
INCONCLUSIVE (execution failure): re-run cleanly — do NOT re-judge the deliverable.
```
