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

Story 1.1 (the orchestrate-and-pull trust fabric) is validated ✅ — the member
execution roles exist and are directable (assumable) by the Hub orchestrator. Story
1.2 stands up the operator's **bootstrap environment**: the Hub-account CloudShell
with repo access and tooling, and runs the **Phase 1 gate** end to end (the
Hub→member AssumeRole Boto3 script). This story **closes Phase 1**.

### Objective & Value

- **Objective:** a documented, reproducible Hub CloudShell setup (token-auth repo
  clone, AWS CLI, Python 3 / Boto3, cfn-lint) **and** a committed Phase-1-gate Boto3
  script that (when run in Phase 2, as `pde-hub-orchestrator`) assumes into
  Dev/Sandbox/Prod sequentially and returns their account ids. **Per Option B, the
  script is authored + committed in 1.2 but its live cross-account run is VD-3b (Phase
  2)**; 1.2's own live proof is Hub-CloudShell reachability + tooling + repo access.
- **Why it matters:** it's the operator's launch pad for the Phase 2 bootstrap deploy;
  the committed gate script is the exact artifact that will validate the real trust
  fabric end-to-end the moment `pde-hub-orchestrator` exists.

### Scope, Dependencies & Position

- **In scope:** CloudShell setup docs, the Phase-1-gate Boto3 script, running it live.
- **Out of scope:** the control plane (Phase 2); the org-wide CloudTrail (Story 4.1).
- **Depends on:** Story 1.1 ✅ (member execution roles directable by the Hub).
- **Unblocks:** Phase 2.
- **Roadmap position:** closes Phase 1 → capture `restore/phase-1-green`.

### Approach & Constraints

- **Approach:** (1) document the Hub CloudShell bootstrap (token-auth clone per the
  HTTPS-token convention, tooling); (2) author a Boto3 gate script that loops
  Dev/Sandbox/Prod, assumes each member execution role with the ExternalId, prints
  the returned account id; (3) run it live from Hub CloudShell.
- **Hard constraints:** AWS-native tooling; the gate script is Python 3 / Boto3;
  least-privilege (uses the trust fabric, adds no new broad permissions).

### Definition of Done / Validation Gate

- **Done means (Option B):** from Hub CloudShell, the operator has (1) token-auth repo
  access + tooling (AWS CLI, Python 3 / Boto3, cfn-lint) working, proven live, and (2)
  the Phase-1-gate Boto3 script authored + committed (targeting `pde-hub-orchestrator`,
  ExternalId-parameterised, using the derive-from-account pattern). The **live
  cross-account `AssumeRole` run is NOT part of 1.2's DoD** — it is the deferred **VD-3b**,
  run in Phase 2 once `pde-hub-orchestrator` exists.
- **Validated by:** the human operator, live from Hub CloudShell (reachability + tooling
  + repo access); the committed script is reviewed for correctness (offline).
- **Validation Result:** `pending`.
- **On pass:** record it, flip 1.2 → ✅; **close Phase 1** — capture
  `restore/phase-1-green`, add the inventory row, flip the Phase 1 Progress row ✅.
  Phase 1 closes on reachability + tooling + committed gate script; the live assume is
  carried into Phase 2 as VD-3b.
- **On fail:** stays 🟡; fix and re-run.
- **Advancement gate:** Phase 2 cannot begin until the Phase 1 gate (Option B) passes.

### Risks & Watch-Items

- **HTTPS-token clone:** use the token-embedded HTTPS URL form for the CloudShell
  clone; rotate any token that leaks into terminal output.
- **/tmp is ephemeral in CloudShell:** anything staged in `/tmp` is wiped on session
  recycle — regenerate rather than assume persistence.
- **Feed commands one line at a time** in CloudShell; multi-line pastes can mis-feed.
- **ExternalId** must be supplied to the gate script's assume-role calls (matches the
  Story 1.1 trust condition).

### Lessons Learned / Carry-Forward *(authored at the end of Story 1.1 — actual live lessons)*

- **Current true state at handoff:** Story 1.1 is ✅ (sealed PASS by the independent
  validator, VD-3a, 2026-09-30). The member execution roles `pde-member-execution-{dev,
  sandbox,prod}` are deployed in Dev `946509368326` / Sandbox `586917955591` / Prod
  `466494951534`, each trusting `arn:aws:iam::641628980935:role/pde-hub-orchestrator`
  (no `:root`, no wildcard) with an `sts:ExternalId` condition; management `467866449172`
  is zero-touch. The Validation Debt Register is empty and the gate is DISARMED, so 1.2
  is properly unblocked.
- **⚠ The `pde-hub-orchestrator` role does NOT exist yet** — it's Phase 2 work. So the
  1.1 DoD deferred the full live Hub→member `sts:AssumeRole` as **VD-3b (Phase 2)** and
  passed on trust-*shape* (Path A). **1.2's Phase-1 gate had the same chicken-and-egg:**
  you cannot assume the member role *as* `pde-hub-orchestrator` because it isn't created.
  **RESOLVED — Option B (stakeholder-chosen, 2026-09-30):** do NOT stand up a temporary
  Hub principal / stand-in role. 1.2's Phase-1 gate proves **Hub-CloudShell reachability
  + tooling + token-auth repo access**, and the Boto3 gate script is **authored +
  committed now** (targeting the real `pde-hub-orchestrator`) but **run in Phase 2**; the
  full live cross-account `AssumeRole` stays the deferred **VD-3b**. Rationale: A would
  build the exact throwaway trust surface Path A deliberately deferred, in three live
  accounts, to prove a synthetic (stand-in) result that isn't the real orchestrator
  anyway — weak evidence + non-zero teardown risk + a duplicate live cycle. B keeps the
  1.1/1.2 reasoning coherent and validates the *real* assume once, in Phase 2, when the
  genuine principal exists. _(The rejected Option A is retained here for the record.)_
- **THE dominant operator lesson (repeated 3× live, cost multiple cycles): per-account
  copy-paste of a hardcoded `EnvironmentName=` (or any per-account literal) is the #1
  failure mode.** Deploys succeeded but created wrong-named roles in the wrong accounts
  (e.g. `pde-member-execution-sandbox` landed in Prod). **Durable fix — derive the
  per-account value FROM the live account, never hand-edit it:**
  ```bash
  ACCT=$(aws sts get-caller-identity --query Account --output text)
  case "$ACCT" in 946509368326) ENV=dev;; 586917955591) ENV=sandbox;; 466494951534) ENV=prod;; *) ENV="";; esac
  echo "Account $ACCT -> $ENV"   # eyeball BEFORE the mutating command; empty ENV = STOP (not a PDE member)
  ```
  Use this derive-from-account pattern in the 1.2 gate script/commands so a wrong-account
  paste is self-correcting or fail-safe.
- **Trust the `get-caller-identity` OUTPUT, not a banner/comment label** — the operator
  was repeatedly in a different account than the comment claimed. Run it before every
  mutating block and match parameters to the *printed* account.
- **NEVER dump a trust document to inspect it — it leaks the ExternalId.** `aws iam
  get-role ...` returns the full `AssumeRolePolicyDocument`, which includes the
  `sts:ExternalId` condition value; it printed the secret to the transcript twice, forcing
  a rotation. **Inspect with a projection instead:** `--query 'Role.RoleName'`, or a
  presence boolean `--query 'AssumeRolePolicyDocument.Statement[0].Condition.StringEquals."sts:ExternalId" != ``null```. Never echo the secret.
- **ExternalId hygiene:** it's `NoEcho` in the template (good) but leaks via `get-role`
  output; rotate immediately if exposed and use the SAME rotated value across all three
  members (Phase-2's `pde-hub-orchestrator` must present exactly that value). Long-term
  home = Hub Secrets Manager / SSM SecureString (Phase 2).
- **Environment gap that blocked STEP 2 initially:** the validator's CloudShell didn't
  have the repo, so `--template-file infra/member-execution-role.yaml` failed with
  `Invalid template path`. This is literally 1.2's job — **1.2 must document the
  token-auth clone as the first step** so the template is on disk before any deploy.
- **Split-brain discipline held and paid off:** the builder never authored the
  validator's rubric; the independent validator (blind, from the pinned repo) authored
  its own DoD, caught the FAIL twice, and only sealed PASS on the corrected state. Keep
  using `DOCS/session-briefs/story-1.1-VALIDATOR-HANDOVER.md` unchanged for any 1.2 live
  gate — do NOT relay operator history to the validator.
- **User notes:** _(open for the user)_
