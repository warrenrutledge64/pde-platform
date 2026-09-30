# Story 1.1 — Independent Validator Handover

> **Purpose (METHODOLOGY §4a — don't grade your own paper).** Story 1.1 is "done"
> only when validated live and recorded. This handover turns an **independent
> validator** (a fresh chat / a second AI such as Gemini — NOT the builder) into the
> party that authors the pass/fail Definition of Done and the live steps, so the
> builder's understanding is never what's being confirmed.
>
> **How to use.**
> 1. The **stakeholder** (not the executor) fills the two `[[ ... ]]` blanks below:
>    the requirement in your own words, and the ExternalId/account values you'll use.
> 2. Paste the fenced block into a **fresh** validator chat.
> 3. Run the validator's authored steps on the **real system** (Hub + member
>    CloudShell), paste back the **raw output**, and let it seal PASS / FAIL /
>    INCONCLUSIVE.
> 4. Hand the sealed one-line verdict to the executor; the executor records it in
>    `governance/RUNBOOK.md` Story 1.1 and (only on PASS) flips 🟡 → ✅ + clears VD-3.
>
> **The builder (executor) did NOT author the DoD below** — the fenced block asks the
> validator to author it blind from the requirement + the raw change. The executor
> only supplies pointers to the raw change (pulled from the repo, not curated).

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write this code and must not trust any
claim that it works — including the builder's. Author a Definition of Done and live
steps FROM SCRATCH, try to BREAK the change, and seal a verdict from the raw output I
run for you. Do not rubber-stamp.

# THE REQUIREMENT (stakeholder's own words — the one anchor no AI authored)
[[ STAKEHOLDER: state, plainly, what Story 1.1 must achieve and how a skeptic would
   know it truly works. A starting point you may edit/replace:
   "PDE's Hub (641628980935) is a control plane that ORCHESTRATES AND PULLS — it must
    be able to DIRECT a function in each member account (Dev/Sandbox/Prod), where the
    work executes LOCALLY; the Hub must NOT be able to push writes into members, and
    must not be a general write-target. Story 1.1 stands up, in each member, a
    least-privilege execution role that ONLY a specific Hub orchestrator role can
    assume, and only when presenting a shared ExternalId. I want proof that: the role
    exists in each member with a trust policy naming the specific Hub role (NOT the
    account root) and requiring the ExternalId; the intended Hub principal can assume
    it; and assuming it WITHOUT the ExternalId (or as the wrong principal) is DENIED.
    Nothing may be created in the management account 467866449172." ]]

# WHAT CHANGED (raw, from the repo — not curated by the builder)
- Repo: github.com/warrenrutledge64/pde-platform  (branch main, pinned commit d179be0)
- The tier-1 artifact under test: infra/member-execution-role.yaml
- Full context to read (fetch at the pinned commit, do not rely on a diff alone):
    infra/member-execution-role.yaml            (the CloudFormation under test)
    governance/PROJECT_PLAN.md                  (RD-006 amended — the orchestrate-and-pull charter)
    governance/RUNBOOK.md                       (Story 1.1 detail + Phase 1 gate + VD-3)
    DOCS/session-briefs/story-1.1-LIVE-RUNBOOK.md (the operator steps the builder proposes — treat as a HINT to scrutinize, not a rubric to inherit)
  Fetch e.g.:  git fetch origin && git checkout d179be0
               (or read each file at that commit via the repo UI)

# THE LIVE ENVIRONMENT (stakeholder supplies)
- Hub account (orchestrator side):        641628980935
- Management/root (must stay untouched):  467866449172
- Member accounts (deploy targets):       Dev=[[ id ]]  Sandbox=[[ id ]]  Prod=[[ id ]]
- ExternalId to be used:                  [[ your secret — you may keep it private and
                                             just confirm it was used consistently ]]
- CHICKEN-AND-EGG the builder flagged (verify, don't take on faith): the Hub role the
  members trust (pde-hub-orchestrator) is not created until Phase 2. Decide how to
  handle it in your steps: (A) validate the TRUST SHAPE now (role exists + correct
  trust principal/ExternalId via get-role) and defer the full cross-account assume to
  Phase 2; or (B) have me create a temporary Hub stand-in principal to prove the full
  assume today. You choose which gives sufficient evidence; say why.

# YOUR TASK — in order
1. From the requirement + the full context, AUTHOR a Definition of Done: the concrete
   pass/fail conditions that must ALL hold. State them before seeing results. Include
   at least one ADVERSARIAL/negative check (e.g. assume without the ExternalId, or as
   the wrong principal, MUST be denied; nothing lands in 467866449172).
2. Write the exact, ordered, copy-paste LIVE steps I run on the real system, each
   labeled with which account it runs in. Include how to read each result.
3. I run them and paste back the RAW output (not my summary). Ask for more if needed.
4. Judge each DoD condition against the raw output, then SEAL: PASS / FAIL /
   INCONCLUSIVE (name which conditions and the evidence).
5. Output a one-line record for the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; do NOT accept a rubric handed to you. The LIVE-RUNBOOK above is
  the builder's proposed steps — scrutinize them, don't inherit them.
- Prefer trying to break it over confirming it.
- Judge only from RAW live output on the real system, not code-reading or assurances.
- If any input reached you via the builder (curated), say so and refuse — inputs come
  from the stakeholder/repo.
```

---

## Executor's note (for the record — NOT part of the validator's rubric)

- **What the executor built + offline-proved** (so the stakeholder knows what's being
  judged): `infra/member-execution-role.yaml` — a per-member least-privilege execution
  role; trust names `arn:aws:iam::641628980935:role/pde-hub-orchestrator` (a specific
  Hub role, not `:root`) with an `sts:ExternalId` condition; permissions scoped to
  `cloudformation:*` stack ops on this member's `pde-*` namespace (no wildcard, no
  AdministratorAccess). Offline: `python3 infra/validate_trust_fabric.py` → 21
  invariants PASS. (This is context, not the pass/fail rubric — the validator authors
  that.)
- **On the sealed verdict:** the executor records the one-line result in
  `governance/RUNBOOK.md` Story 1.1 and, only on PASS, flips 🟡 → ✅ and clears VD-3.
  On FAIL, Story 1.1 stays 🟡 and the next session re-focuses on fixing it. The
  executor never edits this verdict; the validator never edits the RUNBOOK.
