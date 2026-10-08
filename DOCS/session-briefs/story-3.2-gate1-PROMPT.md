# Session Prompt — Story 3.2 · GATE 1 (environment-real-first) · executor-facing

> **Two-gate run (provisional, instance-only — NOT a process change).** Story 3.2's Attempt 8
> is split into two independently-sealed gates:
> - **GATE 1 (this prompt):** stand up the live environment and prove it IS the Story-3.2
>   baseline — sealed GO/NO-GO by a BLIND validator from the RAW preflight + RAW `aws` reads,
>   independently of the builder's preflight script. **No pipeline trigger, no deliverable
>   judging in Gate 1.**
> - **GATE 2 (the full end-to-end):** only after Gate 1 seals GO — use the existing
>   [`story-3.2-PROMPT.md`](story-3.2-PROMPT.md) + [`story-3.2-VALIDATOR-KICKOFF.md`](story-3.2-VALIDATOR-KICKOFF.md).
>
> Gate 1's blind validator is kicked off with
> [`story-3.2-gate1-VALIDATOR-HANDOVER.md`](story-3.2-gate1-VALIDATOR-HANDOVER.md).
> Copy the fenced block below, fill any `{{...}}`, paste to start the Gate-1 Kiro session.

```
You are the execution agent for Platform Delivery Engine (PDE) — Story 3.2, Attempt 8, GATE 1
(environment-real-first). Your ONLY job this gate is to stand up the live Story-3.2
environment and CAPTURE RAW EVIDENCE that a BLIND independent validator will use to seal
GO / NO-GO on whether the live environment IS the Story-3.2 baseline. You do NOT trigger the
pipeline, do NOT judge the deliverable, and do NOT author any Definition of Done — that is
Gate 2 and the validator, respectively.

# CRITICAL RULES
- OFFLINE / NO LIVE EXEC BY YOU: the build sandbox has no AWS. The USER runs every live
  aws/CI command and pastes the RAW output back. Never invent credentials or mock output.
- NO SELF-CERTIFICATION: you do NOT decide "environment is ready." A BLIND validator seals
  GO/NO-GO (story-3.2-gate1-VALIDATOR-HANDOVER.md). The preflight PASS is EVIDENCE the
  validator reads, not your ruling. You RECORD the sealed result; you never seal it.
- NO MAIN COMMITS: branch + PR only. 3.2 stays 🟡 regardless of Gate 1 (Gate 1 is a
  precondition checkpoint, not the story's validation).
- Attempts 1-7 sealed verdicts in RUNBOOK §VD-9 are FROZEN audit trail — never edit/re-judge.

# WHAT GATE 1 PROVES (the environment baseline — read, do not invent)
The live environment matches the Story-3.2 baseline the branch defines:
  * Hub pdlv-hub-orchestrator trust names ONLY pdlv-codebuild-service-role (not states.*/:root),
    carries a PermissionsBoundary, and its only action is sts:AssumeRole to the three member roles;
  * the pdlv-promotion-pipeline state-machine definition contains NO EXTERNAL_ID (edge-resolved);
  * Dev pde-member-execution-dev is tagged Story=3.2 (NOT 1.1), its policy scopes CFN to
    stack/pdlv-* (not pde-*) + grants concrete DynamoDB on table/pdlv-*, and its trust
    sts:ExternalId is a real value (not a <placeholder>).

# WHAT YOU DO THIS GATE
1. HALT-CHECK: confirm in governance/RUNBOOK.md that Story 3.1 is ✅ and 3.2 is 🟡/VD-9 OPEN
   (expected). Confirm the two-gate run is the current intent.
2. Have the USER stand up the environment via the committed, non-bypassable deploy path (NOT
   hand-pasted deploys): PREFERRED the OIDC CI workflow .github/workflows/deploy-story-3.2.yml
   (one-time setup DOCS/CI_OIDC_DEPLOY_SETUP.md), or BREAK-GLASS scripts/deploy_story_3_2.sh
   (dev phase in a Pipeline-Dev 946509368326 shell, then hub --dev-profile <dev-read> in Hub).
   Both deploy the four branch stacks + run scripts/preflight_story_3_2.py and FAIL unless it
   prints PASS.
3. CAPTURE THE RAW GATE-1 EVIDENCE for the validator (USER runs; you collect verbatim):
   a. the full scripts/preflight_story_3_2.py output (its PASS line + per-check detail);
   b. the RAW AWS reads behind it, so the validator can judge the environment WITHOUT trusting
      the script — run in the stated account:
      # Hub 641628980935:
      aws sts get-caller-identity
      aws iam get-role --role-name pdlv-hub-orchestrator --query "Role.{Trust:AssumeRolePolicyDocument,Boundary:PermissionsBoundary}" --output json
      # (+ the orchestrator's attached-policy documents: list-attached-role-policies then
      #    get-policy-version for each, so its only action = sts:AssumeRole to the member ARNs)
      aws stepfunctions describe-state-machine --state-machine-arn arn:aws:states:us-east-1:641628980935:stateMachine:pdlv-promotion-pipeline --query definition --output text
      # Dev 946509368326:
      aws sts get-caller-identity
      aws iam list-role-tags --role-name pde-member-execution-dev --output json
      aws iam get-role --role-name pde-member-execution-dev --query "Role.AssumeRolePolicyDocument" --output json
      # (+ the member role's attached member-execution-permissions policy document via
      #    list-attached-role-policies then get-policy-version)
4. HAND the raw evidence (3a + 3b) to the BLIND validator per
   story-3.2-gate1-VALIDATOR-HANDOVER.md. The validator authors its own environment-baseline
   DoD and seals GO or NO-GO. You do not pre-frame it.
5. RECORD the sealed Gate-1 result as a dated note on RUNBOOK §VD-9 (verbatim). On GO →
   proceed to Gate 2 (the full end-to-end). On NO-GO → fix the environment (re-run the deploy
   path) and re-capture; do NOT proceed to Gate 2. 3.2 stays 🟡 throughout.

# CURRENT TRUE STATE
- Phase 1 ✅; Phase 2 ✅ (restore/phase-2-green @ 8f85740); 3.1 ✅; 3.2 🟡, VD-9 OPEN, ARMED.
- Branch feature/story-3.2 is offline+CI green, grep-proven correct; two-hop chain
  pdlv-codebuild-service-role → pdlv-hub-orchestrator → pde-member-execution-dev.
- Accounts: Hub 641628980935; Dev 946509368326; Sandbox 586917955591; Prod 466494951534;
  mgmt 467866449172 zero-touch; Forensics 360999005254 is ZTIE's.
- This two-gate split is a PROVISIONAL instance exception for Attempt 8 — it binds nothing in
  the process (no RD, no METHODOLOGY/kit change) unless the stakeholder later chooses to.
```
