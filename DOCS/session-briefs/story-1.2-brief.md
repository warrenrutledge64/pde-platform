# Session Brief — Story 1.2: Cross-account IAM execution roles (Hub → Spokes)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> Human-facing story spec + change record for Story 1.2.

## Story 1.2 — Cross-account IAM execution roles in Dev/Sandbox/Prod trusting the Hub

| Field | Value |
|-------|-------|
| **Phase** | 1 — Governance Baseline & Trust Fabric |
| **Build tier** | 2 (depends on 1.1) |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Builds from restore point** | Phase 0 baseline (no infra tag yet; Phase 1 tag is cut at Story 1.3) |
| **Session goal** | Author + offline-prove CloudFormation for a least-privilege execution role in each Spoke (Dev/Sandbox/Prod) whose trust policy explicitly trusts the Hub for deployment operations, and hand the operator the live AssumeRole validation runbook. |

---

### Background & Context

Phase 1's clean audit baseline (Story 1.1, the Org-wide CloudTrail) is validated ✅.
Story 1.2 lays the **trust fabric**: the reusable cross-account substrate the Hub
control plane (Phase 2) will assume to deploy CloudFormation into each Spoke. This
is build tier 2 — it opens the dependency layer that all of Phases 2–3 stand on.

### Objective & Value

- **Objective:** a CloudFormation (YAML) template (deployed once per Spoke, or via
  StackSets across the three) defining an IAM execution role whose **trust policy**
  names the Hub account as principal (least-privilege, ideally with an
  `sts:ExternalId` and/or a condition on the Hub deployer role), and whose
  **permissions** are scoped to exactly the CloudFormation deploy actions the PDE
  needs — not `*`.
- **Why it matters:** without explicit Spoke→Hub trust, the Hub cannot orchestrate
  any deployment. It is the hard dependency for the Phase 1 gate's AssumeRole half
  and for the entire control plane.

### Scope, Dependencies & Position

- **In scope:** the Spoke execution-role template (trust + least-privilege
  permissions), offline proof, and the operator's live `AssumeRole`-into-each-Spoke
  validation runbook (the Phase 1 gate's second half).
- **Out of scope:** the Hub-side deployer role/control plane (Phase 2); anything in
  the management account.
- **Depends on:** Story 1.1 ✅ (VD-1 cleared).
- **Unblocks:** Story 1.3 (CloudShell bootstrap access) and the Phase 1 gate; then
  all of Phase 2.
- **Roadmap position:** tier 2; the trust-fabric layer of Phase 1.

### Approach & Constraints

- **Approach:** (1) author the Spoke role CloudFormation (trust policy → Hub
  principal + external-id/condition; permissions scoped to CFN deploy); (2) offline
  proof (`validate_template.py`-style invariant check + cfn-lint/cfn-guard/Checkov
  operator-side); (3) write the copy-paste deploy (per Spoke) + `AssumeRole`
  validation runbook.
- **Hard constraints:**
  - **Least Privilege & Zero-Trust:** no wildcard trust, no wildcard permissions;
    scope to the exact Hub deployer principal + exact deploy actions.
  - **Single IaC standard:** CloudFormation YAML + Python 3 / Boto3 only.
  - **Static security passed** before deploy (Universal Criterion 3).
  - Spoke roles live in the **Spoke** accounts (Dev/Sandbox/Prod) — **not** the
    management account.

### Definition of Done / Validation Gate

- **Done means:** the Spoke role template deploys into each of Dev/Sandbox/Prod; and
  from the Hub, an `sts assume-role` into each Spoke role **succeeds and returns that
  Spoke's account id** (the Phase 1 gate's AssumeRole half). Offline: invariant
  check + cfn-lint/cfn-guard/Checkov clean.
- **Validated by:** the human operator, live (Hub → each Spoke).
- **Validation Result:** `pending`.
- **On pass:** record it, flip 1.2 → ✅, clear its VD entry. (1.2 does **not** close
  Phase 1 — Story 1.3 does.)
- **On fail:** stays 🟡; re-focus on fixing the trust/permission scoping.
- **Advancement gate:** 1.3 + the Phase 1 gate cannot complete until 1.2 is ✅.

### Risks & Watch-Items

- **Trust-policy scoping:** trusting the whole Hub account root is broad; prefer
  trusting the specific Hub deployer role ARN and requiring an `ExternalId` to
  prevent the confused-deputy problem.
- **Chicken-and-egg with the Hub deployer:** the Spoke trust may reference a Hub
  role that doesn't exist until Phase 2. Decide whether to trust the Hub account
  root initially (then tighten in Phase 2) or stage the Hub deployer role first —
  record the decision as an RD if it shapes the architecture.
- **StackSets vs per-account deploy:** deploying the same role to three accounts is
  a natural StackSet; if used, that's an org-level action from the management
  account (a governance action, acceptable) — keep the *role* in the Spokes.
- **Verify the DEPLOYED role**, not the template: after deploy, `get-role` +
  `assume-role` live, don't infer from the YAML.

### Lessons Learned / Carry-Forward *(authored at the end of Story 1.1)*

- **What went well:** the CloudTrail template was authored production-quality first
  time and cleared a 28-invariant offline check. The `infra/validate_template.py`
  pattern (stdlib, no PyYAML, asserts security invariants against the raw template)
  is a reusable offline proof bar — **carry it forward for 1.2** (add the trust-scope
  + least-privilege invariants).
- **What went wrong / surprised us:** the build sandbox is `INTEGRATIONS_ONLY` —
  **PyPI is blocked (403 proxy)** and PyYAML isn't installed, so cfn-lint / cfn-guard
  / Checkov / a YAML parser **cannot run here**. Offline proof is the stdlib invariant
  checker; the full static bar is an operator/CI step. Don't burn time trying to pip
  install in the sandbox.
- **Current true state:** Story 1.1 is 🟡 (built + offline-proven, **not yet
  live-deployed**). The Org trail, S3 bucket, and KMS key exist only as a template —
  **nothing is deployed to AWS.** VD-1 is OPEN; the advancement gate is ARMED — so
  **1.2 may NOT begin until 1.1 is validated live and VD-1 clears.** Confirm 1.1 ✅
  before starting 1.2 (that is the hard gate, not a formality).
- **Must-know / must-avoid:** deploy Spoke roles to the **Spokes**, never the
  management account. State the account banner on every command block and run
  `aws sts get-caller-identity` first — the recurring #1 failure is running a block
  in the wrong account. Give the operator the full copy-paste sequence per Spoke.
- **User notes:** _(open for the user)_
