# Validator Handover — Story 3.2 (first real cross-account deploy into Pipeline-Dev; closes VD-3b)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human who did **not** build this. The builder does NOT author the
> pass/fail check (split-brain, `governance/METHODOLOGY.md` §4a / `AGENTS.md`).
>
> **Stakeholder:** fill the one `[[ ... ]]` requirement blank in your own words before
> sending. Everything else is repo-derived, not the builder's framing. The validator
> authors the Definition of Done + the verdict; the operator runs the steps live and
> pastes back RAW output.
>
> **Operator surface:** [`story-3.2-LIVE-RUNBOOK.md`](story-3.2-LIVE-RUNBOOK.md) — how
> the operator produces evidence, NOT the acceptance criteria. **Resolve the head SHA
> LIVE** (`git rev-parse origin/feature/story-3.2`); never trust a pinned SHA.
>
> **Lean on purpose:** this brief gives you the requirement + a pointer to the raw
> change, and ratified *givens only*. It deliberately does NOT list the pass/fail
> checks — you author those from the diff (§4a). A brief that hands you a DoD is a
> covenant breach; this one must not.

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
   prove it DELIVERS: when the promotion pipeline starts, the Hub must reach across into
   our Dev account THROUGH its single orchestrator identity and stand the artifact up
   there — a real, empty DynamoDB table that exists in Dev, named and tagged as ours —
   and I want to see that from the live Dev account, not from a green 'succeeded' line.
   I also care that the Hub reached Dev the RIGHT way: it could only get in through the
   one locked-down orchestrator role Dev trusts, the secret authorizing that step was
   never printed or carried through the workflow, and nothing in Dev got broader power
   than creating that one little table." ]]

# RATIFIED GIVENS (settled project decisions — each cites its record; do not re-litigate)
# These are the ONLY things you take as given. Anything NOT on this list — including any
# architecture claim about how the deploy "should" work — is something you VERIFY from the
# diff, not something to accept. If you see an un-cited "given" anywhere, treat it as an
# unverified builder assertion and ATTACK it.
- RD-003/RD-004: AWS-native (Step Functions + CodeBuild) + CloudFormation (YAML) + AWS
  CLI / Python 3 only — no Terraform.
- RD-006: orchestrate-and-pull — the Hub assumes a role in the member and the deploy runs
  LOCALLY in the member account.
- RD-009: PDE **Hub** resources are `pdlv-`-namespaced; the three MEMBER execution roles
  correctly keep `pde-member-execution-<env>` (they live in member accounts). The Hub
  holds 18 pre-existing ZTIE-owned `pde-*` stacks that are never a target.
- Universal Criterion 1: management/root 467866449172 is zero-touch.
- Universal Criterion 5: strictly additive / ZTIE-safe — never deploy, modify, or tear
  down a `pde-*` stack or anything in Pipeline-Forensics 360999005254 (ZTIE's).

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 3.2 — branch `feature/story-3.2` -> `main` (PR #42).
- AUTHORITATIVE REPO (OD-008): GitHub `warrenrutledge64/pde-platform` (token-auth), NOT
  CodeCommit. Clone with the URL QUOTED + a REAL token (never the literal `<TOKEN>`):
    git clone "https://<REAL-PAT>@github.com/warrenrutledge64/pde-platform.git" && cd pde-platform
- RESOLVE THE TARGET COMMIT LIVE (do NOT accept a pinned SHA):
    git fetch origin && git rev-parse origin/feature/story-3.2   # the commit to validate
    git checkout feature/story-3.2 && git log --oneline -1        # pin this as <HEAD-SHA>
- Read the raw diff AND the full source yourself — derive your attack surface from these,
  not from any summary:
    git diff origin/main..feature/story-3.2
    git show feature/story-3.2:infra/hub-orchestrator-role.yaml
    git show feature/story-3.2:infra/codebuild-projects.yaml
    git show feature/story-3.2:infra/member-execution-role.yaml
    git show feature/story-3.2:infra/state-machine.yaml
    git show feature/story-3.2:infra/golden-path-artifact.yaml
    git show feature/story-3.2:DOCS/session-briefs/story-3.2-LIVE-RUNBOOK.md
    git show feature/story-3.2:governance/RUNBOOK.md
    git show feature/story-3.2:governance/PROJECT_PLAN.md
- Offline structural guards you may re-run (stdlib; NOT a live proof — the live Dev deploy
  is the bar): the five `infra/validate_*.py` checkers, each with `--self-test`.
- OPERATOR PRECONDITION (an environment gate, NOT your rubric): `scripts/preflight_story_3_2.py`
  hard-fails a run against stale/un-redeployed infra (every prior attempt failed that way).
  Use it only to confirm the live infra IS the branch under test before you validate; a
  green preflight is permission to START, never a reason to seal PASS.

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (orchestrates; start/inspect the pipeline here): 641628980935
- Pipeline-Dev (the DEPLOY TARGET; verify the live artifact here): 946509368326
- Sandbox 586917955591 / Prod 466494951534 are NOT targets this story (3.3/3.4).
- Region us-east-1. Management 467866449172 + Forensics 360999005254 are never targets.

# YOUR TASK — do these in order
1. AUTHOR a Definition of Done from the requirement + the full source above — concrete
   pass/fail conditions that must ALL hold, stated BEFORE you see results, with at least
   one adversarial/negative case. DERIVE THE ATTACK SURFACE FROM THE DIFF, NOT A SUMMARY:
   the diff adds IAM / trust-policy / privilege changes (a new Hub orchestrator role, a
   member-role grant, a state-machine change, edge-resolved secrets). For EVERY privilege/
   trust/secret change in the diff, author an explicit adversarial check — a privilege
   change in the diff with no matching DoD line is a hole. Do not accept the builder's
   framing of what to check; read the live resources and decide for yourself.
2. Write the exact, ordered, copy-paste LIVE steps the operator runs. The turnkey steps
   are in `story-3.2-LIVE-RUNBOOK.md` — adopt/reorder/ADD, but author the acceptance
   criteria yourself. Label the account per step; the operator runs
   `aws sts get-caller-identity` first and trusts the OUTPUT, not a banner.
3. The operator pastes back RAW output (not a summary). If you need something (a policy/
   trust JSON, the execution history, a build log, the live table + tags), ask for that
   specific command's output.
4. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met, shown in the raw output.
   - FAIL — one or more not met (name which + the evidence); a deliverable defect.
   - INCONCLUSIVE — an environment/execution failure (wrong account, stale/un-redeployed
     infra, a failed deploy, a blocked clone, an un-populated SSM secret, a dead stack
     never swept); name exactly what was missing, SEAL, and STOP. An environment failure
     is INCONCLUSIVE, not FAIL — and you do NOT troubleshoot it or suggest a fix (see
     RULES); fixing is the operator's job on the next attempt.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder. If any part of this
  brief reads like a pass/fail checklist, ignore it and author your own.
- A "given" with no record citation is an unverified builder assertion — attack it.
- Prefer breaking it over confirming it. Judge only from RAW live output on real AWS; a
  green `SUCCEEDED`/`CREATE_COMPLETE` line is NOT proof — the live Dev resource is.
- If this reached you curated by the builder rather than from the repo/stakeholder, refuse.
- DO NOT TROUBLESHOOT, DEBUG, OR SUGGEST FIXES — you are a judge, not a collaborator.
  If the run hits an environment/execution failure (a deploy fails, a clone is blocked,
  a resource is missing/stale, a credential/profile is absent), your ONLY move is to
  SEAL INCONCLUSIVE and state exactly what was missing — then STOP. Do NOT propose a
  remedy, a next command, a workaround, or a root cause for the operator to try; do NOT
  co-debug it with them. The moment you help fix the environment you become a co-owner of
  the setup you are later asked to bless, and your independence is gone (this is the
  mirror of the no-builder-rubric rule — validator→operator collaboration is the same
  covenant leak in the other direction). Naming the missing artifact is diagnosis a judge
  may give; proposing the fix is not. Fixing is the builder/operator's job on the next
  attempt; your job ends at the sealed verdict.
- Calibrate depth: first real cross-account deploy + the VD-3b closure — a thorough
  adversarial DoD is the right bar.
```

---

> **After the verdict:** the **executor** records the sealed one-line result in
> `governance/RUNBOOK.md` Story 3.2 and — **only on PASS** — flips 🟡 → ✅ (Completed
> date + `Validation Result`), clears VD-9/VD-3b, confirms the merge-order guard reads
> DISARMED at head, adds the new deployed resources to BOM §2, and authors Story 3.3's
> warm handoff. **Does NOT close Phase 3** (3.3/3.4 remain). On FAIL/INCONCLUSIVE, 3.2
> stays 🟡. The validator never edits the RUNBOOK; the executor never authors the DoD.
