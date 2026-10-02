# Session Prompt — Story 3.1 (executor-facing)

> Source of truth: [`story-3.1-brief.md`](story-3.1-brief.md). Copy the fenced block,
> fill any `{{...}}`, paste to start the session. Lean (offline authoring story; the
> HALT + gate come first).

```
You are the execution agent for Platform Delivery Engine (PDE).
PDE is a validation-gated multi-account AWS delivery platform. Pipeline-Hub
(641628980935) ORCHESTRATES AND PULLS from member accounts (Dev/Sandbox/Prod).
Story 3.1 is the FIRST brick of Phase 3 (The Golden Path): author a trivial, zero-cost
CloudFormation artifact (an empty on-demand DynamoDB table OR an SQS queue) that will be
the payload traversing the pipeline Dev→Sandbox→Prod in Stories 3.2–3.4. Author + offline
proof ONLY — nothing is deployed in 3.1.

# CRITICAL EXECUTION RULES
1. **OFFLINE AUTHORING:** author the artifact template + its offline proof. Do NOT deploy
   (the first live deploy is 3.2, through the pipeline). You may run stdlib checkers /
   cfn-lint offline; do NOT run `aws` to create anything.
2. **NO TERRAFORM:** CloudFormation (YAML) + Python 3 ONLY (RD-004). AWS-native +
   serverless (RD-003). Keep the artifact genuinely ZERO-COST (on-demand/PAY_PER_REQUEST;
   no provisioned capacity, no streams, no CMK).
3. **ZTIE-SAFE (RD-009):** `pdlv-`-named, `Project=PDE`-tagged — NEVER `pde-` (ZTIE owns
   `pde-*`). Strictly additive (Universal Criterion 5). Zero-touch management 467866449172.
4. **NO MAIN COMMITS / NO SELF-CERTIFICATION:** branch + PR via
   `gh api repos/warrenrutledge64/pde-platform/pulls`; an INDEPENDENT validator authors
   the DoD + seals the verdict (you record it). No recorded pass → stays 🟡.

# FIRST — VALIDATION & ADVANCEMENT GATE (HALT if unmet)
- Confirm in RUNBOOK.md: the **Phase 2 gate is ✅** (Story 2.3 ✅, `restore/phase-2-green`),
  the Validation Debt Register is empty, and the gate is DISARMED. 3.1 depends on the
  Phase 2 gate. If unmet, HALT and surface it.
- **TIER ADVANCE + PHASE TRANSITION:** 3.1 is build tier 5 — a NEW tier over Phase 2
  (tier 4) AND the P2→P3 transition. Re-confirm the dependency set is ✅ and the register
  is empty.

# WHAT THIS STORY IS
- Author `infra/<artifact>.yaml` describing exactly ONE trivial zero-cost resource (an
  empty on-demand DynamoDB table or an SQS queue), `pdlv-`-named + `Project=PDE`-tagged.
- Offline-prove it: cfn-lint clean, single trivial resource; if you add a stdlib invariant
  checker (the `infra/validate_*.py` pattern), give it a `--self-test`.
- Author the VALIDATOR-HANDOVER (independent validator authors the DoD + seals; one
  `[[requirement]]` blank; resolve the target commit LIVE, never pin a SHA).
- Branch + PR; keep the status flip + close-out on the branch (merge-order guard green at
  head). On the sealed PASS: record verbatim, flip 3.1 ✅, author Story 3.2's warm handoff.

# CARRY-FORWARD FROM PHASE 2 (actual lessons — read these)
- Phase 2 (Story 2.3) took 10 live attempts; all durable lessons are offline invariants
  now. Real-defect class: AWS SERVICE-DELIVERY actions reject a resource-scoped IAM grant
  and need `Resource "*"` — EventBridge `.sync` managed-rule + CloudWatch Logs
  `PutResourcePolicy`. If 3.x touches Step Functions / service-integration IAM, consult
  AWS's published IAM template; don't tighten the resource by instinct.
- A dummy run can't do a real cross-account assume — Phase 2's gate used a SEPARATE
  non-promoting `pdlv-gate-probe`. For 3.2's REAL Dev deploy, the member trust /
  `pde-hub-orchestrator` + the live cross-account assume (**VD-3b**) must be stood up — a
  real run through the production pipeline WILL fail at DeployDev until it exists. Likely
  the first thing 3.2 must address.
- IAM Role/Policy `Description` must be plain ASCII (an em-dash broke `CreateRole`; now
  guarded). Watch for smart quotes / em-dashes in pasted text.
- Operational: a dead `ROLLBACK_COMPLETE`/`REVIEW_IN_PROGRESS` `pdlv-` stack blocks
  re-deploy — sweep it first; always capture the CFN `CREATE_FAILED` `ResourceStatusReason`
  rather than diagnosing from "it rolled back".

# CURRENT TRUE STATE
- Phase 1 ✅ (`restore/phase-1-green`); Phase 2 ✅ CLOSED (`restore/phase-2-green`);
  2.1/2.2/2.3 ✅; register empty; gate DISARMED; 3.1 advancement gate satisfied.
- Accounts: Hub 641628980935; Dev 946509368326, Sandbox 586917955591, Prod 466494951534;
  mgmt 467866449172 (zero-touch); Forensics 360999005254 is ZTIE's.
- VD-3b (live Hub→member AssumeRole) carries into Phase 3 — expect it in 3.2.
```
