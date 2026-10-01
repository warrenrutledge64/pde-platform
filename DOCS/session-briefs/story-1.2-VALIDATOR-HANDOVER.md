# Validator Handover — Story 1.2 (CloudShell bootstrap + Phase-1 gate)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a
> second AI, or a human reviewer who did **not** build this. The builder does not
> author the pass/fail check (split-brain discipline, `governance/METHODOLOGY.md`
> §4a / `AGENTS.md`). Story 1.2 **closes Phase 1**, so it gets the full treatment.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the requirement in
> your own words) before you send this. Everything else — the pinned commit, the
> fetch commands, the scope boundary — is pre-filled and comes from the repo, not
> from the builder's framing. The validator authors the Definition of Done and the
> verdict; you run its steps live and paste back the RAW output.
>
> **Operator execution surface (option 3, nested):** the live steps the validator
> will have you run are the turnkey
> [`story-1.2-LIVE-RUNBOOK.md`](story-1.2-LIVE-RUNBOOK.md). The validator decides the
> acceptance criteria; the runbook is how the operator produces the raw evidence.

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code under test, and you must
not trust anyone's claim that it works — including the builder's. Author a Definition
of Done and the live-validation steps FROM SCRATCH, try to BREAK the change, and seal a
verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
Story 1.2 had to give us a working, reproducible operator launch pad in our Pipeline-Hub
account's CloudShell, and commit the script that will later prove the trust fabric. A
skeptical operator should be able to sit down in Hub CloudShell and confirm, with their
own eyes:
  - They are actually in the Hub account 641628980935 (confirmed from the live identity
    output, not a tab label).
  - The real tooling is present and runnable — AWS CLI (v2), Python 3, Boto3, and
    cfn-lint — not just "should be there."
  - They can clone our repo over a token-authenticated HTTPS URL, the templates/scripts
    land on disk, and the embedded token does not stay sitting in the repo config.
  - The committed Phase-1 gate script proves itself with NO network (its offline check
    passes) and its --help runs — so the artifact that will validate the real trust
    fabric in Phase 2 is already correct and ready.
  - Nothing was deployed anywhere, least of all the management account (zero-touch).
I do NOT expect the live cross-account assume into Dev/Sandbox/Prod to run yet — the Hub
orchestrator role does not exist until Phase 2, and that live run is deliberately
deferred (VD-3b). Its absence is not a failure. I DO expect the gate script to be
honestly built: no secret baked in, no way to point it at the wrong accounts, and it
should refuse to run from anywhere but the Hub.

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decision, not the builder's spin)
This project chose "Option B" (recorded 2026-09-30 in governance/RUNBOOK.md and
PROJECT_PLAN.md RD-006): the Hub orchestrator role `pde-hub-orchestrator` is created in
PHASE 2. Therefore Story 1.2's Definition of Done is **Hub-CloudShell reachability +
tooling + token-auth repo access, plus the Phase-1 gate script committed and proven
OFFLINE**. The LIVE cross-account `sts:AssumeRole` into Dev/Sandbox/Prod is a SEPARATE,
DEFERRED item (tracked as VD-3b, Phase 2) and is **out of scope for this verdict** —
its absence is NOT a Story 1.2 failure. (Author an adversarial check that it is
correctly DEFERRED/safe, not one that demands it succeed now.) Everything else is fair
game to attack.

# RE-VALIDATION (attempt 2) — attempt 1 sealed FAIL; the fixes are in the new head
Attempt 1 (head `fcfe4f3d`) FAILED on two operator-launch-pad defects — the token was
left in the git remote, and the 1.2 artifacts were not on disk because the live
CloudShell was never checked out onto this story's branch (a plain `git clone` lands on
`main`, where the files do not yet exist, so `git show fcfe4f3d` was `invalid object
name`). Both are fixed in the remediation head below (token-safe credential-helper
clone, explicit `feature/story-1.2` checkout, and a fail-loud launch-pad VERIFY block).
Author your DoD fresh and re-run; keep the same adversarial checks.

ATTEMPT 2 ALSO FAILED — but as an EXECUTION MISMATCH, not a new code defect: the live
CloudShell ran the OLD token-in-URL command (literal `YOUR_TOKEN` placeholder) and
landed on a commit (`330487…`) that exists NOWHERE in the repo, so the hardened flow
was never executed. For attempt 3, make the launch-pad setup a HARD PRECONDITION of your
DoD: require the operator to run the single **STEP 0 ONE-SHOT BOOTSTRAP** block in
DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md and paste its final `LAUNCH-PAD VERIFY:
PASS` line (HEAD on `feature/story-1.2`, remediation commit `677b632` present, scripts
on disk, no token in `.git/config`) BEFORE any STEP 1+ output is accepted. If that line
is absent, seal FAIL/INCONCLUSIVE on the spot — do not evaluate downstream output from a
launch pad that is on the wrong code.

# WHAT CHANGED (raw, pulled from the repo yourself — not curated by the builder)
- Story / PR: Story 1.2 — PR #17 (branch `feature/story-1.2` -> `main`).
- Pinned commits:  base `1ba738bd899911e6e16009c909f0363981724681`
                   head `677b632bec48e629315a07953b183d396eccad49`  (attempt-2 remediation)
- The 1.2 artifacts live on the branch `feature/story-1.2`, NOT on `main` (the PR is
  unmerged). Get on the right code FIRST, or every file check will fail:
    git fetch origin
    git checkout feature/story-1.2
    git rev-parse --abbrev-ref HEAD        # expect: feature/story-1.2
- Fetch the raw diff yourself (do not trust a summary):
    git diff 1ba738bd899911e6e16009c909f0363981724681..677b632bec48e629315a07953b183d396eccad49
- FULL context at the exact head commit (a diff is not enough — read the whole files):
    git show 677b632:scripts/phase1_gate.py
    git show 677b632:scripts/test_phase1_gate.py
    git show 677b632:DOCS/CLOUDSHELL_BOOTSTRAP.md
    git show 677b632:DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md    # includes the new STEP 2a VERIFY gate
    git show 677b632:governance/RUNBOOK.md        # story ledger + Validation Debt Register (VD-4; attempt-1 FAIL recorded)
  (Also read the trust-fabric contract the gate script targets, unchanged this story:
    git show 677b632:infra/member-execution-role.yaml )

# ENVIRONMENT FACTS (so you can author account-specific steps)
- Pipeline-Hub (where CloudShell + the gate run): 641628980935
- Members (the gate's assume targets, Phase 2): Dev 946509368326, Sandbox 586917955591,
  Prod 466494951534
- Management/root (must be zero-touch): 467866449172
- Pipeline-Forensics 360999005254 is ZTIE's account — NOT part of PDE, never a target.
- Region: us-east-1. The build sandbox is OFFLINE (no network); live runs happen in
  the operator's CloudShell.

# YOUR TASK — do these in order
1. From the requirement + the full source above, AUTHOR a Definition of Done: the
   concrete pass/fail conditions that must ALL hold for Story 1.2 to be truly done,
   stated BEFORE you see results. Include at least one adversarial/negative check
   (e.g. the gate script must REFUSE to run outside the Hub; must NOT contain a
   hardcoded ExternalId; must NOT be able to target the Hub/management accounts; the
   offline proof must FAIL loudly if an invariant is broken).
2. Write the exact, ordered, copy-paste LIVE steps I run on the real system to test
   each DoD condition. The operator's turnkey steps live in
   DOCS/session-briefs/story-1.2-LIVE-RUNBOOK.md — you may adopt, reorder, or ADD to
   them, but author the acceptance criteria yourself. Label the account each step runs
   in. For a no-network check of the committed script, these are available offline:
      python3 scripts/test_phase1_gate.py       # expect: PASS — all 24 gate invariants hold
      python3 scripts/check_docs.py              # governance-doc consistency gate
      python3 scripts/phase1_gate.py --help      # usage prints without boto3 / no AWS call
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
- Prefer trying to break it over confirming it. Treat the deferred live-assume (VD-3b)
  as correctly out of scope — attack everything else.
- Judge only from the RAW live output on the real system (and, for the committed
  script, its offline proof) — not from anyone's assurance.
- If this reached you curated by the builder rather than from the repo/stakeholder,
  say so and refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth: this is a phase-closing bootstrap story (reachability + tooling +
  repo access + a committed, offline-proven script) — not a live data-boundary
  exercise. A thorough-but-proportionate DoD, with the adversarial checks above, is
  the right bar.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` Story 1.2 and — **only on PASS** — flips it 🟡 → ✅, clears
> **VD-4**, and closes Phase 1 (cut `restore/phase-1-green`, write the state manifest,
> add the BOM restore-point row, flip the Phase 1 Progress row ✅). On FAIL, 1.2 stays
> 🟡 and the next session re-focuses on fixing it. The validator never edits the
> RUNBOOK; the executor never authors the DoD.
