# Session Prompt — Story 3.2 · Attempt 5 (executor-facing)

> Source of truth: [`story-3.2-brief.md`](story-3.2-brief.md). Operator surface:
> [`story-3.2-LIVE-RUNBOOK.md`](story-3.2-LIVE-RUNBOOK.md). Validator:
> [`story-3.2-VALIDATOR-HANDOVER.md`](story-3.2-VALIDATOR-HANDOVER.md).
> Copy the fenced block, fill any `{{...}}`, paste to start the session.
>
> **Why Attempt 5 / why a restart:** attempts 1-4 ALL failed as execution/collision
> misses — **none ever judged the deliverable.** The branch code is offline/CI-green and
> grep-proven correct. This session's whole job is a CLEAN live run against the ACTUAL
> branch infra. The #1 rule below exists because 3 of 4 attempts ran against stale infra
> (operator outside the clone, branch stacks never deployed). Read #1 first; everything
> else is secondary.

```
You are the execution agent for Platform Delivery Engine (PDE) — Story 3.2, Attempt 5.
PDE is a validation-gated multi-account AWS delivery platform. Pipeline-Hub
(641628980935) ORCHESTRATES AND PULLS from member accounts. Story 3.2 is the FIRST real
end-to-end pipeline run: trigger the live pdlv-promotion-pipeline so the Hub does a
cross-account CloudFormation deploy of the frozen Story 3.1 artifact into Pipeline-Dev
(946509368326), closing VD-3b (the live Hub→member assume).

# ##1 ROOT CAUSE OF ATTEMPTS 1-4 — THE ONE THING THAT MUST NOT REPEAT ##
Three of four attempts validated STALE, un-redeployed infra: the operator was OUTSIDE
the git clone (`git rev-parse HEAD` → "fatal: not a git repository"), so the branch
stacks were NEVER deployed and the pipeline hit legacy/Phase-1 infra. Attempt 4 hit a
name collision (now resolved: orchestrator renamed to `pdlv-hub-orchestrator`).
THEREFORE, before anything is validated, in ONE Hub CloudShell shell, from INSIDE the
`~/pde-platform` clone on `feature/story-3.2`:
  (a) run the LIVE-RUNBOOK STEP 0 launch-pad lock (hard-exits unless you are inside the
      clone, on the branch, with every deliverable on disk) + populate the two /pdlv/
      SecureStrings (external-id, repo-token) with REAL values;
  (b) deploy ALL FOUR branch stacks FROM the branch: STEP 2a orchestrator, 2b codebuild,
      2c state-machine, 2d Dev member role — and VERIFY each live resource CHANGED (the
      live role carries `Story=3.2` + the pdlv--scoped CFN+DynamoDB grant), never trust
      the deploy line;
  (c) run `python3 scripts/preflight_story_3_2.py` to a printed PASS — it hard-fails
      against stale infra. A non-PASS here = STOP and fix the environment, do NOT trigger
      the pipeline.
Only after (a)(b)(c) does triggering the pipeline (STEP 4) test the DELIVERABLE. A green
execution/deploy against stale infra is the exact false signal that burned 4 cycles.

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
- VERIFY THE LIVE RESOURCE, not the green line (the attempts 1-4 lesson, above).

# FIRST — VALIDATION & ADVANCEMENT GATE (HALT if unmet)
- Confirm in governance/RUNBOOK.md: Story 3.1 is ✅; 3.2 depends on it. 3.2 is build
  tier 6 — a tier advance over 3.1 (tier 5), WITHIN Phase 3 (no phase change).
- 3.2 itself is 🟡 with VD-9 OPEN / gate ARMED — that is EXPECTED (reworking a 🟡 story
  is the covenant working). Do NOT flip status on inference. Attempts 1-4 sealed verdicts
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
Run the clean Attempt-5 live validation: do #1(a)(b)(c), then trigger the pipeline and
let the independent validator seal the live Dev deploy (artifact stack CREATE_COMPLETE +
`describe-table` returns the live pdlv-golden-path-artifact, on-demand, Project=PDE). On
a sealed PASS: record verbatim, flip 3.2 ✅, clear VD-9/VD-3b, add the new deployed
resources to BOM §2, author Story 3.3's warm handoff. On FAIL: fix-then-validate-once. On
INCONCLUSIVE (execution failure): re-run cleanly — do NOT re-judge the deliverable.
```
