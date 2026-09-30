# Session Brief — Story 1.1 (re-scoped): Cross-account trust fabric (Hub → Spokes)

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Re-scoped 2026-09-30:** Story 1.1 was changed from the org-wide CloudTrail
> (deferred to Story 4.1 per RD-007) to the cross-account trust fabric (RD-006).

## Story 1.1 — Cross-account trust fabric: Spoke execution roles trusting specific Hub roles (RD-006)

| Field | Value |
|-------|-------|
| **Phase** | 1 — Trust Fabric |
| **Build tier** | 1 (foundation — no dependencies) |
| **Date** | 2026-09-30 |
| **Status** | In Progress (🟡 — built + offline-proven, awaiting live validation) |
| **Builds from restore point** | Phase 0 baseline (first live-infrastructure story) |
| **Session goal** | Author + offline-prove the CloudFormation for a least-privilege Spoke execution role that trusts a specific Hub deployer role, and hand the operator the Hub→Spoke AssumeRole validation runbook. |

---

### Background & Context

Two ratified decisions reshaped Phase 1: **RD-006** (Pipeline-Hub `641628980935` is
the program-wide shared control plane; Spokes trust *specific Hub roles*) and
**RD-007** (the org-wide audit baseline is deferred in full to Phase 4 / Story 4.1 —
no interim, tracked as declared debt OD-002). So Story 1.1 is now the **trust
fabric** — the reusable substrate the Hub control plane assumes to deploy into every
Spoke. It is build tier 1, the root of the dependency graph.

### Objective & Value

- **Objective:** a CloudFormation (YAML) template (deployed once per Spoke) defining
  a least-privilege PDE execution role whose **trust policy names a specific
  `Pipeline-Hub` deployer role** (never the Hub account root) and requires an
  `sts:ExternalId`, with permissions scoped to exactly the CloudFormation deploy
  actions on the `pde-` stack namespace.
- **Why it matters:** without explicit Spoke→Hub trust, the Hub cannot orchestrate
  any deployment. It is the hard dependency for the Phase 1 gate and all of Phase 2–3.

### Scope, Dependencies & Position

- **In scope:** the Spoke execution-role template (trust + scoped permissions),
  offline proof, the Hub→Spoke AssumeRole validation runbook.
- **Out of scope:** the Hub-side deployer role / control plane (Phase 2); the
  org-wide CloudTrail (deferred, Story 4.1); anything in the management account.
- **Depends on:** Phase 0 ✅. No infrastructure dependencies.
- **Unblocks:** Story 1.2 (CloudShell bootstrap) + the Phase 1 gate; then all of Phase 2.
- **Roadmap position:** first story of Phase 1; tier 1; the trust-fabric foundation.

### Approach & Constraints

- **Approach:** (1) author the Spoke role CloudFormation; (2) offline invariant proof
  (`infra/validate_trust_fabric.py`) + cfn-lint/cfn-guard/Checkov operator-side;
  (3) write the per-Spoke deploy + Hub→Spoke AssumeRole validation runbook.
- **Hard constraints:**
  - **Least Privilege & Zero-Trust (RD-006):** trust a specific Hub role ARN (not
    root) + require an ExternalId; permissions scoped to CFN deploy on `pde-*`, no
    wildcard, no AdministratorAccess.
  - **Single IaC standard:** CloudFormation YAML + Python 3 / Boto3 only.
  - **Static security passed** before deploy (Universal Criterion 3).
  - Roles live in the **Spokes** — never the management account.

### Definition of Done / Validation Gate

- **Done means:** the Spoke role template deploys into each of Dev/Sandbox/Prod; from
  the Hub, `sts:AssumeRole` into each Spoke role succeeds (with the correct
  ExternalId) and returns that Spoke's account id, and is denied without the
  ExternalId. Offline: 19-invariant check + cfn-lint/cfn-guard/Checkov clean.
- **Validated by:** the human operator, live (Hub → each Spoke).
- **Validation Result:** `pending` (VD-2 open).
- **On pass:** record it, flip 1.1 → ✅, clear VD-2. (1.1 does **not** close Phase 1 —
  Story 1.2 does.)
- **On fail:** stays 🟡; re-focus on tightening trust/permission scoping.
- **Advancement gate:** 1.2 + the Phase 1 gate cannot complete until 1.1 is ✅.

### Risks & Watch-Items

- **Chicken-and-egg with the Hub deployer role:** the trust names `pde-hub-deployer`,
  which is created in Phase 2. IAM allows naming a not-yet-existent principal; the
  trust resolves at assume-time. Validate the trust *shape* now; run the full live
  AssumeRole once the Hub role exists (or with a temporary Hub stand-in).
- **Trust scoping:** must be the specific Hub role ARN + ExternalId — never `:root`.
- **Verify the DEPLOYED role** (`get-role` + live `assume-role`), not just the YAML.
- **Wrong account:** deploy in the Spokes, initiate AssumeRole from the Hub.

### Lessons Learned / Carry-Forward *(authored during Story 1.1 / the re-scope)*

- **What went well:** the `infra/validate_*.py` stdlib invariant pattern is a solid
  offline proof bar (PyPI is blocked in the sandbox, so cfn-lint/cfn-guard/Checkov
  are operator/CI). Carry it forward per template.
- **Checker gotcha (fixed):** the invariant validator initially false-failed on
  explanatory comments (`NOT AdministratorAccess`, `not :root`) — strip YAML comment
  lines before asserting invariants so the check tests the *template*, not the prose.
- **The re-scope itself:** the org path added design difficulty; the resolution was
  to fix the load-bearing charter now (RD-006, Hub = shared control plane) and defer
  only the additive audit layer (RD-007), with the org-trail work preserved in
  `infra/deferred/` for Story 4.1. Declared debt OD-002 tracks the deferral.
- **Current true state:** Story 1.1 (trust fabric) is 🟡 — built + offline-proven
  (19 invariants), **not deployed.** VD-2 OPEN, gate ARMED. Nothing on AWS yet.
- **User notes:** _(open for the user)_
