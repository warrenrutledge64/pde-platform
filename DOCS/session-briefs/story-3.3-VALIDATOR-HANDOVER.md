# Validator Handover — Story 3.3 (Approve the Sandbox gate + promote to `Pipeline-Sandbox`)

> ## ⚠️ OPERATOR — DO THIS FIRST (before you send anything to the validator)
> The validator's step-0 gate REJECTS the request unless you supply a printed
> `preflight_story_3_2: PASS` (both scopes) for the exact commit under test. That PASS
> does not exist until YOU deploy the branch. In order, from inside a FRESH
> `~/pde-platform` clone on `feature/story-3.3` (`git fetch origin && git reset --hard
> origin/feature/story-3.3` — the freshness guard enforces HEAD == the remote tip, the
> Attempt-10 lesson), run the steps in [`story-3.3-operations.md`](story-3.3-operations.md):
> STEP 0 (launch pad + confirm the two `/pdlv/` secrets) → STEP 1 (deploy/refresh the
> **Sandbox** member role from the branch + VERIFY the live role) → STEP 2 (preflight
> **both** `--scope hub` AND `--scope sandbox` to a printed `PASS`). ONLY THEN open a
> fresh validator session and send the fenced block below **plus** those PASS lines. If
> you skip the deploy/preflight, the gate halts you (by design) — the operations file is
> YOURS to run; you do NOT hand it to the validator and the validator does NOT run it or
> help you debug it.
>
> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat / a second
> AI / a human who did **not** build this. The builder does NOT author the pass/fail check
> (split-brain, `governance/METHODOLOGY.md` §4a / `governance/AGENTS.md` §4.1).
>
> **Stakeholder:** fill the one `[[ ... ]]` requirement blank in your own words before
> sending. Everything else is repo-derived, not the builder's framing. The validator
> authors the Definition of Done + the verdict; the operator runs the steps live and
> pastes back RAW output.
>
> **Lean on purpose (RD-008 / §4a):** this brief gives the requirement + a pointer to the
> raw change + ratified *givens only*. It deliberately does NOT list the pass/fail checks —
> the validator authors those from the diff. A brief that hands over a DoD is a covenant
> breach; this one must not.

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code, the operations runbook, or
this brief, and you must not trust anyone's claim that it works — including the builder's.
Author a Definition of Done and the live-validation steps FROM SCRATCH, try to BREAK the
change, and seal a verdict from the RAW output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what Story 3.3 must achieve and how a skeptical person would know it
   is truly correct. Do NOT paste the builder's description. A sketch to adapt in your own
   words: "Story 3.2 already deployed our test artifact into Dev and the pipeline is paused
   waiting for a human to approve promotion to Sandbox. Now approve that gate and prove the
   pipeline actually PROMOTES: after my approval it must reach across into our Sandbox
   account THROUGH the one locked-down orchestrator role and stand the same artifact up
   there — a real DynamoDB table that exists in Sandbox, named and tagged as ours — and I
   want to see that from the live Sandbox account, not a green 'succeeded' line. Then it
   must pause again at the Prod gate (Prod must NOT deploy — that's a later story), and it
   must have reached Sandbox the RIGHT way: only through the one orchestrator role Sandbox
   trusts, the authorizing secret never printed, and nothing in Sandbox given broader power
   than creating that one table." ]]

# RATIFIED GIVENS (settled decisions — each cites its record; do not re-litigate)
# These are the ONLY things you take as given. Anything NOT on this list — including any
# claim about how the promotion "should" work — you VERIFY from the diff, not accept. An
# un-cited "given" is an unverified builder assertion: ATTACK it.
- RD-003/RD-004: AWS-native (Step Functions + CodeBuild) + CloudFormation (YAML) + AWS CLI /
  Python 3 only — no Terraform.
- RD-006: orchestrate-and-pull — the Hub assumes a role in the member and the deploy runs
  LOCALLY in the member account.
- RD-011: the two-hop deploy chain `pdlv-codebuild-service-role` -> `pdlv-hub-orchestrator`
  -> `pde-member-execution-<env>`, with the ExternalId resolved at the CodeBuild edge (never
  in the state-machine history).
- RD-009: PDE **Hub** resources are `pdlv-`-namespaced; the three MEMBER execution roles keep
  `pde-member-execution-<env>` (they live in member accounts). A `pde-*` **Hub** resource is a
  DEFECT; the 18 pre-existing `pde-*` Hub stacks are ZTIE's and are never a target.
- Universal Criterion 1: management/root `467866449172` is zero-touch.
- Universal Criterion 5: strictly additive / ZTIE-safe — never deploy, modify, or tear down a
  `pde-*` stack or anything in Pipeline-Forensics `360999005254`.
- Story 3.2 is ✅ (sealed PASS Attempt 11; tag `story-3.2-validated` @ `30e72f3`); the live
  pipeline execution is holding at `AwaitSandboxApproval`.

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / branch: Story 3.3 — branch `feature/story-3.3` -> `main`.
- AUTHORITATIVE REPO (OD-008): GitHub `warrenrutledge64/pde-platform` (token-auth), NOT
  CodeCommit. Clone with the URL QUOTED + a REAL token (never a literal placeholder).
- RESOLVE THE TARGET COMMIT LIVE (do NOT accept a pinned SHA — staleness is the Attempt-10
  miss): `git fetch origin && git rev-parse origin/feature/story-3.3`; pin that as <HEAD-SHA>.
- Read the raw diff AND the full source of everything the change touches yourself:
    git diff origin/main..feature/story-3.3
    git show feature/story-3.3:infra/member-execution-role.yaml      # Sandbox member role
    git show feature/story-3.3:infra/state-machine.yaml              # promotion / approval flow
    git show feature/story-3.3:infra/codebuild-projects.yaml         # the two-hop deploy
    git show feature/story-3.3:infra/golden-path-artifact.yaml       # the frozen artifact
    git show feature/story-3.3:governance/RUNBOOK.md
- Offline structural guards you MAY re-run (stdlib; NOT a live proof — the live Sandbox deploy
  is the bar): the `infra/validate_*.py` checkers, each with `--self-test`.
- OPERATOR PRECONDITION — NON-BYPASSABLE (an environment gate, the Troikauge Moderator Preflight
  Gate — `governance/MODERATOR_PROTOCOL.md` Gate 3 — NOT your rubric): `scripts/preflight_story_3_2.py`
  reads the LIVE infra and hard-fails unless it matches the baseline. The printed
  `preflight_story_3_2 [hub]: PASS` AND `[sandbox]: PASS` for the EXACT <HEAD-SHA> are the FIRST
  raw artifacts you require (YOUR TASK step 0). A green preflight is permission to START — never
  a reason to seal PASS; its ABSENCE/staleness means SEAL INCONCLUSIVE and STOP.

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (orchestrates; approve + inspect the pipeline here): `641628980935`
- Pipeline-Sandbox (the PROMOTION TARGET; verify the live artifact here): `586917955591`
- Pipeline-Dev `946509368326` already holds the Story-3.2 artifact (not re-deployed here).
- Prod `466494951534` is NOT a target this story (3.4). Management `467866449172` + Forensics
  `360999005254` are never targets. Region `us-east-1`.

# YOUR TASK — do these in order
0. GATE — before authoring or judging ANYTHING, require the operator to paste the printed
   `preflight_story_3_2 [hub]: PASS` AND `[sandbox]: PASS` from `scripts/preflight_story_3_2.py`
   for the EXACT <HEAD-SHA> you resolved. This proves the branch deliverable is deployed. If a
   PASS is absent, stale (a different SHA), or the operator cannot produce it, SEAL INCONCLUSIVE
   ("deliverable not confirmed live — preflight PASS not provided") and STOP. Do NOT author a
   DoD, run steps, or judge until this gate is met.
1. AUTHOR a Definition of Done from the requirement + the full source — concrete pass/fail
   conditions that must ALL hold, stated BEFORE you see results, with at least one adversarial /
   negative case. Derive the attack surface from the DIFF, not a summary: for EVERY privilege /
   trust / secret / promotion-control change in the diff (the Sandbox member grant, the approval/
   promotion flow, any IAM), author an explicit adversarial check — a change with no matching DoD
   line is a hole.
2. Write the exact, ordered, copy-paste LIVE steps the operator runs on the real system to test
   each DoD condition. The turnkey operator steps are in `story-3.3-operations.md` — adopt /
   reorder / ADD, but author the acceptance criteria yourself. Label the account per step; the
   operator runs `aws sts get-caller-identity` first and trusts the OUTPUT, not a banner.
3. The operator pastes back RAW output (not a summary). If you need something (a policy/trust
   JSON, the execution history, a build log, the live Sandbox stack + table + tags), ask for that
   specific command's output.
4. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met, demonstrated in the raw output.
   - FAIL — one or more not met (name which + the evidence); a deliverable defect.
   - INCONCLUSIVE — an environment/execution failure (wrong account, stale/un-redeployed infra, a
     failed deploy, a blocked clone, an un-populated secret, a dead stack). Name exactly what was
     missing, SEAL, and STOP.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric handed to you by the builder. If any part of
  this brief reads like a pass/fail checklist, ignore it and author your own.
- A "given" with no record citation is an unverified builder assertion — attack it.
- Prefer breaking it over confirming it. Judge only from RAW live output on real AWS; a green
  `SUCCEEDED` / `CREATE_COMPLETE` line is NOT proof — the live Sandbox resource is.
- If this reached you curated by the builder rather than from the repo/stakeholder, refuse.
- DO NOT TROUBLESHOOT, DEBUG, OR SUGGEST FIXES (OD-016). On any environment/execution failure your
  ONLY move is to SEAL INCONCLUSIVE + name exactly what was missing, then STOP. Naming the missing
  artifact is diagnosis a judge may give; proposing a remedy, a next command, or a workaround is
  not — fixing is the operator's job on the next attempt. Helping fix the environment makes you a
  co-owner of the setup you are later asked to bless; your independence is then gone.
- Calibrate depth: a cross-account promotion + a human-approval gate — a thorough adversarial DoD
  is the right bar.
```

---

> **After the verdict:** the **executor** records the sealed one-line result in
> `governance/RUNBOOK.md` Story 3.3 and — **only on PASS** — flips 🟡 → ✅, authors Story 3.4's
> warm handoff. **Does NOT close Phase 3** (3.4 remains; the Phase 3 gate is the live Prod
> artifact-metadata query). On FAIL/INCONCLUSIVE, 3.3 stays 🟡. The validator never edits the
> RUNBOOK; the executor never authors the DoD.
