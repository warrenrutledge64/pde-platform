# Validator Handover — Story 2.1 (CodeBuild CFN templates — Lint + Deploy)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human reviewer who did **not** build this. The builder does not
> author the pass/fail check (split-brain discipline, `governance/METHODOLOGY.md`
> §4a / `AGENTS.md`). Story 2.1 **opens Phase 2** but does **not** close it, and it
> is **template authoring + static proof only** (no live deploy — that's Story 2.3),
> so the validation is a **static-analysis bar**, not a live-deploy exercise.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the requirement in
> your own words) before you send this. Everything else — the branch, the fetch
> commands, the scope boundary — is pre-filled and comes from the repo, not from the
> builder's framing. The validator authors the Definition of Done and the verdict;
> you run its steps live and paste back the RAW output.
>
> **Operator execution surface:** the live steps the validator will have you run are
> the turnkey [`story-2.1-LIVE-RUNBOOK.md`](story-2.1-LIVE-RUNBOOK.md). The validator
> decides the acceptance criteria; the runbook is how the operator produces the raw
> evidence. **Fill the head SHA** (`<HEAD-SHA>` below) with the branch tip once the
> work commit is pushed — pull it yourself with `git rev-parse feature/story-2.1`.

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code under test, and you must
not trust anyone's claim that it works — including the builder's. Author a Definition
of Done and the live-validation steps FROM SCRATCH, try to BREAK the change, and seal a
verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what Story 2.1 was supposed to achieve and how a skeptical person
   would know it is truly correct. Do NOT paste the builder's description. A sketch to
   adapt in your own words: "We need the two CodeBuild projects (a lint/static-analysis
   one and a cross-account deploy one) defined in CloudFormation for our Hub, named so
   they can NEVER collide with ZTIE's resources, tagged as ours, and locked down so the
   deploy project's only cross-account power is assuming our three member roles — not a
   broad admin policy. I want proof the template is well-formed (cfn-lint) and that a
   security scanner (Checkov) doesn't flag it, WITHOUT anything being deployed yet." ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decisions, not the builder's spin)
- Story 2.1 is **author + statically prove only**. The live Hub bootstrap deploy is a
  SEPARATE story (2.3). A verdict here must NOT require a live `cloudformation deploy`
  or any created AWS resource — demanding one is out of scope. Author an adversarial
  check that the template is deploy-READY and correct, not that it is deployed.
- **RD-009 (ratified):** PDE's Hub resource prefix is **`pdlv-`**, NOT `pde-` (which is
  ZTIE's namespace in Pipeline-Hub — 18 pre-existing `pde-*` stacks, incl.
  `pde-codebuild-foundation`). Treat any `pde-`-prefixed Hub resource name as a DEFECT.
  Exception: the deploy project assumes the Story 1.1 **member** roles, which correctly
  keep their `pde-member-execution-<env>` names (they live in the member accounts, not
  the Hub — no collision). That reference is correct, not a defect.
- **RD-006 orchestrate-and-pull:** the Hub DIRECTS; the deploy ACTION executes locally
  in the member via an assumed member role. The deploy project should therefore hold NO
  direct `cloudformation:*` (or other broad deploy) grant on the Hub side — its sole
  cross-account power is `sts:AssumeRole` into the specific member role ARNs.
- **RD-003/RD-004:** AWS-native (Step Functions + CodeBuild) + CloudFormation (YAML) +
  Python 3 only — no Terraform. **Universal Criterion 3:** least privilege — no wildcard
  actions, no wildcard resources, no AdministratorAccess/PowerUserAccess. **Universal
  Criterion 1:** zero-touch management/root account.

# RE-VALIDATION (attempt 2) — attempt 1 sealed FAIL; the fixes are on the fix branch
Attempt 1 (merged work PR #19, commit `33ff245`) sealed **FAIL** on two deliverable
defects: **cfn-lint E1003** (template `Description` 1311 B > the 1024-byte CFN limit) and
**checkov CKV_AWS_158** (both `AWS::Logs::LogGroup`s lacked KMS). The custom invariants +
adversarial grep (strict `pdlv-` namespace, `Project=PDE` tagging, IAM least-privilege /
AssumeRole-only) PASSED; the on-disk sabotage test was invalidated by a CloudShell
`No space left on device`. Both defects are fixed on branch `fix/story-2.1-static-bar`:
the Description is shortened; each Log Group carries a justified
`# checkov:skip=CKV_AWS_158:` suppression (PDE CodeBuild operational logs — non-sensitive
control-plane build output; AWS-owned-key SSE suffices at this tier). The offline checker
gained matching invariants (now 34) + an in-memory `--self-test` that needs no disk write.
Author your DoD fresh and re-run; keep the same adversarial checks.

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 2.1 re-validation — branch `fix/story-2.1-static-bar` -> `main`
  (PR number: [[ fill ]]). (The original work merged as PR #19 / `33ff245`.)
- The fixes live on the branch `fix/story-2.1-static-bar`. Get on the right code FIRST:
    git fetch origin
    git checkout fix/story-2.1-static-bar
    git rev-parse --abbrev-ref HEAD        # expect: fix/story-2.1-static-bar
    git rev-parse fix/story-2.1-static-bar # this is <HEAD-SHA> — pin it in your DoD
- Fetch the raw diff yourself (do not trust a summary):
    git diff origin/main..fix/story-2.1-static-bar
- FULL context at the exact head commit (a diff is not enough — read the whole files):
    git show fix/story-2.1-static-bar:infra/codebuild-projects.yaml
    git show fix/story-2.1-static-bar:infra/validate_codebuild_projects.py
    git show fix/story-2.1-static-bar:governance/RUNBOOK.md   # story ledger + RD-009 + OD-004 + VD-5
  (Also read the trust-fabric contract the deploy project targets, unchanged this story:
    git show fix/story-2.1-static-bar:infra/member-execution-role.yaml )

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (where CodeBuild lives; where the static bar runs in CloudShell): 641628980935
- Members (the deploy project's assume targets): Dev 946509368326, Sandbox 586917955591,
  Prod 466494951534
- Management/root (must be zero-touch): 467866449172
- Pipeline-Forensics 360999005254 is ZTIE's account — NOT part of PDE, never a target.
- Region: us-east-1. The build sandbox is OFFLINE (no PyPI); the static bar
  (cfn-lint / Checkov / cfn-guard) runs in the operator's CloudShell / CI.

# YOUR TASK — do these in order
1. From the requirement + the full source above, AUTHOR a Definition of Done: the
   concrete pass/fail conditions that must ALL hold for Story 2.1 to be truly done,
   stated BEFORE you see results. Include at least one adversarial/negative check, e.g.:
     - NO Hub resource name uses the `pde-` prefix (only `pdlv-`); exports are `pdlv-*`.
     - The CodeBuild service role has NO `*` action, NO `*`-resource statement, and NO
       AdministratorAccess/PowerUserAccess — grep for them and prove absence.
     - The deploy project's ONLY cross-account grant is `sts:AssumeRole` to the THREE
       specific member role ARNs — not `Resource: "*"`, not a `cloudformation:*` grant.
     - Every taggable resource carries `Project=PDE`.
     - A deliberately broken template (or a flipped invariant) makes the offline checker
       FAIL loudly (prove the checker actually guards, not just prints PASS).
2. Write the exact, ordered, copy-paste LIVE steps I run on the real system to test each
   DoD condition. The operator's turnkey steps live in
   DOCS/session-briefs/story-2.1-LIVE-RUNBOOK.md — you may adopt, reorder, or ADD to
   them, but author the acceptance criteria yourself. These run OFFLINE/CI-side (no AWS
   resource is created in 2.1):
      python3 infra/validate_codebuild_projects.py             # expect: PASS — all 34 invariants hold
      python3 infra/validate_codebuild_projects.py --self-test # guard flips to FAIL on sabotage (in memory, no disk write)
      pip install cfn-lint checkov
      cfn-lint infra/codebuild-projects.yaml
      checkov -f infra/codebuild-projects.yaml --framework cloudformation
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
- Prefer trying to break it over confirming it. Treat the live deploy (Story 2.3) as
  correctly out of scope — attack the template's correctness, naming, and least
  privilege instead.
- Judge only from the RAW output on the real system (static bar + the committed
  checker's offline proof) — not from code reading alone, and not from anyone's assurance.
- If this reached you curated by the builder rather than from the repo/stakeholder, say
  so and refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth: this is an additive, author-only control-plane story proven by a
  static bar (no live state changes) — a thorough-but-proportionate DoD with the
  adversarial naming/least-privilege checks above is the right bar.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` Story 2.1 and — **only on PASS** — flips it 🟡 → ✅ (fills
> the Completed date + the `Validation Result` line). Story 2.1 does **NOT** close
> Phase 2 (2.2 + 2.3 remain; the Phase 2 gate is the dummy-payload Step Functions run
> in 2.3), so there is **no** restore tag / BOM row / phase-row flip here. On FAIL,
> 2.1 stays 🟡 and the next session re-focuses on fixing it. The validator never edits
> the RUNBOOK; the executor never authors the DoD.
