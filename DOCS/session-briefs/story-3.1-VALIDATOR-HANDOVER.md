# Validator Handover — Story 3.1 (Author a trivial, zero-cost Golden-Path artifact — opens Phase 3)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human reviewer who did **not** build this. The builder does not
> author the pass/fail check (split-brain discipline, `governance/METHODOLOGY.md`
> §4a / `AGENTS.md`). Story 3.1 **opens Phase 3** but does **not** close it, and it
> is **template authoring + static proof ONLY** — nothing is deployed in 3.1 (the
> first live deploy is Story 3.2, THROUGH the pipeline). So this validation is a
> **static-analysis bar** (the committed stdlib checker + cfn-lint + Checkov), **not**
> a live-deploy exercise. A verdict here must NOT require a live `cloudformation
> deploy` or any created AWS resource — demanding one is out of scope.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the requirement in
> your own words) before you send this. Everything else — the branch, the fetch
> commands, the scope boundary — is pre-filled and comes from the repo, not from the
> builder's framing. The validator authors the Definition of Done and the verdict;
> you run its steps and paste back the RAW output.
>
> **The head SHA is NOT pinned in this file on purpose — always resolve it LIVE**
> with `git rev-parse origin/feature/story-3.1` at validation time (a hard-coded SHA
> is exactly what went stale on Story 2.2 attempts 3-5). This is a checkout-proof CI
> story: the committed `.github/workflows/static-bar.yml` runs the whole static bar
> on the exact PR head automatically, so the authoritative evidence is the green CI
> run on the PR — no human checkout to go stale.

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code under test, and you must
not trust anyone's claim that it works — including the builder's. Author a Definition
of Done and the validation steps FROM SCRATCH, try to BREAK the change, and seal a
verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what Story 3.1 was supposed to achieve and how a skeptical person
   would know it is truly correct. Do NOT paste the builder's description. A sketch to
   adapt in your own words: "We need ONE tiny, genuinely free CloudFormation artifact —
   a single empty on-demand DynamoDB table (or an SQS queue) — to serve as the test
   PAYLOAD that our pipeline will promote Dev -> Sandbox -> Prod in the next stories.
   It must cost nothing standing (on-demand, no provisioned capacity, no streams, no
   customer KMS key, no backups), be named so it can NEVER collide with ZTIE's pde-*
   resources, be tagged as ours, and describe EXACTLY ONE trivial resource — nothing
   more. I want proof the template is well-formed (cfn-lint) and that a security scanner
   (Checkov) does not flag it, WITHOUT anything being deployed yet." ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decisions, not the builder's spin)
- Story 3.1 is **author + statically prove ONLY**. The first live deploy of this
  artifact is a SEPARATE story (3.2), and it happens THROUGH the pipeline, not by hand.
  A verdict here must NOT require a live `cloudformation deploy` or any created AWS
  resource — demanding one is out of scope. Author an adversarial check that the
  template is deploy-READY, trivial, and zero-cost — not that it is deployed.
- **Zero-cost is a hard requirement.** The artifact must have NO standing cost: on-demand
  billing (`PAY_PER_REQUEST`) with no provisioned capacity; no DynamoDB stream; no global/
  local secondary index; no customer-managed KMS CMK; no point-in-time recovery. Treat any
  of those as a DEFECT (they add cost and/or defeat the "free, disposable payload" purpose).
- **RD-009 (ratified):** PDE's resource prefix is **`pdlv-`**, NOT `pde-` (which is ZTIE's
  namespace in Pipeline-Hub). Treat any `pde-`-prefixed resource NAME / default / export /
  `!Sub` value as a DEFECT. (`pde-` appearing only inside explanatory Description PROSE that
  CITES the RD-009 rule is correct, not a defect.)
- **RD-003/RD-004:** AWS-native + serverless + CloudFormation (YAML) + Python 3 only — no
  Terraform. **Universal Criterion 3:** least privilege — no wildcard actions/resources, no
  admin (this artifact is a bare data resource and should carry NO IAM at all). **Universal
  Criterion 1:** zero-touch management/root account `467866449172` (must not appear).
- **Universal Criterion 5 (strictly additive):** 3.1 adds a NEW template + a NEW offline
  checker; it must not alter the Phase-2 control plane. ZTIE's account 360999005254 is NOT a
  PDE target and must not appear.

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 3.1 — branch `feature/story-3.1` -> `main` (PR number: [[ fill ]]).
- Get on the right code FIRST and RESOLVE THE HEAD LIVE (do NOT trust any pinned SHA):
    git fetch origin
    git checkout feature/story-3.1
    git rev-parse --abbrev-ref HEAD          # expect: feature/story-3.1
    git rev-parse origin/feature/story-3.1   # <- THIS is the commit to validate (the tip)
    git log --oneline -1                     # pin THIS SHA in your DoD as the target lock
- Fetch the raw diff yourself (do not trust a summary):
    git diff origin/main..feature/story-3.1
- FULL context at the exact head commit (a diff is not enough — read the whole files):
    git show feature/story-3.1:infra/golden-path-artifact.yaml
    git show feature/story-3.1:infra/validate_golden_path_artifact.py
    git show feature/story-3.1:.github/workflows/static-bar.yml   # the new checker is wired in
    git show feature/story-3.1:governance/RUNBOOK.md              # story ledger + RD-009 + the register

# ENVIRONMENT FACTS (so you can author account-specific steps if you choose to)
- Pipeline-Hub (where the artifact will eventually deploy, in 3.2+): 641628980935
- Members (the promotion targets, in 3.2-3.4): Dev 946509368326, Sandbox 586917955591,
  Prod 466494951534
- Management/root (must be zero-touch): 467866449172
- Pipeline-Forensics 360999005254 is ZTIE's account — NOT part of PDE, never a target.
- Region: us-east-1. The build sandbox is OFFLINE (no PyPI); the static bar
  (cfn-lint / Checkov) runs in CI on the PR head (checkout-proof) or in CloudShell.

# YOUR TASK — do these in order
1. From the requirement + the full source above, AUTHOR a Definition of Done: the
   concrete pass/fail conditions that must ALL hold for Story 3.1 to be truly done,
   stated BEFORE you see results. Include at least one adversarial/negative check, e.g.:
     - The template declares EXACTLY ONE resource, and it is a trivial zero-cost one
       (on-demand DynamoDB table or SQS queue) — grep/parse and prove there is not a
       second resource, no provisioned capacity, no stream, no GSI, no CMK, no PITR.
     - NO resource NAME / default / export uses the `pde-` prefix (only `pdlv-`); the
       exports are `pdlv-*`. (A `pde-` token in Description PROSE citing RD-009 is OK.)
     - The resource carries the `Project=PDE` tag.
     - There is NO IAM resource and NO wildcard action/resource (a bare payload needs none).
     - A deliberately broken template (or a flipped invariant) makes the offline checker
       FAIL loudly (prove the checker actually guards, not just prints PASS).
2. Write the exact, ordered, copy-paste steps I run to test each DoD condition. These run
   OFFLINE / CI-side (no AWS resource is created in 3.1). The authoritative, checkout-proof
   evidence is the CI static bar on the PR head; you may ALSO have me run the bar by hand:
      # (a) authoritative: the GitHub Actions "PDE infra static bar" run on the PR head
      #     — confirm it is GREEN on the exact tip (checkout-proof; no stale checkout).
      # (b) by hand (Hub CloudShell 641628980935 or any box with the tools):
      python3 infra/validate_golden_path_artifact.py             # expect: PASS — all invariants hold
      python3 infra/validate_golden_path_artifact.py --self-test # guard flips to FAIL on sabotage (in memory, no disk write)
      pip install cfn-lint checkov
      cfn-lint infra/golden-path-artifact.yaml
      checkov -f infra/golden-path-artifact.yaml --framework cloudformation
   Label the account any step runs in (nothing in 3.1 creates AWS resources).
3. I run them and paste back the RAW output (not my summary). If you need something that
   is missing, ask me for that specific command's output — do not assume. If a repeated
   identical FAIL looks like it is grading stale code, re-confirm the target SHA against
   `git rev-parse origin/feature/story-3.1` BEFORE accepting the FAIL (the Story 2.2 lesson).
4. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met, shown in the raw output.
   - FAIL — one or more not met (name which + the evidence).
   - INCONCLUSIVE — the output doesn't let you decide; say exactly what's missing.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder.
- Prefer trying to break it over confirming it. Treat the live deploy (Story 3.2) as
  correctly out of scope — attack the template's triviality, zero-cost, naming, and the
  absence of IAM/wildcards instead.
- Judge only from the RAW output on the real system (the CI static bar on the PR head +
  the committed checker's offline proof) — not from code reading alone, and not from
  anyone's assurance.
- If this reached you curated by the builder rather than from the repo/stakeholder, say
  so and refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth: this is an additive, author-only payload story proven by a static bar
  (no live state changes) — a thorough-but-proportionate DoD with the adversarial
  triviality/zero-cost/naming checks above is the right bar.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` Story 3.1 and — **only on PASS** — flips it 🟡 → ✅ (fills
> the Completed date + the `Validation Result` line) and clears the Story 3.1
> Validation Debt entry so the gate reads DISARMED at the branch head (merge-order
> guard green). Story 3.1 does **NOT** close Phase 3 (3.2-3.4 remain; the Phase 3 gate
> is the live Prod artifact-metadata query), so there is **no** restore tag / BOM row /
> phase-row flip here. On FAIL, 3.1 stays 🟡 and the next session re-focuses on fixing
> it (fix-then-validate-once). The validator never edits the RUNBOOK; the executor
> never authors the DoD.
