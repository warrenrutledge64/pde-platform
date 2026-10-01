# Validator Handover — PHASE 1 GATE (Trust Fabric)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a second
> AI, or a human reviewer who did **not** build this. The builder does not author the
> pass/fail check (split-brain discipline, `governance/METHODOLOGY.md` §4a / `AGENTS.md`).
> This is the **end-of-phase gate** handover for Phase 1 — the phase-level sibling of the
> per-story `story-N.N-VALIDATOR-HANDOVER.md`.
>
> **What a phase gate proves (different from a story).** A story handover proves one slice
> against a diff. A **phase gate** proves the **INTEGRATED** Phase-1 outcome — the
> orchestrate-and-pull trust fabric as a whole — against the phase's **gate statement**,
> anchored at the frozen **`restore/phase-1-green`** tag. The validator does not re-check
> stories 1.1/1.2 (those sealed their own PASSes — their recorded results are carried below
> as context); it authors a DoD for the **integrated phase** + its restore point + its bill
> of materials.
>
> **This is a RETROACTIVE / HISTORICAL re-proof.** Phase 1 is already CLOSED (✅, Story 1.2
> sealed PASS 2026-10-01, `restore/phase-1-green` cut). This handover re-proves the closed
> phase AT ITS TAG — not against `main` today. The anchor is a frozen commit, so there is no
> open-PR / CURRENT-vs-HISTORICAL ambiguity.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the gate requirement in
> your own words) before you send this. Everything else — the pinned tag/commit, the fetch
> commands, the phase story set, the deferred-scope boundary — is pre-filled from the repo,
> not from the builder's framing. The validator authors the Definition of Done and the
> verdict; you run its steps live and paste back the RAW output.

---

```
You are an INDEPENDENT VALIDATOR for the END-OF-PHASE GATE of PHASE 1 (Trust Fabric). You
did NOT build this system, and you must not trust anyone's claim that it works — including
the builder's. Author a Definition of Done and the live-validation steps FROM SCRATCH, try
to BREAK the integrated phase, and seal a verdict from the raw output I run for you. Do not
rubber-stamp. "Each story passed" is NOT a phase pass — the gate is the integrated,
end-to-end live behaviour of the trust fabric against its gate statement.

# THE GATE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ State, plainly, what ALL of Phase 1 must do end-to-end for the trust fabric to be
   "done" — the observable INTEGRATED behaviour (the Hub can direct each member via the
   orchestrate-and-pull trust direction, from a working Hub operator launch pad), not a
   list of stories. The RUNBOOK gate statement (carried verbatim below) is the starting
   point; put it in YOUR words and add any live acceptance you require. ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decision, not the builder's spin)
"Option B" (recorded 2026-09-30 in governance/RUNBOOK.md + PROJECT_PLAN.md RD-006): the Hub
orchestrator role `pde-hub-orchestrator` is created in PHASE 2. Therefore the LIVE
cross-account `sts:AssumeRole` into Dev/Sandbox/Prod — the trust fabric's full live
exercise — is a SEPARATE, DEFERRED item (tracked as **VD-3b**, Phase 2) and is **out of
scope for this verdict**; its absence is NOT a Phase-1 failure. What IS in scope at the
phase tag: the member execution roles exist + trust ONLY the designated Hub principal (not
`*`), the gate script `scripts/phase1_gate.py` is honestly built + offline-proven (24
invariants) and refuses to misfire, and the Hub operator launch pad is reachable with
tooling + token-auth repo access. Author an adversarial check that the live assume is
correctly DEFERRED/SAFE (the trust is in place and least-privilege), not one that demands
it succeed now.

# THE PHASE TARGET (pinned read-only — reproducible by anyone from the SHA)
- Phase: 1 — Trust Fabric
- Restore tag: restore/phase-1-green   commit: 60a27f5c2b505c7b166fd4eec01efba348f62464   (annotated: yes)
  NOTE a pin to RECONCILE: BOM §4 records the Phase-1 validated commit as `7bd6358`, while
  the restore/phase-1-green tag points at `60a27f5`. Treat the DISCREPANCY as a finding to
  check (is `7bd6358` an ancestor of the tag? is the BOM §4 row stale?) — do not assume.
- Reproduce the phase code:  git fetch --tags && git checkout 60a27f5c2b505c7b166fd4eec01efba348f62464
- State manifest (RESTORE.md rule 4 — tag PAIRED WITH a verified manifest): per BOM §4 the
  live-state manifest for restore/phase-1-green is "to be captured" (not yet recorded) — so
  the restore point's STATE HALF is a FINDING to weigh, not a silent pass.
- Accounts in scope: Pipeline-Hub 641628980935 (launch pad + the gate's assume-FROM side);
  members Dev 946509368326 / Sandbox 586917955591 / Prod 466494951534 (the gate's assume
  TARGETS, exercised live in Phase 2 — VD-3b); Management 467866449172 MUST be zero-touch.
  Pipeline-Forensics 360999005254 is ZTIE's account — never a PDE target.
- CROSS-ACCOUNT ACCESS MODEL (do not mistake this for a defect): the gate reaches members via
  `sts:AssumeRole` into `pde-hub-orchestrator` + an ExternalId — it does NOT use AWS CLI named
  profiles (`--profile dev/sandbox/prod`). "The config profile (dev) could not be found" is
  therefore NOT an in-scope failure; the live cross-account assume is the DEFERRED VD-3b
  (`pde-hub-orchestrator` exists only in Phase 2). In-scope member checks at the tag are
  READ-ONLY `aws iam get-role` / `get-role-policy` run from a session that can read the member
  account (confirm the role exists + trusts ONLY the specific Hub principal + requires the
  ExternalId) — not a profile-driven assume.

# VERBATIM RUNBOOK CONTEXT (pulled from the repo, unmodified — the per-story evidence the phase integrates)
- Phase-1 gate statement (the "## Phase 1" _Gate:_ line + the Progress-Summary row):
  _Gate: From an AWS CloudShell session in the Hub account, a human operator (as the Hub
  orchestrator principal) performs an STS AssumeRole into the member execution role in Dev,
  Sandbox, and Prod sequentially, returning their Account IDs — proving the Hub can direct a
  member and the orchestrate-and-pull trust direction is correct. (CloudTrail half deferred
  to the Phase-4 gate per RD-007.) [Option B] Story 1.2 CLOSES Phase 1 on: Hub CloudShell
  reachability + tooling + token-auth repo access proven live, AND the Boto3 gate script
  authored + committed; the live cross-account AssumeRole is the deferred VD-3b (Phase 2)._
- Phase-1 story set (master-table rows, verbatim):
  | 1.1 | Orchestrate-and-pull trust fabric — member execution roles the Hub invokes (RD-006 amended) | — | ✅ | 2026-09-30 | |
  | 1.2 | Configure CloudShell environment with repo access for the bootstrap deploy | 1.1 | ✅ | 2026-10-01 | restore/phase-1-green |
  (Each story's recorded Validation Result is in governance/RUNBOOK.md under its detail block
   + its own story-N.N-VALIDATOR-HANDOVER.md; paste the specific lines you ask for.)

# STEP 0 — LAUNCH-PAD BOOTSTRAP (HARD PRECONDITION — do this FIRST, before anything else)
# This gate RUNS in Hub CloudShell and reads the repo + queries AWS. Story 1.2 proved (over
# FIVE attempts) that the #1 failure mode here is an un-bootstrapped launch pad: a plain
# clone lands on `main` (where the files are not), a stray `~/.git` repo hijacks the clone,
# or the operator runs from the wrong directory — producing exactly `fatal: not a git
# repository` / `No such file or directory`. So BEFORE you (the validator) accept ANY output:
# require the operator to bootstrap the launch pad and paste the `LAUNCH-PAD VERIFY: PASS`
# line. If that line is absent, seal INCONCLUSIVE on the spot (execution failure, NOT a
# deliverable finding, and NOT a regression of the already-closed Phase 1) — do not evaluate
# downstream output from a launch pad that is on the wrong code or wrong directory.
#   cd ~                                  # start from HOME; ~ must NOT itself be a git repo
#   git clone https://<PAT>@github.com/warrenrutledge64/pde-platform.git   # one line; PAT via credential helper per DOCS/CLOUDSHELL_BOOTSTRAP.md
#   cd pde-platform
#   bash scripts/bootstrap_launchpad.sh   # Hub-account check, $HOME-repo guard, clean checkout, fail-loud VERIFY
#   # EXPECT the final line: LAUNCH-PAD VERIFY: PASS   AND   pwd == ~/pde-platform
# (For a HISTORICAL re-proof, after VERIFY PASS also `git checkout 60a27f5…` to pin the phase tag — see below.)

# WHAT TO FETCH (raw, pulled from the repo yourself at the phase tag — not curated by the builder)
# PRECONDITION: STEP 0 above returned `LAUNCH-PAD VERIFY: PASS` and you are in ~/pde-platform.
    git fetch origin --tags
    git checkout 60a27f5c2b505c7b166fd4eec01efba348f62464
    git cat-file -t restore/phase-1-green          # expect: tag (annotated)
    # FULL context at the tag (a diff is not enough — read the whole files):
    git show 60a27f5:infra/member-execution-role.yaml      # the trust-fabric contract (Story 1.1)
    git show 60a27f5:scripts/phase1_gate.py                # the Phase-1 gate script
    git show 60a27f5:scripts/test_phase1_gate.py           # its 24-invariant offline proof
    git show 60a27f5:governance/RUNBOOK.md                 # phase/story ledger + VD + OD + RD
    git show 60a27f5:governance/BOM.md                     # the bill of materials (§2 inventory + §4 restore index)

# YOUR TASK — do these in order
1. From the gate requirement + the full source above, AUTHOR a Definition of Done for the
   PHASE 1 GATE: the concrete pass/fail conditions that must ALL hold for the INTEGRATED
   trust fabric to be done, stated BEFORE you see results. Include at least one adversarial
   check at a SEAM (e.g. a member role trusts ONLY the designated Hub principal + the
   ExternalId, never `*` or the whole Hub account; the gate script cannot be pointed at the
   Hub/management accounts; the offline proof FAILS loudly if an invariant is broken).
2. Write the exact, ordered, copy-paste LIVE steps I run on the real system to test each DoD
   condition, labeling the account each runs in. The offline proofs available with no
   network:
      python3 scripts/test_phase1_gate.py       # expect: PASS — all 24 gate invariants hold
      python3 scripts/check_docs.py              # governance-doc consistency gate
      python3 scripts/phase1_gate.py --help      # usage prints, no boto3 / no AWS call
   LIVE (Hub CloudShell): confirm the member execution roles exist in Dev/Sandbox/Prod and
   their trust policy admits ONLY the designated Hub principal + ExternalId (e.g.
   `aws iam get-role` / `get-role-policy` read-only in each member account), and that the Hub
   launch pad is reachable with tooling. The live cross-account AssumeRole itself is DEFERRED
   (VD-3b) — assert it is correctly set up + least-privilege, do not demand it run.
3. RESTORE-POINT VALIDATION (REQUIRED — the gate validates the restore point, not just
   behaviour). A restore point you have never proven you can restore from is faith. Per BOM
   §4 the Phase-1 state manifest is "to be captured" — so author a DoD item that requires the
   paired state manifest be captured (RESTORE.md read-only Boto3 capture of the Dev/Sandbox/
   Prod member-role projections + Hub launch pad) and VERIFIED against live state before the
   restore point counts as complete; treat "state half not captured" as INCONCLUSIVE for the
   restore-point dimension, never a silent pass. Also reconcile the tag↔BOM §4 commit pin
   (60a27f5 vs 7bd6358).
4. BOM RECONCILIATION (REQUIRED — deployed == inventoried, against live AWS). The BOM is the
   bill of materials: "if it is deployed/produced, it is in the inventory." Have me list the
   Phase-1 deployed materials — the member execution roles (CFN stack `pde-trust-fabric`) in
   each member account — and confirm BOM §2 lists each with its real deployed identity, and
   that nothing deployed for Phase 1 is missing / no BOM §2 Phase-1 row is an orphan. A
   deployed resource absent from the BOM is a FINDING.
5. I run them and paste back the RAW output (not my summary). If you need something missing,
   ask me for that specific command's output — do not assume.
6. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met (incl. restore-point #3 + BOM #4), shown in raw output.
   - FAIL — one or more not met (name which + the evidence).
   - INCONCLUSIVE — the output doesn't let you decide; say exactly what's missing.
7. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — phase 1 gate: <what was checked>, <date>, confirmed by <who>`  (or `FAIL — phase 1: <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder.
- "Each story passed" is NOT a phase pass — judge the integrated live trust fabric.
- A phase gate is NOT passed until its RESTORE POINT is validated (#3) AND its BOM is
  reconciled against live AWS (#4), not just its behaviour.
- Treat the deferred live cross-account assume (VD-3b) as correctly out of scope — attack
  everything else (trust direction, least privilege, the gate script's honesty).
- Judge only from the RAW live output on the real system (and, for the committed script, its
  offline proof) — not from anyone's assurance.
- If this reached you curated by the builder rather than from the repo/stakeholder, say so
  and refuse — the inputs must come from the stakeholder/repo.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` and reconciles the Phase-1 close — confirm `restore/phase-1-green`
> is complete (code tag + a captured, verified state manifest), the BOM §2 inventory matches
> live AWS, and the Progress-Summary Phase 1 row is ✅. `check_docs.py` CHECK N hard-checks
> that a ✅ phase has its restore point recorded in BOM.md. The validator never edits the
> RUNBOOK; the executor never authors the DoD. (Phase 1 is already ✅ CLOSED; a FAIL/
> INCONCLUSIVE here opens a remediation item — it does not silently re-open the phase.)
