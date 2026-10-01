# Validator Handover — Story 2.2 (Step Functions state machine — Dev→Sandbox→Prod + approval gates)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human reviewer who did **not** build this. The builder does not
> author the pass/fail check (split-brain discipline, `governance/METHODOLOGY.md`
> §4a / `AGENTS.md`). Story 2.2 is the **second** Phase-2 brick but does **not**
> close Phase 2, and it is **template authoring + static proof only** (no live
> deploy — that's Story 2.3), so the validation is a **static-analysis bar**, not a
> live-deploy exercise.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the requirement in
> your own words) before you send this. Everything else — the branch, the fetch
> commands, the scope boundary — is pre-filled and comes from the repo, not from the
> builder's framing. The validator authors the Definition of Done and the verdict;
> you run its steps live and paste back the RAW output.
>
> **Operator execution surface:** the live steps the validator will have you run are
> the turnkey [`story-2.2-LIVE-RUNBOOK.md`](story-2.2-LIVE-RUNBOOK.md). The validator
> decides the acceptance criteria; the runbook is how the operator produces the raw
> evidence. **Fill the head SHA** (`<HEAD-SHA>` below) with the branch tip once the
> work commit is pushed — pull it yourself with `git rev-parse feature/story-2.2`.

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code under test, and you must
not trust anyone's claim that it works — including the builder's. Author a Definition
of Done and the live-validation steps FROM SCRATCH, try to BREAK the change, and seal a
verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what Story 2.2 was supposed to achieve and how a skeptical person
   would know it is truly correct. Do NOT paste the builder's description. A sketch to
   adapt in your own words: "We need the control-plane orchestrator defined in
   CloudFormation for our Hub: a Step Functions state machine that walks a release
   through Dev, then Sandbox, then Prod, and PAUSES for a human to approve before Sandbox
   and before Prod (a real pause that can wait as long as a person takes, not a timer).
   Each promotion must kick off our existing deploy CodeBuild project — it must NOT be
   granted broad powers of its own. It must be named so it can NEVER collide with ZTIE's
   resources, tagged as ours, and locked down to least privilege. I want proof the
   template + the embedded state-machine definition are well-formed (cfn-lint) and that a
   security scanner (Checkov) doesn't flag it, WITHOUT anything being deployed yet." ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decisions, not the builder's spin)
- Story 2.2 is **author + statically prove only**. The live Hub bootstrap deploy is a
  SEPARATE story (2.3), and the dummy-payload run that reaches "Awaiting Sandbox Approval"
  and pauses is the **Phase 2 gate** (also 2.3). A verdict here must NOT require a live
  `cloudformation deploy`, a `start-execution`, or any created AWS resource — demanding
  one is out of scope. Author an adversarial check that the template is deploy-READY and
  correct, not that it is deployed.
- **RD-009 (ratified):** PDE's Hub resource prefix is **`pdlv-`**, NOT `pde-` (which is
  ZTIE's namespace in Pipeline-Hub — 18 pre-existing `pde-*` stacks). Treat any
  `pde-`-prefixed Hub resource name as a DEFECT. Exception: the promotion inputs name the
  Story 1.1 **member** roles, which correctly keep their `pde-member-execution-<env>`
  names (they live in the member accounts, not the Hub — no collision). That reference is
  correct, not a defect.
- **RD-006 orchestrate-and-pull:** the Hub DIRECTS; the deploy ACTION executes locally in
  the member. The state machine therefore holds NO cross-account `sts:AssumeRole` into a
  member role and NO broad deploy grant — its only "deploy" power is starting the SPECIFIC
  `pdlv-deploy` CodeBuild project (by its project ARN). The cross-account assume lives in
  the Story 2.1 CodeBuild service role, which the deploy project uses. The member role
  ARNs appear in the state machine ONLY as promotion inputs (DefinitionSubstitutions /
  CodeBuild env overrides), never as an IAM grant Resource.
- **Native manual-approval pause:** the pre-Sandbox and pre-Prod approvals must be a
  NATIVE paused state (`.waitForTaskToken` callback), NOT a `Wait`/timer. The pause must
  carry the Step Functions task token so a human can resume (SendTaskSuccess) or reject
  (SendTaskFailure).
- **RD-003/RD-004:** AWS-native (Step Functions + CodeBuild) + CloudFormation (YAML) +
  Python 3 only — no Terraform. **Universal Criterion 3:** least privilege — no wildcard
  actions, no `codebuild:*`, no `sns:*`, no AdministratorAccess/PowerUserAccess.
  **Universal Criterion 1:** zero-touch management/root account. **Universal Criterion 5:**
  strictly additive / ZTIE-safe.

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 2.2 — branch `feature/story-2.2` -> `main` (PR number: [[ fill ]]).
- Get on the right code FIRST and pin the head commit:
    git fetch origin
    git checkout feature/story-2.2
    git rev-parse --abbrev-ref HEAD        # expect: feature/story-2.2
    git rev-parse feature/story-2.2        # this is <HEAD-SHA> — pin it in your DoD
- Fetch the raw diff yourself (do not trust a summary):
    git diff origin/main..feature/story-2.2
- FULL context at the exact head commit (a diff is not enough — read the whole files):
    git show feature/story-2.2:infra/state-machine.yaml
    git show feature/story-2.2:infra/validate_state_machine.py
    git show feature/story-2.2:governance/RUNBOOK.md   # story ledger + RD-009 + VD register
  (Also read the Story 2.1 project this state machine starts, and the Story 1.1 member
   role it ultimately targets, both unchanged this story:
    git show feature/story-2.2:infra/codebuild-projects.yaml
    git show feature/story-2.2:infra/member-execution-role.yaml )

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (where the state machine + CodeBuild live; where the static bar runs in
  CloudShell): 641628980935
- Members (the promotion targets, assumed by the deploy project): Dev 946509368326,
  Sandbox 586917955591, Prod 466494951534
- Management/root (must be zero-touch): 467866449172
- Pipeline-Forensics 360999005254 is ZTIE's account — NOT part of PDE, never a target.
- Region: us-east-1. The build sandbox is OFFLINE (no PyPI); the static bar
  (cfn-lint / Checkov / cfn-guard) runs in the operator's CloudShell / CI.
- CloudShell is ~1 GB and has run out of disk mid-validation before (OD-007) — the
  LIVE-RUNBOOK frees disk first and fail-loud-VERIFYs the files exist after checkout.

# YOUR TASK — do these in order
1. From the requirement + the full source above, AUTHOR a Definition of Done: the
   concrete pass/fail conditions that must ALL hold for Story 2.2 to be truly done,
   stated BEFORE you see results. Include at least these adversarial/negative checks:
     - The ASL definition sequences Dev -> (approve) -> Sandbox -> (approve) -> Prod;
       StartAt is the Dev deploy; the "Next" edges match that exact order.
     - BOTH approval states are `arn:aws:states:::sns:publish.waitForTaskToken` (a native
       pause) and carry `$$.Task.Token` — NOT a `Wait`/timer. Prove there is NO `Wait`.
     - All THREE promotions are `arn:aws:states:::codebuild:startBuild.sync` on the
       SAME `pdlv-deploy` project (ProjectName = ${DeployProjectName}), with per-env
       TARGET_ENV/TARGET_ROLE_ARN/EXTERNAL_ID overrides.
     - NO Hub resource name uses the `pde-` prefix (only `pdlv-`); exports are `pdlv-*`.
     - The execution role has NO `*` action, NO `codebuild:*`, NO `sns:*`, NO
       AdministratorAccess/PowerUserAccess — grep for them and prove absence. The only
       CodeBuild grant is scoped to the specific `project/${DeployProjectName}` ARN; the
       only `sns:Publish` target is the approval topic (not `*`).
     - The state machine grants NO `sts:AssumeRole` into a member role (member ARNs are
       promotion inputs only — RD-006). Prove absence of a member-role ARN as an IAM
       Resource.
     - Every taggable resource carries `Project=PDE`.
     - A deliberately broken template (or a flipped invariant) makes the offline checker
       FAIL loudly (prove the checker actually guards, not just prints PASS). The checker
       ships a `--self-test` that does this in memory (no disk write).
2. Write the exact, ordered, copy-paste LIVE steps I run on the real system to test each
   DoD condition. The operator's turnkey steps live in
   DOCS/session-briefs/story-2.2-LIVE-RUNBOOK.md — you may adopt, reorder, or ADD to
   them, but author the acceptance criteria yourself. These run OFFLINE/CI-side (no AWS
   resource is created in 2.2):
      python3 infra/validate_state_machine.py             # expect: PASS — all 48 invariants hold
      python3 infra/validate_state_machine.py --self-test # guard flips to FAIL on sabotage (in memory, no disk write)
      pip install cfn-lint checkov
      cfn-lint infra/state-machine.yaml
      checkov -f infra/state-machine.yaml --framework cloudformation
   Label the account any step runs in (the static bar is Hub-CloudShell 641628980935).
3. I run them and paste back the RAW output (not my summary). If you need something
   that's missing, ask me for that specific command's output — do not assume.
4. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met, shown in the raw output.
   - FAIL — one or more not met (name which + the evidence).
   - INCONCLUSIVE — the output doesn't let you decide; say exactly what's missing.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder.
- Prefer trying to break it over confirming it. Treat the live deploy + the dummy-payload
  paused-state run (Story 2.3 / the Phase 2 gate) as correctly out of scope — attack the
  template's correctness, the state-machine definition, naming, and least privilege instead.
- Judge only from the RAW output on the real system (static bar + the committed checker's
  offline proof) — not from code reading alone, and not from anyone's assurance.
- If this reached you curated by the builder rather than from the repo/stakeholder, say
  so and refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth: this is an additive, author-only control-plane story proven by a
  static bar (no live state changes) — a thorough-but-proportionate DoD with the
  adversarial sequence / approval-pause / least-privilege checks above is the right bar.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` Story 2.2 and — **only on PASS** — flips it 🟡 → ✅ (fills
> the Completed date + the `Validation Result` line). Story 2.2 does **NOT** close
> Phase 2 (2.3 remains; the Phase 2 gate is the dummy-payload Step Functions run in
> 2.3), so there is **no** restore tag / BOM row / phase-row flip here. On FAIL, 2.2
> stays 🟡 and the next session re-focuses on fixing it. The validator never edits
> the RUNBOOK; the executor never authors the DoD.
