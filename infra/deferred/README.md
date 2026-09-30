# Deferred — Org-wide Audit Governance (RD-007)

> **Do NOT deploy anything in this directory during Phases 1–3.**
>
> These artifacts are **deferred, not abandoned.** They are kept here for
> **historical reference** and as the starting point for the scheduled governance
> cutover (**Story 4.1**, Phase 4).

## Why this is here

The project originally opened with an Organization-wide CloudTrail audit baseline
as Story 1.1 (RD-005). Two ratified decisions changed that:

- **RD-006** — `Pipeline-Hub` (`641628980935`) is the program-wide **shared control
  plane**. When org-wide audit is enabled, its administration is **delegated to the
  Hub** (not run from the Organization root), under a dedicated least-privilege
  governance role kept separate from any tenant deploy role.
- **RD-007** — the org-wide audit baseline is **deferred in full** (no interim
  baseline) to a scheduled governance story, so the PDE delivery engine is proven
  first. The absence of a PDE-provided org-wide audit trail during design/build is
  an **accepted, declared debt** (see the RUNBOOK Operational Debt Register, OD-002).

## What's here

| File | Status | Notes |
|------|--------|-------|
| `cloudtrail-org-baseline.yaml` | **deferred** | The as-built org-trail template from the original Story 1.1 — **root-hosted** model. At Story 4.1 it is adapted from root-hosted to **Hub-delegated** (RD-006) before deployment. 28-invariant offline proof passed at authoring time. |
| `validate_cloudtrail_template.py` | **deferred** | Stdlib offline invariant checker for the template above. Still runnable in place: `python3 infra/deferred/validate_cloudtrail_template.py`. |

## When this gets picked up

**Story 4.1 (Phase 4 — Governance Cutover):** enable CloudTrail delegated
administration to the Hub (`register-delegated-administrator` from the Org root —
root's sole, one-time governance action), adapt this template to the Hub-delegated
model, deploy the org-wide trail as a shared control-plane service, and retire the
RD-007 audit debt.
