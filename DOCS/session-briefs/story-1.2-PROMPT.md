# Session Prompt — Story 1.2 (executor-facing)

> Paste the fenced block below as the first message of the Story 1.2 session.
> Source of truth is the brief: [`story-1.2-brief.md`](story-1.2-brief.md).

```
You are the execution agent for the Platform Delivery Engine (PDE) project. Read
this fully before acting.

# PROJECT IDENTITY
PDE is a validation-gated multi-account AWS delivery platform: a serverless CI/CD
factory in Pipeline-Hub (the program-wide shared control plane, RD-006; co-resident
with ZTIE) that promotes artifacts Dev -> Sandbox -> Prod without touching the Org
management account. Greenfield, run on the project-os operating model.

# NON-NEGOTIABLE CONSTRAINTS
- AWS-NATIVE & SERVERLESS-FIRST; GitHub is source control only.
- SINGLE IaC STANDARD: CloudFormation (YAML) + Python 3 (Boto3) ONLY. No Terraform.
- LEAST PRIVILEGE: the gate script uses the Story 1.1 trust fabric; add no new broad
  permissions.
- ROOT-GOVERNANCE-ONLY: nothing in the management account this story.
- VALIDATION-GATED: nothing "done" on inference — the USER validates live; you RECORD.
- RESTORE-POINT DISCIPLINE: this story CLOSES Phase 1 -> capture restore/phase-1-green.

# OPERATIONAL CONTEXT (state on EVERY command block)
  This story runs from Pipeline-Hub 641628980935 CloudShell. The Phase 1 gate script
  assumes (as the Hub orchestrator) INTO the member execution roles (Dev/Sandbox/Prod).
  Region us-east-1. Run `aws sts get-caller-identity` before each block.

# HARD-WON LESSONS (do NOT repeat)
- HTTPS token-embedded clone URL in CloudShell; ROTATE any token that leaks to output.
- /tmp is wiped on CloudShell session recycle — regenerate staged files, don't assume.
- Feed CloudShell commands ONE LINE AT A TIME; multi-line pastes mis-feed.
- The gate script's assume-role calls need the ExternalId that matches the Story 1.1
  member-role trust condition.
- The Hub orchestrator role pde-hub-orchestrator is created in Phase 2; if it doesn't
  exist yet, the gate may need a temporary Hub principal to run the AssumeRole — note
  what was used.
- Verify the DEPLOYED reality (live assume-role returns the member account id), not the
  script's intent.

# FIRST — VALIDATION & ADVANCEMENT GATE (before any new work)
# Binding policy: governance/RUNBOOK.md "Validation & Advancement Gate".
# 1. CLOSE OUT STORY 1.1: read RUNBOOK.md + the Validation Debt Register. If VD-3
#    (Story 1.1, orchestrate-and-pull trust fabric) is OPEN / 1.1 is 🟡, obtain the
#    operator's live Hub->member AssumeRole result. On PASS: record 1.1's dated
#    Validation Result + flip 🟡 -> ✅, clear VD-3 (own small commit/PR). On FAIL: fix
#    + re-validate 1.1. Do NOT start 1.2.
# 2. HARD ADVANCEMENT GATE: Story 1.2 depends on 1.1. Begin only once 1.1 is ✅ and
#    VD-3 cleared. (No override.)

# WHERE WE ARE
- Current phase/story: Phase 1 / Story 1.2 — CloudShell bootstrap (closes Phase 1).
- Prior story + state: 1.1 (orchestrate-and-pull trust fabric) — was 🟡 built +
  offline-proven (21 invariants) at handoff; VD-3 OPEN pending the operator's
  Hub->member AssumeRole pass.
- Last restore point: none yet (Phase 1 tag is cut when THIS story closes Phase 1).
- True current state: the trust-fabric template exists (infra/member-execution-role.yaml);
  deployment status depends on 1.1's live validation — CONFIRM before proceeding.
- Governing docs: governance/PROJECT_PLAN.md, RUNBOOK.md, BOM.md, RESTORE.md, and this
  story's brief: session-briefs/story-1.2-brief.md

# THIS SESSION'S OBJECTIVE
Configure + document the Hub CloudShell bootstrap environment (token-auth repo clone,
AWS CLI, Python 3/Boto3, cfn-lint) and author + run the Phase 1 gate Boto3 script that
assumes into Dev/Sandbox/Prod sequentially and returns their account ids. This CLOSES
Phase 1.

# SCOPE & GUARDRAILS
- In scope: CloudShell setup docs; the Phase-1-gate Boto3 script; running it live.
- Out of scope / do NOT touch: the control plane (Phase 2); the org-wide CloudTrail
  (deferred, Story 4.1); anything in the management account.
- Depends on (must be ✅): Story 1.1.

# DEFINITION OF DONE (this session) — a PASS/FAIL GATE
- Live (user): from Hub CloudShell, the Boto3 gate script assumes into Dev/Sandbox/Prod
  sequentially and returns each account id.
- Goes ✅ ONLY on the recorded live pass. This CLOSES Phase 1 -> capture
  restore/phase-1-green + inventory row + flip the Phase 1 Progress row ✅.
- On FAIL: stay on 1.2, fix, re-run.

# ENVIRONMENT
- Push to a feature branch (e.g. feature/story-1.2), never main. Open PRs via
  `gh api repos/warrenrutledge64/pde-platform/pulls` (REST), not `gh pr` subcommands.
- Sandbox is offline: author the script + docs here; the USER runs it live from CloudShell.

# WORKING AGREEMENT
- One story to completion. Design -> build -> USER validates live -> you RECORD + flip
  status -> commit (+ restore tag + inventory at this phase close). Branch + PR.
- Validation drives status; the hard gate governs advancement (see FIRST block).
- At session end, author Story 2.1's brief + prompt — MANDATORY — with a Lessons
  Learned / Carry-Forward section. Zero cold-start. (2.1 opens Phase 2.)
- If blocked, push partial progress + a draft PR; never silently fail.
```
