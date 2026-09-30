# Session Brief — Story 1.2 (re-scoped): CloudShell bootstrap environment

> One brief per story, populated from [`RUNBOOK.md`](../../governance/RUNBOOK.md).
> **Re-scoped 2026-09-30:** after the Phase-1 re-scope, Story 1.2 is the CloudShell
> bootstrap (formerly Story 1.3); the trust roles moved to Story 1.1.

## Story 1.2 — Configure CloudShell environment with repo access for the bootstrap deploy

| Field | Value |
|-------|-------|
| **Phase** | 1 — Trust Fabric |
| **Build tier** | 2 (depends on 1.1) |
| **Date** | _(fill at session start)_ |
| **Status** | Not Started |
| **Builds from restore point** | Phase 0 baseline (Phase 1 tag is cut at this story's close) |
| **Session goal** | Configure + document the Hub CloudShell bootstrap environment and run the Phase 1 gate Boto3 script (AssumeRole into Dev/Sandbox/Prod), closing Phase 1. |

---

### Background & Context

Story 1.1 (the trust fabric) is validated ✅ — the Spoke execution roles exist and
are assumable from the Hub. Story 1.2 stands up the operator's **bootstrap
environment**: the Hub-account CloudShell with repo access and tooling, and runs the
**Phase 1 gate** end to end (the AssumeRole-into-each-Spoke Boto3 script). This story
**closes Phase 1**.

### Objective & Value

- **Objective:** a documented, reproducible Hub CloudShell setup (token-auth repo
  clone, AWS CLI, Python 3 / Boto3, cfn-lint) **and** a committed Phase-1-gate Boto3
  script that assumes into Dev/Sandbox/Prod sequentially and returns their account ids.
- **Why it matters:** it's the operator's launch pad for the Phase 2 bootstrap deploy,
  and running the gate script proves the trust fabric works end to end from the real
  bootstrap context.

### Scope, Dependencies & Position

- **In scope:** CloudShell setup docs, the Phase-1-gate Boto3 script, running it live.
- **Out of scope:** the control plane (Phase 2); the org-wide CloudTrail (Story 4.1).
- **Depends on:** Story 1.1 ✅ (trust fabric assumable).
- **Unblocks:** Phase 2.
- **Roadmap position:** closes Phase 1 → capture `restore/phase-1-green`.

### Approach & Constraints

- **Approach:** (1) document the Hub CloudShell bootstrap (token-auth clone per the
  HTTPS-token convention, tooling); (2) author a Boto3 gate script that loops
  Dev/Sandbox/Prod, assumes each Spoke role with the ExternalId, prints the returned
  account id; (3) run it live from Hub CloudShell.
- **Hard constraints:** AWS-native tooling; the gate script is Python 3 / Boto3;
  least-privilege (uses the trust fabric, adds no new broad permissions).

### Definition of Done / Validation Gate

- **Done means:** from Hub CloudShell, the Boto3 gate script assumes into
  Dev/Sandbox/Prod sequentially and returns each account id — the Phase 1 gate. Story
  1.2 closes Phase 1.
- **Validated by:** the human operator, live from Hub CloudShell.
- **Validation Result:** `pending`.
- **On pass:** record it, flip 1.2 → ✅; **close Phase 1** — capture
  `restore/phase-1-green`, add the inventory row, flip the Phase 1 Progress row ✅.
- **On fail:** stays 🟡; fix and re-run.
- **Advancement gate:** Phase 2 cannot begin until the Phase 1 gate passes.

### Risks & Watch-Items

- **HTTPS-token clone:** use the token-embedded HTTPS URL form for the CloudShell
  clone; rotate any token that leaks into terminal output.
- **/tmp is ephemeral in CloudShell:** anything staged in `/tmp` is wiped on session
  recycle — regenerate rather than assume persistence.
- **Feed commands one line at a time** in CloudShell; multi-line pastes can mis-feed.
- **ExternalId** must be supplied to the gate script's assume-role calls (matches the
  Story 1.1 trust condition).

### Lessons Learned / Carry-Forward *(authored at the end of Story 1.1)*

- **Story 1.1 was re-scoped** to the trust fabric (RD-006) with the org-wide audit
  deferred (RD-007, tracked as OD-002). If Story 1.1's live validation surfaced any
  trust/ExternalId lessons, fold them in here.
- **Current true state at handoff:** Story 1.1 was 🟡 (built + offline-proven, 19
  invariants), pending the operator's live Hub→Spoke AssumeRole pass. **Confirm 1.1 is
  ✅ and VD-2 cleared before starting 1.2** (hard advancement gate).
- **The Hub deployer role** (`pde-hub-deployer`) referenced by the trust fabric is
  created in Phase 2 — the gate script may need a temporary Hub principal to run the
  AssumeRole if Phase 2 hasn't started; note whatever was actually used.
- **User notes:** _(open for the user)_
