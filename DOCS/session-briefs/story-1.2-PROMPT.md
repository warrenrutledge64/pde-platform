# Session Prompt — Story 1.2 (executor-facing)

> Paste the fenced block below as the first message of the Story 1.2 session.
> Source of truth is the brief: [`story-1.2-brief.md`](story-1.2-brief.md).

```
You are the execution agent for the Platform Delivery Engine (PDE) project. Read
this fully before acting.

# PROJECT IDENTITY
PDE is a validation-gated multi-account AWS delivery platform: a serverless CI/CD
factory in the Pipeline-Hub account (co-resident with ZTIE) that promotes artifacts
Dev -> Sandbox -> Prod without ever touching the Org management account. Greenfield,
run on the project-os operating model.

# NON-NEGOTIABLE CONSTRAINTS
- LEAST PRIVILEGE & ZERO-TRUST: no wildcard trust, no wildcard permissions. Scope
  the Spoke role's trust to the exact Hub deployer principal (+ ExternalId/condition)
  and its permissions to exactly the CloudFormation deploy actions PDE needs.
- ROOT-GOVERNANCE-ONLY: nothing in the management account (467866449172) this story.
  Spoke roles live in Dev/Sandbox/Prod.
- SINGLE IaC STANDARD: CloudFormation (YAML) + Python 3 (Boto3) ONLY. No Terraform.
- Production-quality; STATIC SECURITY PASSED (cfn-lint/cfn-guard/Checkov) before deploy.
- VALIDATION-GATED: nothing "done" on inference — the USER validates live; you RECORD.
- RESTORE-POINT DISCIPLINE: build from a known-good point; revert rather than patch.

# OPERATIONAL CONTEXT (state on EVERY command block)
  Spoke roles deploy into the Pipeline-Dev / Pipeline-Sandbox / Pipeline-Prod
  accounts (NOT the management account). The AssumeRole validation runs FROM the
  Pipeline-Hub account INTO each Spoke. Region: us-east-1 (pinned in BOM). Run
  `aws sts get-caller-identity` before each block and confirm the account.
Never present a command without its account banner.

# HARD-WON LESSONS (do NOT repeat)
- Build sandbox is INTEGRATIONS_ONLY: PyPI is BLOCKED (403 proxy) and PyYAML is not
  installed. cfn-lint/cfn-guard/Checkov CANNOT run in the sandbox — offline proof is
  the stdlib invariant checker (see infra/validate_template.py from Story 1.1; extend
  the pattern with trust-scope + least-privilege invariants). The full static bar is
  an operator/CI step. Don't waste time pip-installing in the sandbox.
- Verify the DEPLOYED role (get-role + live assume-role), not just the template.
- #1 live failure is running a block in the WRONG account — get-caller-identity first.
- Give the user the FULL copy-paste sequence per Spoke, with real account ids/region.
- Keep status glyphs OUT of the Ready/Blocked/Tier tables in the RUNBOOK (only the
  phase summary tables + detail-block headers carry glyphs) — else check_docs CHECK S
  false-positives. (Fixed in the checker, but the authoring rule still stands.)

# FIRST — VALIDATION & ADVANCEMENT GATE (do this BEFORE any new work)
# Binding policy: governance/RUNBOOK.md "Validation & Advancement Gate".
# 1. CLOSE OUT STORY 1.1: read RUNBOOK.md + the Validation Debt Register. If VD-1
#    (Story 1.1) is still OPEN / 1.1 is 🟡, obtain the operator's live result for the
#    CloudTrail gate. On PASS: record 1.1's dated Validation Result + flip 🟡 -> ✅,
#    clear VD-1 (its own small commit/PR). On FAIL: fix + re-validate 1.1. Do NOT
#    start 1.2.
# 2. HARD ADVANCEMENT GATE: Story 1.2 depends on 1.1. It may begin ONLY once 1.1 is
#    ✅ and VD-1 is cleared. The register being ARMED blocks new-story work. (No override.)

# WHERE WE ARE
- Current phase/story: Phase 1 / Story 1.2 — cross-account IAM execution roles.
- Prior story + validation state: 1.1 (Org-wide CloudTrail) — was 🟡 built +
  offline-proven at handoff; VD-1 OPEN pending the operator's live CloudTrail pass.
- Last restore point: none yet (Phase 1 tag is cut at Story 1.3).
- True current state: the CloudTrail template exists (infra/cloudtrail-org-baseline.yaml,
  28 invariants pass) but deployment status depends on 1.1's live validation — CONFIRM
  before proceeding.
- Governing docs: governance/PROJECT_PLAN.md, RUNBOOK.md, BOM.md, RESTORE.md, and
  this story's brief: session-briefs/story-1.2-brief.md

# THIS SESSION'S OBJECTIVE
Author + offline-prove CloudFormation for a least-privilege execution role in each
Spoke (Dev/Sandbox/Prod) whose trust policy explicitly trusts the Hub for deploy
operations, then hand the operator the live AssumeRole-into-each-Spoke validation
runbook (the Phase 1 gate's AssumeRole half).

# SCOPE & GUARDRAILS
- In scope: the Spoke execution-role template (trust + scoped permissions); offline
  proof; the per-Spoke deploy + Hub->Spoke assume-role validation runbook.
- Out of scope / do NOT touch: the Hub deployer role / control plane (Phase 2);
  anything in the management account.
- Depends on (must be ✅): Story 1.1.

# DEFINITION OF DONE (this session) — a PASS/FAIL GATE
- Offline: invariant check + cfn-lint/cfn-guard/Checkov clean (operator/CI).
- Live (user): Spoke role deployed in each of Dev/Sandbox/Prod; from the Hub,
  `sts assume-role` into each Spoke role SUCCEEDS and returns that Spoke's account id.
- Goes ✅ ONLY on the recorded live pass. 1.2 does NOT close Phase 1 (1.3 does).
- On FAIL: stay on 1.2, tighten trust/permissions, re-validate.

# ENVIRONMENT
- Push to a feature branch (e.g. feature/story-1.2), never main. Open PRs via
  `gh api repos/warrenrutledge64/pde-platform/pulls` (REST), not `gh pr` subcommands.
  main is PR-only (self-enforced convention on a free private repo).
- Sandbox is offline: author + statically prove here; the USER runs the live deploy +
  assume-role validation from CloudShell.

# WORKING AGREEMENT
- One story to completion. Design -> build -> USER validates live -> you RECORD +
  flip status -> commit. Branch + PR, never push to main.
- Validation drives status; the hard gate governs advancement (see FIRST block).
- At session end, author Story 1.3's brief + prompt — MANDATORY — with a Lessons
  Learned / Carry-Forward section of THIS session's actual lessons. Zero cold-start.
- If blocked, push partial progress + a draft PR; never silently fail.
```
