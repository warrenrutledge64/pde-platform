# Validator Handover — Story 3.2 (Trigger the pipeline → first real cross-account deploy into Pipeline-Dev; closes VD-3b)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human reviewer who did **not** build this. The builder does not
> author the pass/fail check (split-brain discipline, `governance/METHODOLOGY.md`
> §4a / `AGENTS.md`). Story 3.2 is the **first real end-to-end pipeline run** — the
> first time the production `pdlv-promotion-pipeline` does a genuine cross-account
> deploy — and the story that closes **VD-3b** (the live Hub→member assume).
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the requirement in
> your own words) before you send this. Everything else — the branch, the fetch
> commands, the scope boundary — is pre-filled and comes from the repo, not from the
> builder's framing. The validator authors the Definition of Done and the verdict;
> the operator runs its steps live and pastes back the RAW output.
>
> **Operator execution surface:** the live steps the validator will have the operator
> run are the turnkey [`story-3.2-LIVE-RUNBOOK.md`](story-3.2-LIVE-RUNBOOK.md). The
> validator decides the acceptance criteria; the runbook is how the operator produces
> the raw evidence. **The head SHA is NOT pinned in this file on purpose — always
> resolve it LIVE** with `git rev-parse origin/feature/story-3.2` at validation time
> (a hard-coded SHA is exactly what went stale on Story 2.2 attempts 3-5).

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code or runbook under test,
and you must not trust anyone's claim that it works — including the builder's. Author
a Definition of Done and the live-validation steps FROM SCRATCH, try to BREAK the
change, and seal a verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what Story 3.2 was supposed to achieve and how a skeptical person
   would know it is truly correct. Do NOT paste the builder's description. A sketch to
   adapt in your own words: "Our zero-cost test artifact and our Hub control plane are
   built and proven in isolation. Now actually RUN the pipeline for the first time and
   prove it DELIVERS: when the promotion pipeline starts, the Hub must reach across
   into our Dev account THROUGH its single orchestrator identity and stand the artifact
   up there — a real, empty DynamoDB table that exists in Dev, named as ours and tagged
   as ours — and I want to see that from the live Dev account, not from a green
   'succeeded' line. I also care that the Hub reached Dev the RIGHT way: the deploy
   engine could only get into Dev by first stepping through the one locked-down
   orchestrator role (which is the only thing Dev trusts), the secret that authorizes
   that cross-account step was never printed anywhere or carried through the workflow,
   and nothing in Dev got broader power than creating that one little table." ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decisions, not the builder's spin)
- Story 3.2 is a **live pipeline run + a live cross-account deploy**. The Hub
  (641628980935) orchestrates; the artifact is deployed LOCALLY in Pipeline-Dev
  (946509368326). The deploy is **strictly additive** net-new `pdlv-` stacks.
- **THE TWO-HOP DEPLOY CHAIN (the architecture that closes VD-3b).** The real pipeline
  reaches a member account through exactly this chain, and each link trusts exactly one
  principal:
    pdlv-codebuild-service-role  --(hop 1, same account)-->  pde-hub-orchestrator
    pde-hub-orchestrator         --(hop 2, cross-account, + ExternalId)-->  pde-member-execution-dev
  The NEW `pde-hub-orchestrator` role is a PURE PASS-THROUGH: its ONLY permission is
  `sts:AssumeRole` on the three member role ARNs, its trust is pinned to EXACTLY the
  `pdlv-codebuild-service-role` (never the Hub root), and a PERMISSIONS BOUNDARY caps it
  at exactly that so a future over-permissive edit cannot escalate it. The Phase-1
  member roles are UNCHANGED in their trust direction — they still trust
  `pde-hub-orchestrator` + the ExternalId; this story just makes that principal exist.
- **The ExternalId is resolved at the EDGE, never carried through the orchestration.**
  The deploy CodeBuild project reads it from a Hub SSM SecureString
  (`/pdlv/promotion/external-id`) via a `PARAMETER_STORE` env var (natively decrypted +
  MASKED by CodeBuild). It is NO LONGER a state-machine parameter or an
  EnvironmentVariablesOverride — so it must NOT appear in the state-machine definition,
  the execution input, or the execution history. Treat a plaintext ExternalId anywhere
  in the orchestration layer as a DEFECT. (The repo-clone GitHub token follows the same
  pattern: `/pdlv/promotion/repo-token`, resolved at the edge, masked, never in source.)
- **The deploy is a REAL deploy, not a stub.** The `pdlv-deploy` buildspec clones the
  frozen artifact at the edge, performs hop 1 then hop 2, then runs
  `aws cloudformation deploy` of `infra/golden-path-artifact.yaml` as the `pdlv-`
  artifact stack LOCALLY in the member, with the mandatory `Project=PDE` stack tag, and
  then VERIFIES the live table. A green execution/`UPDATE_COMPLETE` line is NOT proof —
  the live Dev table is.
- **The artifact is FROZEN from Story 3.1** (sealed PASS 2026-10-04): one empty
  on-demand `AWS::DynamoDB::Table` (`PAY_PER_REQUEST`, no provisioned capacity / stream
  / GSI / CMK / PITR), `pdlv-golden-path-artifact`, `Project=PDE`. It must be unchanged.
- **Member execution permission (Story 3.2 addition).** The Dev member role's execution
  policy now grants `pdlv-`-scoped CloudFormation stack ops AND a CONCRETE DynamoDB
  table-lifecycle action set (CreateTable/DeleteTable/UpdateTable/Describe*/Tag* — NOT a
  `dynamodb:*` action wildcard, NO data-plane item actions), BOTH scoped STRICTLY to
  `pdlv-*` resource ARNs. Treat any `pde-`/ZTIE-scoped or wildcard-resource grant on the
  member role as a DEFECT. Verify from the LIVE deployed policy JSON, not the template.
- **RD-009 (ratified):** PDE's Hub resource prefix is **`pdlv-`**, NOT `pde-` (ZTIE's
  namespace — 18 pre-existing `pde-*` stacks). The deployed ARTIFACT stack + table are
  `pdlv-`. Exception: the member roles AND the orchestrator role correctly keep their
  `pde-member-execution-<env>` / `pde-hub-orchestrator` names (they are the Phase-1
  trust principals; renaming them would rewrite the validated Phase-1 baseline). Treat a
  PDE Hub STACK or artifact deployed under `pde-` as a DEFECT.
- **RD-003/RD-004:** AWS-native (Step Functions + CodeBuild) + CloudFormation (YAML) +
  AWS CLI / Python 3 only — no Terraform. **Universal Criterion 1:** zero-touch
  management/root 467866449172. **Universal Criterion 5:** strictly additive / ZTIE-safe
  (never deploy, modify, or tear down a `pde-*` stack or anything in Pipeline-Forensics
  360999005254, which is ZTIE's).

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 3.2 — branch `feature/story-3.2` -> `main`.
- AUTHORITATIVE REPO (OD-008): GitHub **`warrenrutledge64/pde-platform`** (token-auth) —
  NOT CodeCommit, NOT `pde-hub`. Clone with the whole URL QUOTED and a REAL token (never
  the literal `<TOKEN>`, which bash reads as a redirect):
    git clone "https://<REAL-PAT>@github.com/warrenrutledge64/pde-platform.git" && cd pde-platform
    git remote -v   # confirm github.com/warrenrutledge64/pde-platform
- RESOLVE THE TARGET COMMIT LIVE (do NOT accept a pinned SHA):
    git fetch origin
    git rev-parse origin/feature/story-3.2    # <- THIS is the commit to validate (the tip)
    git checkout feature/story-3.2
    git rev-parse --abbrev-ref HEAD           # expect: feature/story-3.2
    git log --oneline -1                      # pin this SHA in your DoD as <HEAD-SHA>
- Fetch the raw diff yourself (do not trust a summary):
    git diff origin/main..feature/story-3.2
- FULL context at the exact head commit (read the whole files, not just the diff):
    git show feature/story-3.2:infra/hub-orchestrator-role.yaml    # NEW orchestrator (pass-through + boundary + pinned trust)
    git show feature/story-3.2:infra/codebuild-projects.yaml       # two-hop deploy buildspec + edge-resolved secrets
    git show feature/story-3.2:infra/member-execution-role.yaml    # pdlv--scoped CFN + DynamoDB member grant
    git show feature/story-3.2:infra/state-machine.yaml            # ExternalId passthrough REMOVED
    git show feature/story-3.2:infra/golden-path-artifact.yaml     # frozen Story 3.1 artifact
    git show feature/story-3.2:DOCS/session-briefs/story-3.2-LIVE-RUNBOOK.md
    git show feature/story-3.2:governance/RUNBOOK.md               # story ledger + RD-006/009 + VD/OD registers
    git show feature/story-3.2:governance/PROJECT_PLAN.md          # Phase 3 scope + registered decisions
- Offline proof you can re-run with no AWS/PyPI (stdlib only):
    python3 infra/validate_hub_orchestrator_role.py && python3 infra/validate_hub_orchestrator_role.py --self-test
    python3 infra/validate_trust_fabric.py
    python3 infra/validate_codebuild_projects.py && python3 infra/validate_codebuild_projects.py --self-test
    python3 infra/validate_state_machine.py && python3 infra/validate_state_machine.py --self-test
    python3 infra/validate_golden_path_artifact.py && python3 infra/validate_golden_path_artifact.py --self-test
  (These are structural guards, NOT a live proof — the live Dev deploy below is the bar.)
- OPERATOR PRECONDITION (not your rubric): `scripts/preflight_story_3_2.py` reads the LIVE
  Hub+Dev resources and hard-fails unless they match the Story-3.2 baseline — it exists ONLY
  to stop a validation run against STALE, un-redeployed infra (both prior attempts failed that
  way; attempt 2 ran from outside the clone so the deploys never happened). It is a
  builder-authored ENVIRONMENT GATE, in the same category as "are you in the right account /
  the right clone" — it is NOT your acceptance criteria. Use it (or your own equivalent) only
  to confirm the live infra IS the branch under test; then author your OWN Definition of Done
  and judge the deliverable independently from the raw output. A green preflight is a gate to
  START validating — NEVER a reason to seal PASS. Do not inherit the builder's checks as your
  verdict (split-brain, METHODOLOGY §4a).

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (orchestrates; where you start the pipeline + inspect the execution,
  in CloudShell): 641628980935
- Pipeline-Dev (the DEPLOY TARGET — where you verify the live artifact): 946509368326
- Sandbox 586917955591, Prod 466494951534 are NOT targets this story (3.3/3.4).
- Management/root (must be zero-touch): 467866449172
- Pipeline-Forensics 360999005254 is ZTIE's account — NOT part of PDE, never a target.
- Region: us-east-1. The Hub already holds 18 ZTIE-owned `pde-*` stacks — never a target.
- A missing/empty SSM ExternalId or repo token makes the deploy buildspec FAST-FAIL with
  an explicit message (STEP 0 precondition) — that is an environment/precondition miss
  (INCONCLUSIVE), not a deliverable defect.

# YOUR TASK — do these in order
1. From the requirement + the full source above, AUTHOR a Definition of Done: the
   concrete pass/fail conditions that must ALL hold for Story 3.2 to be truly done,
   stated BEFORE you see results. Include at least these adversarial/negative checks:
     - BEFORE the run, the Dev `pdlv-golden-path-artifact` stack does NOT already exist
       (so a PASS proves THIS run created it); the Hub deploys are additive (no `pde-*`
       stack, management, or Forensics touched); the `pdlv-` namespace is respected.
     - The NEW `pde-hub-orchestrator` role, from its LIVE policy/trust JSON (not the
       template): its ONLY action is `sts:AssumeRole`, scoped to exactly the three
       `pde-member-execution-<env>` ARNs; its trust names ONLY the
       `pdlv-codebuild-service-role` (NOT `:root`, NOT any other principal); it carries a
       PermissionsBoundary; it has NO local Hub power (no cloudformation/s3/logs/kms/ssm)
       and NO read of the ExternalId secret.
     - The `pdlv-codebuild-service-role` assumes ONLY the orchestrator (hop 1) — it holds
       NO direct `sts:AssumeRole` into a member role — plus a read scoped to exactly the
       two named `/pdlv/` SSM parameters (+ `kms:Decrypt` via-SSM only).
     - The ExternalId appears NOWHERE in the state-machine definition, the execution
       input, or the execution history (prove from `describe-state-machine` +
       `get-execution-history`); the deploy project resolves it from SSM
       (`PARAMETER_STORE`) and CodeBuild masks it in the build log.
     - THE DEPLOY: the pipeline execution runs DeployDev, and the `pdlv-deploy` build log
       shows the identity landing in Dev 946509368326 AFTER hop 2 (proof the two-hop
       chain worked live — VD-3b). The Dev artifact stack reaches CREATE_COMPLETE (not
       ROLLBACK), and from the LIVE Dev account `describe-table` returns
       `pdlv-golden-path-artifact` with `BillingMode: PAY_PER_REQUEST` and a `Project=PDE`
       tag. The member role that created it is `pdlv-`-scoped (no wildcard/`pde-` grant).
     - The artifact is unchanged from Story 3.1 (one empty on-demand table; no CMK/PITR/
       stream/GSI/provisioned capacity).
     - Negative: with the ExternalId SSM param ABSENT/empty, the deploy fast-fails with
       the explicit precondition message (NOT a silent AccessDenied) — you may assert
       this by reading the buildspec, or have the operator demonstrate it.
2. Write the exact, ordered, copy-paste LIVE steps the operator runs. The turnkey steps
   live in DOCS/session-briefs/story-3.2-LIVE-RUNBOOK.md — you may adopt, reorder, or ADD
   to them, but author the acceptance criteria yourself. Label the account each step runs
   in (Hub 641628980935 to deploy the control plane + start/inspect the pipeline;
   Pipeline-Dev 946509368326 to redeploy the member role + verify the live artifact). The
   operator runs `aws sts get-caller-identity` first in each account and trusts the
   OUTPUT, not a banner.
3. The operator runs them and pastes back the RAW output (not a summary). If you need
   something missing (the full policy/trust JSON, the execution history, the CodeBuild
   log, the live table description + tags), ask for that specific command's output.
4. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met, shown in the raw output.
   - FAIL — one or more not met (name which + the evidence). A deliverable defect
     (e.g. the orchestrator trusts root, the ExternalId leaks into the execution
     history, the member grant is wildcard/`pde-`, the artifact changed) is a FAIL.
   - INCONCLUSIVE — the output doesn't let you decide (e.g. an execution/environment
     failure: wrong account, out-of-disk clone, an un-populated SSM secret, a dead
     ROLLBACK_COMPLETE stack never swept); say exactly what's missing. An
     environment/execution failure is INCONCLUSIVE, not FAIL.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder.
- Prefer trying to break it over confirming it. The deploy is live — attack the landed
  orchestrator least-privilege + pinned trust + boundary, whether the ExternalId truly
  never leaves the edge, whether the member grant is strictly `pdlv-`-scoped, and whether
  the artifact table GENUINELY exists in the live Dev account (vs. a green line, a
  wrong-account read, or a stale pre-existing table).
- Judge only from the RAW output on the real AWS system — not from code reading alone,
  and not from anyone's assurance. A green `SUCCEEDED`/`CREATE_COMPLETE` line is NOT
  proof; the described live Dev table + the two-hop build log are.
- If this reached you curated by the builder rather than from the repo/stakeholder, say
  so and refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth: this is the first real cross-account deploy AND the VD-3b closure — a
  thorough adversarial DoD (two-hop chokepoint integrity + edge-only secret + live
  least-privilege + a genuinely-present Dev artifact) is the right bar.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` Story 3.2 and — **only on PASS** — flips it 🟡 → ✅ (fills the
> Completed date + the `Validation Result` line), clears **VD-3b** (and VD-9 if opened),
> confirms the merge-order guard reads **DISARMED** at head, adds the new deployed
> resources (the `pde-hub-orchestrator` role + boundary, the two `/pdlv/` SSM
> SecureStrings, the Dev `pdlv-golden-path-artifact` stack/table) to BOM §2, and authors
> Story 3.3's warm handoff. **This does NOT close Phase 3** (3.3 promote-to-Sandbox +
> 3.4 release-to-Prod remain; the Phase 3 gate is the live Prod artifact query). On
> FAIL/INCONCLUSIVE, 3.2 stays 🟡 and the next session re-focuses on fixing the
> deliverable (FAIL) or re-running cleanly (INCONCLUSIVE execution failure). The
> validator never edits the RUNBOOK; the executor never authors the DoD.
