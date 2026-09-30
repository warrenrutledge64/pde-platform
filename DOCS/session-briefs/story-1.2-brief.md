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
  script that assumes into Dev/Sandbox/Prod sequentially and returns their account ids.
- **Why it matters:** it's the operator's launch pad for the Phase 2 bootstrap deploy,
  and running the gate script proves the trust fabric works end to end from the real
  bootstrap context.

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
  passed on trust-*shape* (Path A). **1.2's Phase-1 gate has the same chicken-and-egg:**
  you cannot assume the member role *as* `pde-hub-orchestrator` because it isn't created.
  Resolve at 1.2 start with the stakeholder — either (A) the gate script assumes each
  member role using the **operator's own Hub principal temporarily added to the trust**
  (or a temporary Hub stand-in role), proving reachability now; or (B) treat the
  full-assume as the deferred VD-3b and have 1.2's gate prove Hub-CloudShell reachability
  + tooling + repo access without the assume. Note which was chosen and why.
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
