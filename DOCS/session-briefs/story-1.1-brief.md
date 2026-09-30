# Session Brief — Story 1.1 (orchestrate-and-pull): Trust fabric — member execution roles the Hub invokes

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Re-scoped twice (2026-09-30):** from the org-wide CloudTrail (→ Story 4.1,
> RD-007) to a trust fabric, then from the initial *Hub-pushes* shape to the RD-006
> **orchestrate-and-pull** direction (Hub directs; member executes locally).

## Story 1.1 — Orchestrate-and-pull trust fabric: member execution roles the Hub invokes (RD-006 amended)

| Field | Value |
|-------|-------|
| **Phase** | 1 — Trust Fabric |
| **Build tier** | 1 (foundation — no dependencies) |
| **Date** | 2026-09-30 |
| **Status** | In Progress (🟡 — built + offline-proven, awaiting live validation, VD-3) |
| **Builds from restore point** | Phase 0 baseline (first live-infrastructure story) |
| **Session goal** | Author + offline-prove CloudFormation for a least-privilege member execution role that a *specific Hub orchestrator role* can assume/direct, and hand the operator the Hub→member AssumeRole validation runbook. |

---

### Background & Context

Per the amended **RD-006**, `Pipeline-Hub` (`641628980935`) is the program-wide
shared control plane that **orchestrates and pulls**: it *directs* functions that
live in the member accounts, the *action executes locally in the member*, results
flow back via a contract-gated intake, and a human accept/reject on the Hub
dashboard is enforced via a Hub-signed decision token. **RD-007** defers the
org-wide audit baseline to Phase 4 (Story 4.1). So Story 1.1 is the tier-1 **trust
fabric** for that model — a member execution role the Hub can invoke — the root of
the dependency graph.

### Objective & Value

- **Objective:** a CloudFormation (YAML) template (deployed once per member)
  defining a least-privilege **member execution role** whose trust policy names a
  **specific Hub orchestrator role** (never the Hub account root) and requires an
  `sts:ExternalId`; permissions scoped to the CloudFormation actions the member's
  **local** execution needs on the `pde-` stack namespace.
- **Why it matters:** without this, the Hub cannot direct any member function. It is
  the hard dependency for the Phase 1 gate and all of Phases 2–3.

### Scope, Dependencies & Position

- **In scope:** the member execution-role template (trust direction + scoped local
  permissions), offline proof, the Hub→member AssumeRole validation runbook.
- **Out of scope (tight tier-1 scope):** the orchestration engine (Step Functions),
  the member→Hub results intake data-contract, and the Hub-signed decision-token
  machinery — all **Phase 2**. Also out: the org-wide CloudTrail (Story 4.1); the
  management account.
- **Depends on:** Phase 0 ✅. No infrastructure dependencies.
- **Unblocks:** Story 1.2 (CloudShell bootstrap) + the Phase 1 gate; then Phase 2.
- **Roadmap position:** first story of Phase 1; tier 1.

### Approach & Constraints

- **Approach:** (1) author the member execution-role CloudFormation;
  (2) offline invariant proof (`infra/validate_trust_fabric.py`) + cfn-lint/cfn-guard/
  Checkov operator-side; (3) write the per-member deploy + Hub→member AssumeRole
  validation runbook.
- **Hard constraints:**
  - **RD-006 orchestrate-and-pull direction:** the Hub *directs*; the member
    *executes locally*. Trust a specific Hub **orchestrator** role ARN (not root) +
    require an ExternalId; the Hub is not a general write-target.
  - **Least Privilege:** permissions scoped to local CFN deploy on `pde-*`, no
    wildcard, no AdministratorAccess.
  - **Single IaC standard:** CloudFormation YAML + Python 3 / Boto3 only.
  - Roles live in the **members** — never the management account.

### Definition of Done / Validation Gate

- **Done means:** the member role template deploys into each of Dev/Sandbox/Prod;
  from the Hub (orchestrator principal), `sts:AssumeRole` into each member role
  succeeds (with the correct ExternalId), returns that member's account id, and is
  denied without the ExternalId. Offline: 21-invariant check + cfn-lint/cfn-guard/
  Checkov clean.
- **Validated by:** the human operator, live (Hub → each member).
- **Validation Result:** `pending` (VD-3 open).
- **On pass:** record it, flip 1.1 → ✅, clear VD-3. (1.1 does **not** close Phase 1
  — Story 1.2 does.)
- **On fail:** stays 🟡; re-focus on tightening trust/permission scoping.
- **Advancement gate:** 1.2 + the Phase 1 gate cannot complete until 1.1 is ✅.

### Risks & Watch-Items

- **Chicken-and-egg with the Hub orchestrator role:** the trust names
  `pde-hub-orchestrator`, created in Phase 2. IAM allows naming a not-yet-existent
  principal; the trust resolves at assume-time. Validate the trust *shape* now; run
  the full live AssumeRole once the Hub role exists (or with a temporary stand-in).
- **Trust scoping:** must be the specific Hub orchestrator role ARN + ExternalId —
  never `:root`.
- **Verify the DEPLOYED role** (`get-role` + live `assume-role`), not just the YAML.
- **Direction:** deploy in the members; initiate AssumeRole from the Hub.

### Lessons Learned / Carry-Forward *(authored during Story 1.1 / the re-scopes)*

- **The `infra/validate_*.py` stdlib invariant pattern** is the offline proof bar
  (PyPI blocked in the sandbox → cfn-lint/cfn-guard/Checkov are operator/CI). It must
  **strip YAML comments** before asserting, or explanatory prose (`NOT
  AdministratorAccess`, `not :root`) false-fails the check.
- **Two re-scopes at tier 1, cheaply:** because Story 1.1 was still 🟡 (nothing
  deployed), correcting first the *what* (CloudTrail → trust fabric, RD-007) and then
  the *direction* (Hub-pushes → orchestrate-and-pull, RD-006 amendment) cost only
  template rewrites + re-proofs. The retired push-model template is preserved in
  `infra/deferred/` — remediate-forward, never delete history.
- **Current true state:** Story 1.1 is 🟡 — built + offline-proven (21 invariants),
  **not deployed.** VD-3 OPEN, gate ARMED. Nothing on AWS yet.
- **User notes:** _(open for the user)_
