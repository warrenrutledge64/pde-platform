# Session Brief — Story 2.1: CodeBuild CloudFormation templates (Lint + Deploy)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Story 2.1 OPENS Phase 2 (PDE Control Plane).** It is the first story on the new
> dependency layer (Phase 1 gate), so confirm the whole gate before starting.

## Story 2.1 — CodeBuild CloudFormation templates (Lint + Deploy), ZTIE-safe naming prefixes

| Field | Value |
|-------|-------|
| **Phase** | 2 — PDE Control Plane (The Hub) |
| **Build tier** | 3 (depends on the Phase 1 gate) |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Builds from restore point** | `restore/phase-1-green` (cut at Story 1.2's close) |
| **Session goal** | Author + offline-prove CloudFormation (YAML) for the two PDE CodeBuild projects — a Lint/static-analysis project and a Deployment project — under the ZTIE-safe `pde-` naming + tagging namespace. |

---

### Background & Context

Phase 1 is closed: the orchestrate-and-pull trust fabric (Story 1.1, member
execution roles the Hub directs) is validated ✅, and the Hub CloudShell bootstrap +
committed Phase-1 gate script (Story 1.2) passed its live Option-B proof — so
`restore/phase-1-green` exists. Phase 2 builds the **PDE control plane in
Pipeline-Hub `641628980935`**: a serverless CI/CD engine (Step Functions +
CodeBuild) that performs cross-account CFN deploys. Story 2.1 is the first brick —
the **CodeBuild projects** (lint + deploy) expressed as CloudFormation.

### Objective & Value

- **Objective:** two CloudFormation (YAML) templates (or one parameterised template
  with both projects) defining the PDE **Lint/static-analysis** CodeBuild project
  and the **Deployment** CodeBuild project, each under the `pde-` naming prefix with
  strict `Project=PDE` tagging, offline-proven by a stdlib invariant checker.
- **Why it matters:** these are the build/deploy executors the Phase-2 Step Functions
  state machine (Story 2.2) orchestrates; getting the naming/tagging ZTIE-safe here
  is what keeps PDE strictly additive to the co-resident ZTIE control plane.

### Scope, Dependencies & Position

- **In scope:** the CodeBuild CFN template(s) (Lint + Deploy projects), their
  least-privilege service-role shape, `pde-` naming + `Project=PDE` tags, and an
  offline invariant checker (mirroring `infra/validate_trust_fabric.py`).
- **Out of scope:** the Step Functions state machine (Story 2.2); the actual Hub
  bootstrap deploy (Story 2.3); the member execution roles (Story 1.1, done); the
  org-wide CloudTrail (Story 4.1); anything in the management account.
- **Depends on:** the **Phase 1 gate** (Stories 1.1 ✅ + 1.2 ✅; VD-4 cleared).
- **Unblocks:** Story 2.2 (state machine) and, with it, Story 2.3 (bootstrap).
- **Roadmap position:** opens Phase 2; a tier-2→tier-3 advance AND a Phase 1→Phase 2
  transition — name both at handoff and re-confirm the full new dependency set is ✅.

### Approach & Constraints

- **Approach:** (1) author `infra/codebuild-projects.yaml` (CFN YAML) with the Lint
  and Deploy `AWS::CodeBuild::Project` resources + a tightly-scoped CodeBuild service
  role; (2) enforce the `pde-` name prefix and `Project=PDE` tags on every resource
  (Universal Criterion 5); (3) write `infra/validate_codebuild_projects.py` (stdlib,
  no network) asserting the invariants; (4) hand the USER the deploy + static-bar
  (cfn-lint / cfn-guard / Checkov) commands for the live run.
- **Hard constraints:** CloudFormation (YAML) + Python 3 only — **no Terraform**
  (RD-004); AWS-native + serverless (RD-003); **least privilege / zero-trust** — the
  CodeBuild service role is scoped to exactly the lint/deploy tasks, no wildcards, no
  AdministratorAccess (RD-006, Universal Criterion 3); **ZTIE-safe** `pde-` namespace,
  strictly additive + non-destructive (Universal Criterion 5); zero-touch management
  account (Universal Criterion 1).

### Validation Rationale & Compliance Mapping (optional)

- **Rationale:** establishes the build/deploy execution surface under least privilege
  and in a ZTIE-isolated namespace — the control-plane foundation Phase 2 proves.
- **Audit evidence produced:** the CFN template(s) + the offline invariant report;
  (live) cfn-lint / cfn-guard / Checkov output from the USER's run.

### Change & Rollback

- **Change type:** standard (additive, offline authoring; live deploy is Story 2.3).
- **Restore point this builds from:** `restore/phase-1-green`.
- **Backout plan:** 2.1 produces source only — revert via the normal git revert
  procedure; no live state is changed in 2.1 (the Hub deploy is Story 2.3).

### Definition of Done / Validation Gate

- **Done means:** the CodeBuild CFN template(s) pass the offline invariant checker
  AND the USER returns raw passing STDOUT from the static bar (cfn-lint, and
  cfn-guard / Checkov as available) confirming the Lint + Deploy projects are
  well-formed, `pde-`-prefixed, `Project=PDE`-tagged, and least-privilege (no
  wildcard / AdministratorAccess). _(2.1 is template authoring + static proof; the
  live deploy into the Hub is Story 2.3 — do not deploy in 2.1.)_
- **Validated by:** the USER, live (static bar in CloudShell / CI); the template is
  reviewed for correctness offline.
- **Validation Result:** `pending`.
- **On pass:** record it, flip 2.1 → ✅. _(Does NOT close Phase 2 — 2.2 + 2.3 remain;
  the Phase 2 gate is the dummy-payload Step Functions run in Story 2.3.)_
- **On fail:** stays 🟡; fix and re-run.
- **Advancement gate:** 2.3 cannot begin until 2.1 **and** 2.2 are ✅.

### Risks & Watch-Items

- **ZTIE collision:** the Hub co-hosts the live ZTIE control plane — every PDE
  resource name must carry the `pde-` prefix and `Project=PDE` tag; never reuse a
  bare/unprefixed name that could shadow a ZTIE resource.
- **Least privilege creep:** resist granting the CodeBuild service role broad deploy
  permissions "to be safe." Scope to the lint/deploy tasks on the `pde-` namespace;
  the cross-account deploy power comes from assuming the Story 1.1 member roles, not
  from a broad Hub-side policy.
- **Offline invariant checker hygiene:** the Story 1.1/1.2 checkers strip comments /
  match on structure — keep asserted invariants testing the template, not prose
  (don't let an explanatory `# not AdministratorAccess` comment satisfy a check).
- **No live deploy in 2.1:** the Hub bootstrap deploy is Story 2.3; 2.1 stops at
  authored + statically proven.

### Lessons Learned / Carry-Forward *(authored at the end of Story 1.2 — actual lessons)*

- **What went well:** Option B kept the 1.1/1.2 reasoning coherent — the Phase-1 gate
  script (`scripts/phase1_gate.py`) was authored + offline-proven (24 invariants via
  `scripts/test_phase1_gate.py`) targeting the *real* `pde-hub-orchestrator`, with no
  throwaway Hub principal stood up. The offline proof bar is a FAKE-STS stub (no boto3,
  no network) exercising the happy path, the wrong-account precondition, a denied
  assume, a landed-in-wrong-account mismatch, and the missing-ExternalId usage error —
  so the gate logic is correct-by-construction before Phase 2 ever runs it live.
- **What went wrong / surprised us:** nothing live (1.2 is offline-authored). One
  offline-tooling gotcha: `ruff` is not on PATH in the build sandbox — use
  `~/.pyenv/versions/3.12.13/bin/ruff`. And `ruff` flags `EXE001` on a script with a
  shebang that is not executable — `chmod +x` the scripts (both `scripts/phase1_gate.py`
  and `scripts/test_phase1_gate.py` are `+x`). A least-privilege invariant that greps
  for `iam:` false-positives on role ARNs (`arn:aws:iam::…`) — assert on IAM *action
  verbs*, not the `iam:` substring.
- **Current true state at handoff:** Story 1.1 ✅. Story 1.2 is **🟡 built +
  offline-proven, VD-4 OPEN** (gate ARMED) — pending its live Option-B pass. **Phase 1
  is NOT yet closed and `restore/phase-1-green` does NOT yet exist** until 1.2's live
  pass is recorded. **⚠ Do NOT start Story 2.1 until 1.2 is ✅, VD-4 is cleared, and
  the Phase 1 gate shows ✅.** (Hard advancement gate — no override.)
- **The committed Phase-1 gate script is Phase 2's VD-3b.** The live Hub→member
  `sts:AssumeRole` (`python3 scripts/phase1_gate.py` → prints dev/sandbox/prod account
  ids) runs in Phase 2 once `pde-hub-orchestrator` exists. When Story 2.2/2.3 create
  that Hub role, run the committed script to clear VD-3b — the artifact is ready and
  proven; it just needs the real principal.
- **ExternalId hygiene (hard, from Story 1.1):** never dump a role's trust document
  (`aws iam get-role` leaks the ExternalId) — inspect with a projection. Supply the
  secret via `read -rs` → `PDE_EXTERNAL_ID`, never a literal; rotate on all three
  members if it leaks. The gate script never hardcodes/echoes it.
- **Account topology (authoritative):** Hub `641628980935` (orchestrator / where
  CloudShell + CodeBuild run); members Dev `946509368326`, Sandbox `586917955591`,
  Prod `466494951534`; management/root `467866449172` is zero-touch; Pipeline-Forensics
  `360999005254` is **ZTIE's**, not PDE. Use the derive-from-account pattern for any
  per-account value.
- **Must-know / must-avoid for this session:** Phase 2 is where PDE first deploys into
  the Hub (eventually, in 2.3) — the ZTIE-safe `pde-` prefix + tagging discipline
  (Universal Criterion 5) starts here in 2.1. Keep 2.1 to template + offline proof;
  the live Hub deploy is Story 2.3.
- **User notes:** _(open for the user)_
