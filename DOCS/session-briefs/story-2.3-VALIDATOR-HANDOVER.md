# Validator Handover — Story 2.3 (Bootstrap PDE control plane into the Hub + the Phase 2 gate — CLOSES Phase 2)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human reviewer who did **not** build this. The builder does not
> author the pass/fail check (split-brain discipline, `governance/METHODOLOGY.md`
> §4a / `AGENTS.md`). Story 2.3 is the **third and final** Phase-2 brick, the
> **first live-deploy story**, and the one that **CLOSES Phase 2** via the Phase 2
> gate. Unlike 2.1/2.2 (static author-only bars), this validation is a **live
> deploy + a live Step Functions gate run** in the Hub.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the requirement in
> your own words) before you send this. Everything else — the branch, the fetch
> commands, the scope boundary — is pre-filled and comes from the repo, not from the
> builder's framing. The validator authors the Definition of Done and the verdict;
> the operator runs its steps live and pastes back the RAW output.
>
> **Operator execution surface:** the live steps the validator will have the operator
> run are the turnkey [`story-2.3-LIVE-RUNBOOK.md`](story-2.3-LIVE-RUNBOOK.md). The
> validator decides the acceptance criteria; the runbook is how the operator produces
> the raw evidence. **The head SHA is NOT pinned in this file on purpose — always
> resolve it LIVE** with `git rev-parse origin/feature/story-2.3` at validation time
> (a hard-coded SHA is exactly what went stale on Story 2.2 attempts 3-5).

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code or runbook under test,
and you must not trust anyone's claim that it works — including the builder's. Author
a Definition of Done and the live-validation steps FROM SCRATCH, try to BREAK the
change, and seal a verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what Story 2.3 was supposed to achieve and how a skeptical person
   would know it is truly correct. Do NOT paste the builder's description. A sketch to
   adapt in your own words: "Our two Phase-2 templates (the CodeBuild projects and the
   Step Functions promotion state machine) have been written and statically proven;
   now actually STAND THEM UP in our Hub account for the first time, via CLI, and prove
   two things from the live system: (1) the IAM roles that landed are locked down to
   exactly their job — no admin, no wildcards, no broad powers — and named/tagged as
   ours so they can never collide with ZTIE's resources; and (2) when a human kicks off
   the pipeline with a throwaway payload, it runs up to the first human-approval point
   ('Awaiting Sandbox Approval') and PAUSES there cleanly, with no permission or
   configuration errors — a real pause that waits for a person, not a timer, and that
   does NOT barrel past the approval on its own. I want this shown from the live AWS
   environment, not from reading the template." ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decisions, not the builder's spin)
- Story 2.3 is a **live deploy + a live gate run** in Pipeline-Hub 641628980935. It
  deploys the ALREADY-SEALED Story 2.1 + 2.2 templates (unchanged this story) and runs
  the Phase 2 gate. The deploy is **strictly additive** net-new `pdlv-` stacks.
- **The Phase 2 gate (the bar to seal):** a dummy-payload execution of the
  `pdlv-promotion-pipeline` state machine **reaches the "Awaiting Sandbox Approval"
  paused state WITHOUT IAM or configuration errors.** It must PAUSE there (status
  RUNNING, waiting on the Step Functions task token) and NOT auto-advance. It must NOT
  require approving/promoting past the pause (that is Phase 3) and must NOT require a
  real cross-account member deploy to succeed — a dummy-safe first step is acceptable;
  YOU decide the acceptable shape of that (see the DeployDev note below).
- **DeployDev runs BEFORE the pause (the one real risk).** The state machine's
  `StartAt` is `DeployDev` (`codebuild:startBuild.sync` on `pdlv-deploy`), and only
  after it completes does the execution reach `AwaitSandboxApproval`. The `pdlv-deploy`
  buildspec starts with `aws sts assume-role` into `pde-member-execution-dev`. The
  Phase-1 member roles trust `pde-hub-orchestrator` (a Hub role that does NOT exist yet
  — the deferred VD-3b), NOT the `pdlv-codebuild-service-role` the deploy project runs
  as. So a naive dummy run can FAIL at `DeployDev` and never reach the pause. The gate
  asks only that the run reaches the pause without errors — it does NOT require a real
  deploy. The LIVE-RUNBOOK STEP 5 offers two dummy-safe routes (make Dev trust the
  CodeBuild service role for the gate / use a no-op DeployDev); YOU author which is
  acceptable. A fabricated pause, or a `DeployDev` failure dressed up as a pause, is a
  FAIL.
- **RD-009 (ratified):** PDE's Hub resource prefix is **`pdlv-`**, NOT `pde-` (which is
  ZTIE's namespace in Pipeline-Hub — 18 pre-existing `pde-*` stacks). Treat any
  `pdlv-` collision or any PDE resource deployed under `pde-` as a DEFECT. Exception:
  the member roles correctly keep their `pde-member-execution-<env>` names (member
  accounts, not the Hub).
- **RD-006 orchestrate-and-pull / Universal Criterion 3 (least privilege):** the
  state-machine execution role may ONLY start/describe/stop the SPECIFIC `pdlv-deploy`
  project (by ARN), publish to the `pdlv-promotion-approval` topic, and write its own
  logs — NO cross-account `sts:AssumeRole`, NO `codebuild:*`/`sns:*`/`*`, NO
  Admin/PowerUser. The cross-account deploy power lives ONLY in the
  `pdlv-codebuild-service-role`, scoped to the three named member-role ARNs. Verify
  this from the LIVE deployed policy JSON, not from the template.
- **RD-003/RD-004:** AWS-native (Step Functions + CodeBuild) + CloudFormation (YAML) +
  AWS CLI / Python 3 only — no Terraform. **Universal Criterion 1:** zero-touch
  management/root account 467866449172. **Universal Criterion 5:** strictly additive /
  ZTIE-safe (never deploy, modify, or tear down a `pde-*` stack or anything in
  Pipeline-Forensics 360999005254, which is ZTIE's).

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 2.3 — branch `feature/story-2.3` -> `main`.
- AUTHORITATIVE REPO (OD-008 — Story 2.2 aborted twice on a wrong-repo clone): the code
  is on GitHub **`warrenrutledge64/pde-platform`** (token-auth clone) — it is NOT a
  CodeCommit repo and is NOT named `pde-hub`. Clone with the whole URL QUOTED and a REAL
  token (never the literal `<TOKEN>`, which bash reads as a redirect — Story 2.2
  attempt 6):
    git clone "https://<REAL-PAT>@github.com/warrenrutledge64/pde-platform.git" && cd pde-platform
    git remote -v   # confirm github.com/warrenrutledge64/pde-platform (NOT codecommit, NOT pde-hub)
- RESOLVE THE TARGET COMMIT LIVE (do NOT accept a pinned SHA — that is what went stale on
  Story 2.2 attempts 3-5):
    git fetch origin
    git rev-parse origin/feature/story-2.3    # <- THIS is the commit to validate (the tip)
    git checkout feature/story-2.3
    git rev-parse --abbrev-ref HEAD           # expect: feature/story-2.3
    git log --oneline -1                      # pin this SHA in your DoD as <HEAD-SHA>
- Fetch the raw diff yourself (do not trust a summary):
    git diff origin/main..feature/story-2.3
- FULL context at the exact head commit (read the whole files, not just the diff):
    git show feature/story-2.3:infra/codebuild-projects.yaml   # Story 2.1 (deployed here, unchanged)
    git show feature/story-2.3:infra/state-machine.yaml        # Story 2.2 (deployed here, unchanged)
    git show feature/story-2.3:infra/member-execution-role.yaml # Story 1.1 member trust (DeployDev depends on it)
    git show feature/story-2.3:DOCS/session-briefs/story-2.3-LIVE-RUNBOOK.md
    git show feature/story-2.3:governance/RUNBOOK.md           # story ledger + RD-006/009 + VD/OD registers
    git show feature/story-2.3:governance/PROJECT_PLAN.md      # the Phase 2 gate statement (verbatim)

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (where you deploy + run the gate, in CloudShell): 641628980935
- Members (the promotion targets, assumed by the deploy project): Dev 946509368326,
  Sandbox 586917955591, Prod 466494951534
- Management/root (must be zero-touch): 467866449172
- Pipeline-Forensics 360999005254 is ZTIE's account — NOT part of PDE, never a target.
- Region: us-east-1. The Hub already holds 18 ZTIE-owned `pde-*` stacks — never a target.
- CloudShell is ~1 GB and has run out of disk mid-validation before (OD-007) — the
  LIVE-RUNBOOK frees disk first and fail-loud-VERIFYs the files exist after checkout.

# YOUR TASK — do these in order
1. From the requirement + the full source above, AUTHOR a Definition of Done: the
   concrete pass/fail conditions that must ALL hold for Story 2.3 to be truly done,
   stated BEFORE you see results. Include at least these adversarial/negative checks:
     - BEFORE deploy, the `pdlv-` namespace is FREE in the Hub (no pre-existing
       `pdlv-*` stack); the deploy is additive (no existing stack modified/deleted);
       no `pde-*` stack and nothing in management/Forensics is touched.
     - Both stacks deploy to CREATE_COMPLETE (not ROLLBACK); CodeBuild FIRST, then the
       state machine. The live resources exist and are `pdlv-`-named: the
       `pdlv-promotion-pipeline` state machine, `pdlv-lint` + `pdlv-deploy` projects,
       the `pdlv-promotion-approval` SNS topic, and the two exec roles. NONE of PDE's
       own resources is `pde-`-named.
     - From the LIVE policy JSON (not the template): the state-machine role has NO `*`
       action, NO `codebuild:*`/`sns:*`/`iam:*`, NO Admin/PowerUser; its only CodeBuild
       grant is scoped to the specific `project/pdlv-deploy` ARN; its only `sns:Publish`
       target is the approval-topic ARN; it holds NO `sts:AssumeRole` into a member role.
       The `pdlv-codebuild-service-role` holds the cross-account assume, scoped to the
       three named `pde-member-execution-<env>` ARNs only. Trust policies name only the
       expected service principals.
     - Every taggable PDE resource carries `Project=PDE` (verify from the live resource).
     - THE GATE: a dummy-payload execution reaches `AwaitSandboxApproval` and PAUSES —
       `describe-execution` status is RUNNING (NOT SUCCEEDED/FAILED/TIMED_OUT/ABORTED),
       and `get-execution-history` shows `DeployDev` succeeded then the execution
       entered `AwaitSandboxApproval` on a `sns:publish.waitForTaskToken` with NO
       following TaskFailed/ExecutionFailed/access-denied/config error. Prove it is a
       NATIVE pause (waiting on the task token), not a timer, and that it does NOT
       auto-advance (still RUNNING a moment later). Decide + state what counts as an
       acceptable dummy-safe `DeployDev`.
     - The task token is NOT sent (no promotion past the pause — that is Phase 3).
2. Write the exact, ordered, copy-paste LIVE steps the operator runs on the real system
   to test each DoD condition. The operator's turnkey steps live in
   DOCS/session-briefs/story-2.3-LIVE-RUNBOOK.md — you may adopt, reorder, or ADD to
   them, but author the acceptance criteria yourself. Label the account each step runs
   in (everything is Hub CloudShell 641628980935; the operator runs
   `aws sts get-caller-identity` first and trusts the OUTPUT, not a banner).
3. The operator runs them and pastes back the RAW output (not a summary). If you need
   something missing (e.g. the full policy JSON, or the execution history), ask for that
   specific command's output — do not assume.
4. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met, shown in the raw output.
   - FAIL — one or more not met (name which + the evidence).
   - INCONCLUSIVE — the output doesn't let you decide (e.g. an execution/environment
     failure: wrong account, out-of-disk clone, DeployDev never ran); say exactly
     what's missing. An environment/execution failure is INCONCLUSIVE, not FAIL.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder.
- Prefer trying to break it over confirming it. The deploy is live — attack the landed
  least-privilege, the naming/tagging, and whether the gate run genuinely PAUSES at
  "Awaiting Sandbox Approval" without errors (vs. fails at DeployDev, or auto-advances,
  or was faked).
- Judge only from the RAW output on the real AWS system — not from code reading alone,
  and not from anyone's assurance. A green `CREATE_COMPLETE` line is NOT proof; the
  described live resource is.
- If this reached you curated by the builder rather than from the repo/stakeholder, say
  so and refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth: this is the first live deploy AND the Phase-2-closing gate — a
  thorough adversarial DoD (additive-deploy safety + live least-privilege + a genuine,
  error-free, non-auto-advancing approval pause) is the right bar.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` Story 2.3 and — **only on PASS** — flips it 🟡 → ✅ (fills
> the Completed date + the `Validation Result` line), **flips the Phase 2
> Progress-Summary row ✅**, cuts `restore/phase-2-green` + its state manifest, adds the
> deployed resources to BOM §2, confirms the merge-order guard reads **DISARMED** at
> head, and authors Story 3.1's warm handoff. **This CLOSES Phase 2 and opens Phase 3.**
> On FAIL/INCONCLUSIVE, 2.3 stays 🟡 and the next session re-focuses on fixing the
> deliverable (FAIL) or re-running cleanly (INCONCLUSIVE execution failure). The
> validator never edits the RUNBOOK; the executor never authors the DoD.
