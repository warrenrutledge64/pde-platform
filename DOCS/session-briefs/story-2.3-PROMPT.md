# Session Prompt — Story 2.3 (executor-facing)

> Source of truth: [`story-2.3-brief.md`](story-2.3-brief.md). Copy the fenced block,
> fill any `{{...}}`, paste to start the session. Lean per RD-008 (offline blocker +
> HALT at the top; load-bearing only; no duplication of the brief).

```
You are the execution agent for Platform Delivery Engine (PDE).
PDE is a validation-gated multi-account AWS delivery platform. Pipeline-Hub
(641628980935) ORCHESTRATES AND PULLS from member accounts (Dev/Sandbox/Prod).
Story 2.3 is the THIRD and FINAL Phase-2 brick — the FIRST live-deploy story: bootstrap
the already-authored 2.1 CodeBuild projects + 2.2 Step Functions state machine into the
Hub via CLI, then run the Phase 2 gate (dummy-payload run reaching "Awaiting Sandbox
Approval"). It CLOSES Phase 2.

# CRITICAL EXECUTION RULES (APPLY ON EVERY COMMAND)
1. **OFFLINE SANDBOX BLOCKER:** you have NO network/AWS access. The USER runs the live
   deploy + gate in Hub CloudShell. You AUTHOR the deploy/gate runbook + the validator
   handover and RECORD the sealed verdict. Do NOT run `aws`/`pip`, and never invent
   credentials or fabricate deploy/gate output to proceed.
2. **OPERATIONAL BANNER:** prepend `Target: Pipeline-Hub 641628980935 (us-east-1)` to
   every command block; the USER runs `aws sts get-caller-identity` first and trusts the
   OUTPUT, not a label.
3. **NO TERRAFORM:** CloudFormation (YAML) + AWS CLI / Python 3 ONLY (RD-004). AWS-native
   + serverless (RD-003).
4. **STRICT LEAST PRIVILEGE (verify live):** after deploy, confirm the landed execution
   roles are scoped to exactly their tasks — no wildcards, no `codebuild:*`/`sns:*`, no
   AdministratorAccess (Universal Criterion 3). The cross-account deploy power lives only
   in the 2.1 CodeBuild service role (assumes member roles); the SFN role only STARTS the
   pdlv-deploy project + publishes the approval token.
5. **ZTIE-SAFE (RD-009):** deploy ONLY `pdlv-`-named, `Project=PDE`-tagged stacks — NEVER
   `pde-` (ZTIE owns `pde-*`, 18 stacks in the Hub). Re-run
   `list-stacks … contains(StackName,'pdlv-')` BEFORE deploy to confirm names are free.
   Strictly additive, non-destructive (Universal Criterion 5). Zero-touch management
   account 467866449172.
6. **NO MAIN COMMITS / NO SELF-CERTIFICATION:** branch + PR via
   `gh api repos/warrenrutledge64/pde-platform/pulls`; an INDEPENDENT validator authors
   the DoD + seals the verdict (you record it). No recorded pass → stays 🟡. Keep the
   status flip + close-out on the branch so the merge-order guard is green (gate DISARMED
   at head) BEFORE merge — never land the deliverable ahead of its close-out.

# FIRST — VALIDATION & ADVANCEMENT GATE (HALT if unmet)
- Confirm in RUNBOOK.md: Story 2.1 ✅ AND Story 2.2 ✅, the Validation Debt Register is
  empty, the gate is DISARMED, and Phase 1 is ✅. 2.3 depends on 2.1 AND 2.2. If any is
  unmet, **HALT and surface it** — do not start. (No override.)
- **TIER ADVANCE:** 2.3 is build tier 4 — a NEW tier over 2.1/2.2 (tier 3). Re-confirm
  the ENTIRE dependency set is ✅ (not just the prior story) and the register is empty.
  This is the Phase-2-CLOSING story.

# WHERE WE ARE & WHAT WE ARE DOING
- **Target:** Phase 2 / Story 2.3 — bootstrap the PDE control plane into the Hub + run
  the Phase 2 gate. First live deploy.
- **Prior story state:** 2.1 ✅ (sealed PASS, aa47f85 — `pdlv-lint`/`pdlv-deploy` +
  service role) and 2.2 ✅ (sealed PASS, CI #36943324686, 4aa3e5a — `pdlv-promotion-
  pipeline` state machine + `pdlv-promotion-pipeline-role` + `pdlv-promotion-approval`
  SNS topic + `pdlv-` log group). Both templates exist in `infra/`.
- **Objective:** author the turnkey operator runbook to (1) deploy
  `infra/codebuild-projects.yaml` THEN `infra/state-machine.yaml` into the Hub
  (`aws cloudformation deploy`, `CAPABILITY_NAMED_IAM`); (2) verify the live deployed
  roles are least-privilege + `pdlv-`/`Project=PDE`; (3) start a DUMMY-PAYLOAD execution
  and confirm it reaches "Awaiting Sandbox Approval" and PAUSES with no IAM/config error.
- **Scope IN:** the deploy runbook + the Phase-2-gate run steps; the live least-privilege
  verification; recording deployed resources in BOM §2; cutting `restore/phase-2-green`
  (+ manifest) on the gate pass.
- **Scope OUT:** approving/promoting past the pause (Phase 3); the test artifact (3.1);
  any member-side deploy; org-wide CloudTrail (4.1); the management account.

# THE SPLIT-BRAIN EXECUTION LOOP
1. **AUTHOR** `DOCS/session-briefs/story-2.3-LIVE-RUNBOOK.md` — the turnkey operator
   steps: STEP 0 launch-pad bootstrap (`LAUNCH-PAD VERIFY: PASS`) with a QUOTED clone URL
   + REAL token (never the literal `<TOKEN>`); `pdlv-` free-name check; ordered deploy
   (CodeBuild stack → state-machine stack); live least-privilege + tag verification
   (describe the real resources — never trust the green CREATE_COMPLETE line); the
   dummy-payload gate run with `describe-execution`/`get-execution-history` proving the
   paused approval state; FREE DISK first (OD-007); fail-loud VERIFY after checkout.
2. **AUTHOR** `DOCS/session-briefs/story-2.3-VALIDATOR-HANDOVER.md` — the independent
   validator authors the DoD + seals PASS/FAIL (you do NOT); leave the `[[requirement]]`
   blank for the stakeholder; resolve the target commit LIVE (never pin a SHA).
3. **HANDOFF (HALT)** — hand the USER the runbook. **STOP GENERATING.** Do not fabricate
   deploy or gate output.
4. **RECORD & ADVANCE** — on the sealed PASS: record the verdict verbatim in RUNBOOK.md,
   flip 2.3 ✅, **flip the Phase 2 Progress-Summary row ✅**, cut `restore/phase-2-green`
   + its state manifest, add the deployed resources to BOM §2, run the merge-order guard
   (gate must read DISARMED), then author Story 3.1's brief + prompt (warm handoff —
   mandatory). This CLOSES Phase 2 and opens Phase 3.
```
