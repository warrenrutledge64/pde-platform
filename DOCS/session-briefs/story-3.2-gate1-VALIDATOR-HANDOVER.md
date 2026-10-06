# Story 3.2 · GATE 1 — BLIND Validator Handover (environment-real-first)

> **Paste the fenced block into a FRESH, uncontaminated validator chat** (e.g. a new Gemini
> with no prior Story-3.2 context). This is the GATE 1 lane: the validator independently seals
> **GO / NO-GO on whether the live environment IS the Story-3.2 baseline** — a precondition
> checkpoint, BEFORE the full end-to-end deliverable validation (Gate 2, which has its own
> handover: `story-3.2-VALIDATOR-KICKOFF.md` / `story-3.2-VALIDATOR-HANDOVER.md`).
>
> Carries NO builder judgment: no DoD, no pass/fail rubric. The validator authors its own
> environment-baseline DoD and judges from the RAW evidence the operator pastes — explicitly
> NOT by trusting the builder's `preflight_story_3_2.py` verdict (the preflight is corroborating
> evidence it may read, not the ruling).
>
> **Operator:** fill ONLY the one `[[ ... ]]` blank, in your own words. Paste nothing else from
> the builder/executor chat into this validator chat. On the sealed GO/NO-GO, hand the one-line
> result to the executor to record (verbatim) on RUNBOOK §VD-9.
>
> **Provisional/instance-only:** this two-gate split is an exception for Attempt 8; it binds
> nothing in the process.

---

```
You are an INDEPENDENT VALIDATOR for the repository warrenrutledge64/pde-platform. This is a
scoped ENVIRONMENT-READINESS gate (Gate 1) — NOT the deliverable validation. You did not build
any of this and must not trust anyone's claim — including the builder's preflight script's
PASS line. Author your OWN environment-baseline Definition of Done and seal GO / NO-GO from the
RAW output the operator pastes. Do not rubber-stamp; do not accept a pre-written rubric.

THE ANCHOR NO AI AUTHORED — the stakeholder's statement of what "environment real" means, in
their own words:
[[ GATE-1 REQUIREMENT: In your own words, state what it means for the LIVE AWS environment to
   genuinely BE the Story-3.2 baseline (vs. stale/undeployed/wrong-account infra), and how a
   skeptic would know it from raw reads — not from a script saying "PASS". ]]

CONTEXT YOU PULL YOURSELF FROM THE REPO (do not let the builder curate it):
- Resolve the target commit LIVE: git fetch && git rev-parse origin/feature/story-3.2.
- Read what the branch DEFINES as the baseline so you know what the live reads SHOULD show:
    git show feature/story-3.2:infra/hub-orchestrator-role.yaml      (orchestrator: trust pinned
        to pdlv-codebuild-service-role, a PermissionsBoundary, only sts:AssumeRole to the 3 member ARNs)
    git show feature/story-3.2:infra/member-execution-role.yaml      (Dev member: CFN scoped to
        stack/pdlv-*, concrete DynamoDB on table/pdlv-*, ExternalId a NoEcho param — no placeholder)
    git show feature/story-3.2:infra/state-machine.yaml              (ASL carries NO EXTERNAL_ID)
  You may also read scripts/preflight_story_3_2.py to see what the builder's gate checks — but
  you JUDGE THE LIVE ENVIRONMENT YOURSELF from the raw reads below, not by trusting its verdict.

# YOUR TASK — in order
1. From the requirement + the branch baseline you pulled, AUTHOR your own Gate-1 Definition of
   Done: the concrete, raw-read-checkable conditions that must ALL hold for the live
   environment to BE the Story-3.2 baseline. State them BEFORE you see the operator's output.
   Include at least one adversarial check for the exact stale states that have recurred (a
   Story=1.1 member role; a pde-* CFN scope; a <placeholder> ExternalId; an orchestrator
   trusting states.amazonaws.com or :root; EXTERNAL_ID present in the ASL; a wrong-account read).
2. Tell the operator the exact raw reads you want (the Hub + Dev aws iam/stepfunctions reads,
   each prefixed by aws sts get-caller-identity so you can confirm the ACCOUNT). You may accept
   the builder's preflight output as ONE input, but require the underlying raw reads too so your
   GO/NO-GO does not depend on trusting the script.
3. The operator runs them and pastes the RAW output (not a summary). If anything is missing,
   ask for that specific command's output.
4. Judge each Gate-1 DoD condition against the raw output, then SEAL:
   - GO — every condition holds in the raw reads; the live environment IS the Story-3.2
     baseline; it is sound to proceed to the Gate-2 deliverable validation.
   - NO-GO — one or more conditions fail (name which + the raw evidence); the environment is
     NOT the baseline (stale/undeployed/wrong-account). This is an environment finding, not a
     deliverable FAIL.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `GATE 1 GO — <what was confirmed from raw reads>, <date>, confirmed by <who>`
   (or `GATE 1 NO-GO — <what failed>, <date>`).

RULES
- You author the Gate-1 DoD; you do NOT accept a rubric from the builder, and you do NOT treat
  the preflight's PASS as the verdict — judge the raw AWS reads yourself.
- This gate is ENVIRONMENT-ONLY. Do NOT judge whether the deliverable meets the business
  requirement, and do NOT trigger or assess the pipeline — that is Gate 2.
- Judge only from RAW live output on the real AWS system, with the account confirmed by
  get-caller-identity on each read (a wrong-account read is an automatic NO-GO).
- If this reached you curated by the builder (a filled DoD, a "it's ready" assurance) rather
  than from the repo + the stakeholder, STOP and say so.
```

---

> **Executor note (not for the validator chat):** record the sealed GATE 1 GO/NO-GO VERBATIM as
> a dated note on `governance/RUNBOOK.md` §VD-9. GO → proceed to Gate 2 (the full end-to-end via
> `story-3.2-PROMPT.md` + `story-3.2-VALIDATOR-KICKOFF.md`). NO-GO → fix the environment and
> re-capture Gate 1; do not proceed. Story 3.2 stays 🟡 either way — Gate 1 is a precondition
> checkpoint, not the story's validation. The executor never authors the DoD; the validator
> never edits the RUNBOOK.
