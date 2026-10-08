# Operations — TEMPLATE (the Builder's operator instructions)

> **Purpose.** The standardized **operator execution surface** authored by the
> **Designer / Builder seat (Kiro)**: the exact, in-order commands the Human runs on
> the real system to *produce raw evidence* for a story. One per story, stored under
> `session-briefs/` as `story-<id>-LIVE-RUNBOOK.md`. See
> [`../governance/AGENTS.md`](../governance/AGENTS.md) §2.2.
>
> **This is NOT the acceptance criteria ([`../governance/AGENTS.md`](../governance/AGENTS.md) §4.1).**
> Operations tell the operator *how to produce raw output*; they must never say
> "judge X by Y." The independent Validator authors the Definition of Done; this
> file only produces the evidence the Validator reads.
>
> **Moderator gates are wired in, not optional ([`../governance/MODERATOR_PROTOCOL.md`](../governance/MODERATOR_PROTOCOL.md)).**
> Every run passes the four mechanical gates *before* validation: **Pre-Execution**
> (right branch/secrets, gate state), **Deployment** (branch actually applied; no
> dead stack; branch marker present on the live resource), **Preflight** (live
> infra matches the story baseline; right account), **Live Result** (output is from
> the proven target). A red gate is a hard stop — a run on stale/wrong/un-deployed
> infra judges nothing. Map each STEP to the gate it satisfies.
>
> **KEEP IT LEAN — fat causes drift and hallucination (RD-008 / METHODOLOGY §7).**
> Load-bearing commands only; one canonical copy; re-trim on re-scope. Fill every
> `{{...}}`, delete these blockquotes.

---

## Story {{STORY_ID}} — {{STORY_TITLE}} · LIVE operations

### Prerequisites & Environment assumptions

- **Target(s):** {{account name + id + region per environment this run touches; the
  operator trusts `aws sts get-caller-identity`, not a label}}.
- **Zero-touch (never a target):** {{accounts/namespaces that must not be touched}}.
- **Checkout:** inside a fresh clone of `{{repo}}` on `{{branch}}` at a known HEAD.
- **Secrets/params required:** {{named secrets/SSM params that must exist with REAL
  values — not placeholders — before STEP 0}}.
- **Tooling:** {{CLIs/scripts the steps assume}}.

### STEP 0 — Pre-Execution Gate · launch pad + secrets *(Moderator: Pre-Execution)*

```bash
# Target: {{ACCOUNT NAME account-id (region)}}
{{commands: confirm identity, clone the correct repo on the correct branch, record
  HEAD; populate required secrets/params with REAL values}}
```

- **Verify:** `aws sts get-caller-identity` = the expected account; `git rev-parse
  --abbrev-ref HEAD` = `{{branch}}`; every required secret resolves (not a
  placeholder). STOP on any mismatch — this is the Pre-Execution Gate (fail-closed).

### STEP 1 … STEP N — Deployment & Preflight *(Moderator: Deployment, then Preflight)*

> One STEP per discrete action. Each carries an **account banner**, then a
> **Verify** block that reads the *live resource*, not the deploy exit code. Tag each
> STEP with the Moderator gate it satisfies.

```bash
# Target: {{ACCOUNT NAME account-id (region)}}
{{STEP n commands — reconcile namespace / deploy the branch template(s) / etc.}}
```

- **Verify (Deployment Gate):** {{read a branch-specific marker off the deployed
  resource — a new tag/version/policy/env var — proving the branch is really live;
  confirm no dead/rolled-back stack remains}}.
- **Verify (Preflight Gate):** {{before triggering validation, run the story's
  preflight (e.g. `python3 scripts/preflight_<story>.py`) to a printed `PASS`; it
  reads live infra and hard-fails unless it matches the story baseline + confirms the
  right account. A FAIL = branch not deployed; go back. An env error ≠ a result}}.

### STEP N+1 — Exercise + capture *(Moderator: Live Result)*

```bash
# Target: {{ACCOUNT NAME account-id (region)}}
{{trigger the behaviour under test and capture ALL raw output}}
```

- **Verify (Live Result Gate):** the captured output comes from the target proven
  green by the gates above (pinned HEAD / marker-verified resource), is complete (no
  aborted step, no false-negative "none found" against an absent file), and is handed
  **raw** to the independent Validator — who authors the DoD and seals
  PASS/FAIL/INCONCLUSIVE. The operator does not judge.

### Backout

- **Revert this run:** {{how to undo — delete the created stack(s); or coordinated
  restore to the last good restore point, never a forward-patch}}.
- **Scope guard:** only touch this story's own namespace; never a zero-touch
  account/namespace. {{restore point to return to}}.
