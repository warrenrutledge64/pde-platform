# Session Brief — Story 1.1: Net-new Org-wide CloudTrail (audit baseline)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> This is the human-facing story spec; it doubles as the change record + audit
> artifact for Story 1.1.

## Story 1.1 — Net-new Org-wide CloudTrail (centralized S3 bucket + KMS key), capturing all `Pipeline-*` accounts

| Field | Value |
|-------|-------|
| **Phase** | 1 — Governance Baseline & Trust Fabric |
| **Build tier** | 1 (foundation — no dependencies) |
| **Date** | 2026-09-30 |
| **Status** | Not Started |
| **Builds from restore point** | none yet (Phase 0 baseline; first live infrastructure story) |
| **Session goal** | Author + offline-prove the CloudFormation for a clean Org-wide CloudTrail (new centralized S3 log bucket + KMS CMK) that captures every `Pipeline-*` account, and hand the operator the live deploy + validation runbook. |

---

### Background & Context

PDE's Phase 0 (governance baseline) is complete: `PROJECT_PLAN.md` + `RUNBOOK.md` +
`RESTORE.md` + `BOM.md` are stood up and pass `check_docs.py`. Story 1.1 is the
**first live-infrastructure story** and the **root of the entire dependency graph**
(build tier 1). Per RD-005, PDE establishes a *completely new* Org-wide CloudTrail
so every cross-account action from Day 1 of the platform is captured under a clean,
untainted audit boundary — nothing else in Phases 1–3 should run until this baseline
is actively recording.

### Objective & Value

- **Objective:** a CloudFormation (YAML) template (plus any Python/Boto3 helpers)
  defining (a) a new centralized S3 log bucket (block-public, versioned, SSE-KMS,
  a least-privilege bucket policy scoped to the CloudTrail service), (b) a dedicated
  KMS customer-managed key with a CloudTrail-scoped key policy, and (c) an
  Organization-wide CloudTrail (`IsOrganizationTrail: true`, multi-region,
  log-file validation enabled) that captures all `Pipeline-*` accounts.
- **Why it matters:** it is the clean audit baseline (RD-005) and the hard
  dependency for Story 1.2 and every later cross-account deployment. Without it,
  nothing downstream may begin (advancement gate).

### Scope, Dependencies & Position

- **In scope:** the CloudTrail + S3 bucket + KMS CMK CloudFormation; offline static
  proof (cfn-lint, cfn-guard, Checkov); the operator's live deploy + gate-validation
  runbook.
- **Out of scope:** the cross-account IAM trust roles (Story 1.2); any control-plane
  or pipeline resources (Phase 2); anything in the management account beyond the
  Org-wide CloudTrail configuration itself.
- **Depends on:** Phase 0 (governance baseline) ✅. No infrastructure dependencies.
- **Unblocks:** Story 1.2 (cross-account trust roles) and, transitively, all of
  Phases 1–3.
- **Roadmap position:** first story of Phase 1; tier 1; opens the live build.

### Approach & Constraints

- **Approach:** (1) author the CloudFormation YAML; (2) run it through cfn-lint /
  cfn-guard / Checkov offline and fix findings; (3) write the exact copy-paste
  deploy sequence + the Phase 1-gate validation checks for the operator.
- **Hard constraints:**
  - **Root-Governance-Only:** the trail is the **sole** permitted management-account
    (467866449172) resource — deploy the Org trail from the management account, and
    put **nothing else** there (Universal Criterion 1).
  - **Single IaC standard:** CloudFormation YAML + Python 3 / Boto3 only — no
    Terraform (RD-004).
  - **Production-quality:** real bucket policy, real KMS key policy, encryption,
    log-file validation on — no placeholders.
  - **Static security passed:** must clear cfn-lint / cfn-guard / Checkov before
    deploy (Universal Criterion 3).

### Validation Rationale & Compliance Mapping (optional)

- **Rationale:** establishes the immutable, encrypted, org-wide audit trail — the
  evidentiary foundation for every later validation and the platform's governance
  posture.
- **Candidate control mappings** *(proposed, pending ratification):*

| Framework | Control ID | Control Name | Rationale | Status |
|-----------|-----------|--------------|-----------|--------|
| NIST SP 800-53 Rev 5 | AU-2 | Event Logging | Org-wide trail captures account activity. | Proposed |
| NIST SP 800-53 Rev 5 | AU-9 | Protection of Audit Information | SSE-KMS + log-file validation + block-public bucket. | Proposed |
| NIST SP 800-53 Rev 5 | SC-28 | Protection of Information at Rest | KMS CMK encryption of log objects. | Proposed |
| NIST CSF | DE.AE-3 | Event data aggregated/correlated | Centralized multi-account log bucket. | Proposed |
| ISO/IEC 27001:2022 | A.8.15 | Logging | Centralized, tamper-evident logging. | Proposed |

- **Audit evidence produced:** the deployed trail's `describe-trails` /
  `get-trail-status` output and the first log objects landing in the new bucket.

### Change & Rollback

- **Change type:** normal (creates the org-wide audit baseline).
- **Restore point this builds from:** Phase 0 baseline (no prior infra tag).
- **Backout plan:** delete the CloudTrail stack (trail + bucket policy + KMS key
  scheduled for deletion) from the management account; because it is a
  single, self-contained stack with no dependents yet, teardown is clean. Document
  the exact delete sequence in the story's runbook.

### Definition of Done / Validation Gate

> A **pass/fail gate**, not a description. The user validates live; the executor
> records the result; only a recorded pass flips the status.

- **Done means:** the CloudFormation deploys cleanly from the management account;
  `aws cloudtrail get-trail-status` shows the trail logging + `IsOrganizationTrail`
  true + multi-region + log-file-validation enabled; and **log files begin landing
  in the new S3 bucket for the `Pipeline-*` accounts** (the Phase 1 gate's
  CloudTrail half). Offline: cfn-lint / cfn-guard / Checkov clean.
- **Validated by:** the human operator, live in the AWS management account.
- **Validation Result:** `pending` — until validated.
- **On pass (and only then):** record the dated Validation Result, flip Story 1.1 →
  ✅ in the runbook. (Story 1.1 does **not** close Phase 1 — Story 1.3 does — so no
  restore tag here.)
- **On fail:** story stays 🟡; the next session re-focuses on fixing +
  re-validating THIS story before Story 1.2.
- **Advancement gate:** Story 1.2 (and all downstream cross-account work) cannot
  start until Story 1.1 is ✅.

### Risks & Watch-Items

- **Zero-touch root discipline:** it is easy to accidentally create incidental
  resources in the management account — deploy *only* the trail stack there and
  verify nothing else was added.
- **KMS key policy correctness:** the CloudTrail service principal must be granted
  `kms:GenerateDataKey*` / `kms:DescribeKey` or trail creation fails; the S3 bucket
  policy must allow `cloudtrail.amazonaws.com` `s3:GetBucketAcl` +
  `s3:PutObject` with the `bucket-owner-full-control` condition.
- **Org-trail prerequisites:** creating an Organization trail requires the
  management account (or a delegated administrator) and that trusted access for
  CloudTrail is enabled in AWS Organizations — check this before deploy.
- **Region pinning:** pin the home region for the trail + bucket and record it in
  `BOM.md` (currently "to be pinned at Story 1.1").
- **Do NOT enable S3 Object Lock in COMPLIANCE mode** on the log bucket (a prior
  lesson: 365-day WORM makes the bucket un-deletable and blocks clean rollback).

### Lessons Learned / Carry-Forward *(authored at the end of Phase 0 / Story 0.1)*

- **What went well:** the `pde-platform` repo already shipped a mature, un-instantiated
  OS-layer scaffold (a superset of `project-os-starter`, with a working
  `check_docs.py` gate). Instantiating it — rather than clobbering it — preserved the
  gate and the independent-validator protocol.
- **What went wrong / surprised us:** `check_docs.py` CHECK S false-positived because
  its summary-table regex matches **any** line beginning `| <story-id> |` and takes
  the **first** status glyph it sees for that id. Auxiliary tables (Blocked / Ready /
  Tiers) that key on a story id and contain a `✅` in prose (e.g. "1.1 not yet ✅")
  poisoned the real status. **Rule for this project:** only the phase summary tables
  and the detail-block headers may carry status glyphs; keep glyphs out of the
  Blocked/Ready/Tier tables (say "not yet validated", not "not yet ✅").
- **Current true state:** Phase 0 governance baseline authored + `check_docs.py`
  PASS + `test_check_docs`/`test_repo_map` 15 tests OK, on branch
  `feature/story-0-bootstrap` (PR open). **Nothing is deployed to AWS yet** — no
  live infrastructure exists. Story 0.1 stays 🟡 until the human confirms the
  runbook faithfully mirrors the plan (Phase 0 gate).
- **Must-know / must-avoid for this session:** PLAN is authoritative — do not invent
  scope. Deploy **only** the trail to the management account. Prove offline before
  asking the operator to deploy. Verify the *deployed* trail (get-trail-status), not
  just that the template lints. Give the operator the full copy-paste sequence with
  the real region + account values substituted.
- **User notes:** _(open for the user)_
