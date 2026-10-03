# Validator Handover — PHASE 2 GATE (PDE Control Plane / The Hub)

> **Feed the fenced block below to an INDEPENDENT validator** — a fresh chat, a second
> AI, or a human reviewer who did **not** build this. The builder does not author the
> pass/fail check (split-brain discipline, `governance/METHODOLOGY.md` §4a / `AGENTS.md`).
> This is the **end-of-phase gate** handover for Phase 2 — the phase-level sibling of the
> per-story `story-N.N-VALIDATOR-HANDOVER.md`.
>
> **What a phase gate proves (different from a story).** A story handover proves one slice
> against a diff. A **phase gate** proves the **INTEGRATED** Phase-2 outcome — the PDE
> control plane as a whole — against the phase's **gate statement**, anchored at the frozen
> **`restore/phase-2-green`** tag. The validator does not re-check stories 2.1/2.2/2.3
> (those sealed their own PASSes — their recorded results are carried below as context); it
> authors a DoD for the **integrated phase** + its restore point + its bill of materials.
>
> **This is a close-out gate OWED (tracked as OD-011).** Phase 2 is story-complete (2.1/
> 2.2/2.3 all ✅, `restore/phase-2-green` cut) but its Progress-Summary row is **🟡 (not
> closed)** — the executor prematurely flipped it ✅ on the Story-2.3 gate and reconciled it
> back. This gate is what flips it ✅. The anchor is a frozen tag, so there is no open-PR /
> CURRENT-vs-HISTORICAL ambiguity.
>
> **Stakeholder:** personalize the one blank marked `[[ ... ]]` (the gate requirement in
> your own words) before you send this. Everything else — the pinned tag/commit, the fetch
> commands, the phase story set, the scope boundary — is pre-filled from the repo, not from
> the builder's framing. The validator authors the Definition of Done and the verdict; you
> run its steps live and paste back the RAW output.
>
> **STEP 0 is a HARD PRECONDITION (OD-013).** The attempt-1 gate FAIL (2026-10-02) reported
> the execution environment was "missing the git repo / BOM / scripts / RESTORE manifest",
> and attempt-2 (2026-10-03) again flagged "RESTORE.md missing" — but `governance/RESTORE.md`
> has existed since the greenfield bootstrap (on both `main` and `feature/story-1.2`). The
> root cause was that STEP 0 delegated to `scripts/bootstrap_launchpad.sh`, which is a
> STORY-1.2-specific bootstrap: it checks out `feature/story-1.2` and verifies only Story-1.2
> files, never the Phase-2 target or `governance/RESTORE.md`/`BOM.md`. STEP 0 is now a
> SELF-CONTAINED Phase-2 bootstrap that checks out the CI-GREEN `main` (the OD-012
> reconciliation target, NOT the stale `restore/phase-2-green` tag `3c42d03`, NOT
> `feature/story-1.2`) and verifies the Phase-2 file set (`governance/RESTORE.md`,
> `governance/BOM.md`, `RUNBOOK.md`, the state-machine template + checker + deploy-tag guard)
> and the CKV_AWS_111 reconciliation marker, printing `PHASE-2 LAUNCH-PAD VERIFY: PASS`
> before any gate step. If it does not pass, the validator seals **INCONCLUSIVE (Execution
> Failure)**, not FAIL — and a reported "RESTORE.md missing" when the file IS in the repo is
> itself the signal the launch pad is on the wrong branch.

---

```
You are an INDEPENDENT VALIDATOR for the END-OF-PHASE GATE of PHASE 2 (PDE Control Plane,
The Hub). You did NOT build this system, and you must not trust anyone's claim that it
works — including the builder's. Author a Definition of Done and the live-validation steps
FROM SCRATCH, try to BREAK the integrated phase, and seal a verdict from the raw output I
run for you. Do not rubber-stamp. "Each story passed" is NOT a phase pass — the gate is the
integrated, end-to-end live behaviour of the control plane against its gate statement, plus
its restore point and its bill of materials.

# STEP 0 — HARD PRECONDITION: BOOTSTRAP THE LAUNCH PAD FIRST (do this BEFORE anything else)
# (OD-013 — added after the attempt-1 gate FAIL reported "missing git repo / BOM / scripts
#  / RESTORE manifest". Those files ARE in the repo — that verdict's execution-environment
#  findings were an UN-BOOTSTRAPPED launch pad, not a deliverable defect. A plain clone can
#  land on main / the wrong dir, or a stray ~/.git can hijack it. Bootstrap, then verify,
#  BEFORE you accept any downstream output.)
#   ⚠ DO NOT run `scripts/bootstrap_launchpad.sh` for THIS gate — it is a STORY-1.2-specific
#   bootstrap: it hard-codes `git checkout feature/story-1.2` and verifies only Story-1.2
#   files (phase1_gate.py, member-execution-role.yaml, …). It does NOT check out the Phase-2
#   target and does NOT verify governance/RESTORE.md or governance/BOM.md — which is exactly
#   why attempt-2 (2026-10-03) reported a FALSE "RESTORE.md missing": the launch pad was on
#   the wrong branch, not that the file is absent (governance/RESTORE.md has existed since
#   the greenfield bootstrap, on both main and feature/story-1.2). For a PHASE-2 gate, run
#   this SELF-CONTAINED STEP 0 instead (checks out the Phase-2 target + the Phase-2 file set):
#
#   Run in Pipeline-Hub 641628980935 CloudShell (confirm with `aws sts get-caller-identity`):
#     cd ~ && rm -rf pde-platform
#     # Replace REAL_PAT with a real GitHub PAT — never paste the literal <TOKEN>, and QUOTE
#     # the URL so bash cannot read '<' as a redirect (OD-008 lesson):
#     git clone "https://REAL_PAT@github.com/warrenrutledge64/pde-platform.git"
#     cd pde-platform
#     # The Phase-2 re-validation target is the CI-GREEN main (which carries the OD-012
#     # CKV_AWS_111 reconciliation), NOT the stale restore/phase-2-green tag 3c42d03 and NOT
#     # feature/story-1.2. Resolve + confirm it live:
#     git fetch origin --tags && git checkout main && git reset --hard origin/main
#     git log --oneline -1
#     # Fail-loud PHASE-2 launch-pad VERIFY (note: RESTORE.md/BOM.md live under governance/):
#     ok=1
#     for f in governance/RESTORE.md governance/BOM.md governance/RUNBOOK.md \
#              infra/state-machine.yaml infra/validate_state_machine.py \
#              scripts/check_deploy_tags.py; do
#       [ -f "$f" ] && echo "PASS on disk: $f" || { echo "FAIL MISSING: $f"; ok=0; }
#     done
#     grep -q 'checkov:skip=CKV_AWS_111' infra/state-machine.yaml \
#       && echo "PASS: CKV_AWS_111 reconciliation present (CI-green target)" \
#       || { echo "FAIL: on a pre-reconciliation commit — checkout origin/main"; ok=0; }
#     git cat-file -t restore/phase-2-green >/dev/null 2>&1 \
#       && echo "PASS: restore/phase-2-green tag resolvable" || { echo "FAIL: tag missing"; ok=0; }
#     [ "$ok" = 1 ] && echo "PHASE-2 LAUNCH-PAD VERIFY: PASS" \
#       || echo "PHASE-2 LAUNCH-PAD VERIFY: FAIL — do NOT proceed; paste this output back"
#
#   REQUIRE a printed `PHASE-2 LAUNCH-PAD VERIFY: PASS` before any gate step. If it prints
#   FAIL (any file missing, or the CKV_AWS_111 line absent = a pre-reconciliation checkout),
#   SEAL **INCONCLUSIVE (Execution Failure)** on the spot — NOT FAIL. A FAIL means a
#   deliverable defect; a launch pad that never loaded the right code judged nothing. A
#   reported "RESTORE.md missing" when `governance/RESTORE.md` IS in the repo is itself the
#   signal the launch pad is on the wrong branch — re-run this STEP 0. (Preferred, checkout-
#   proof alternative for the OFFLINE arm: read the committed CI static bar run on main's
#   head — GitHub checks out the exact commit, so no local checkout can go stale.)
#   Only once the Phase-2 launch pad verifies do you proceed to the gate task below.

# THE GATE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ State, plainly, what ALL of Phase 2 must do for the PDE control plane to be "done" — the
   observable INTEGRATED behaviour (the Hub control plane stands up ZTIE-safely and, driven
   with a dummy payload, reaches the human-approval pause cleanly under least privilege),
   not a list of stories. The RUNBOOK gate statement (carried verbatim below) is the
   starting point; put it in YOUR words and add any live acceptance you require. ]]

# SCOPE BOUNDARY YOU MUST TREAT AS A GIVEN (project decisions, not the builder's spin)
- The Phase-2 gate is proven via the SEPARATE, structurally non-promoting `pdlv-gate-probe`
  state machine, NOT a dummy run through the production `pdlv-promotion-pipeline`. Why: the
  production pipeline's first state `DeployDev` does a real cross-account `sts:AssumeRole`
  into `pde-member-execution-dev`, whose trust targets the Phase-3 `pde-hub-orchestrator`
  (the deferred VD-3b) — so a dummy run through production hard-fails at DeployDev by
  design. The probe has NO deploy state and reaches the same `AwaitSandboxApproval`
  `.waitForTaskToken` pause. Treat "the gate is proven on the probe, and the production
  pipeline carries NO input-driven bypass" as the correct design (Option 1b) — author an
  adversarial check that the probe is structurally incapable of promoting (no codebuild/
  startBuild state; terminates in Fail, never Succeed; role is publish+logs only) AND that
  the production pipeline has no gateMode/Choice bypass branch.
- The live cross-account `sts:AssumeRole` (VD-3b) is DEFERRED to Phase 3 (the
  `pde-hub-orchestrator` role is created there). Its absence is NOT a Phase-2 failure — do
  not demand a real member deploy. In scope: the control plane deploys ZTIE-safely, the IAM
  is least-privilege, and the approval pause is reachable with no error.
- RD-009: PDE's Hub prefix is `pdlv-`; `pde-*` (18 stacks) is ZTIE's — never a target.
  Management 467866449172 is zero-touch; Pipeline-Forensics 360999005254 is ZTIE's.

# THE PHASE TARGET (pinned read-only — reproducible by anyone from the SHA)
- Phase: 2 — PDE Control Plane (The Hub)
- Restore tag (as cut at Story-2.3 close): restore/phase-2-green   commit: 3c42d0313f34cd1d61e95576380b55506958edaf   (annotated: yes)
  (The validated Story-2.3 commit `d19f92c` is an ancestor of this merge commit — confirm
   with `git merge-base --is-ancestor d19f92c 3c42d03`.)
- ⚠ STALE-BASELINE NOTICE (OD-012 / CKV_AWS_111, 2026-10-02): the `3c42d03` baseline FAILS the
  CI static bar — Checkov CKV_AWS_111 flags the AWS-mandated `events:Put*` `Resource "*"` on
  `SyncEventsPolicy` (a latent finding that Story 2.3's live-deploy validation never ran
  through CI). The RE-VALIDATION TARGET is therefore NOT `3c42d03` but the NEW, CI-GREEN
  commit that carries the justified `checkov:skip=CKV_AWS_111:` reconciliation (+ the
  matching offline invariant, 62 total). Resolve the target LIVE — do NOT pin a SHA here (a
  pinned SHA goes stale): `git fetch origin && git rev-parse origin/<the-reconciliation-branch>`,
  confirm `grep -n 'checkov:skip=CKV_AWS_111' infra/state-machine.yaml` returns a hit AND the
  CI static bar is GREEN on that head, BEFORE any gate step. On a sealed PASS the stakeholder
  RE-CUTS `restore/phase-2-green` at that CI-green commit (RESTORE.md rule 4) — the frozen
  tag is only trustworthy once its baseline passes the full bar.
- Reproduce the phase code:  git fetch origin && git checkout <the CI-green reconciliation commit>  (NOT 3c42d03 — see the stale-baseline notice)
- State manifest (RESTORE.md rule 4 — tag PAIRED WITH a verified manifest): per BOM §4 the
  live-state manifest for restore/phase-2-green is "to be captured" (tracked as OD-010) — so
  the restore point's STATE HALF is a FINDING to weigh (see #3), not a silent pass.
- Accounts in scope: Pipeline-Hub 641628980935 (where the control plane runs + the gate is
  exercised). Members Dev 946509368326 / Sandbox 586917955591 / Prod 466494951534 are the
  Phase-3 deploy targets (VD-3b) — NOT exercised live here. Management 467866449172 MUST be
  zero-touch; Pipeline-Forensics 360999005254 is ZTIE's — never a PDE target.

# VERBATIM RUNBOOK CONTEXT (pulled from the repo, unmodified — the per-story evidence the phase integrates)
- Phase-2 gate statement (the "## Phase 2" _Gate:_ line + the Progress-Summary row):
  _Gate: A human operator triggers the deployed Step Function in the Hub account with a
  dummy payload, and the execution successfully reaches the "Awaiting Sandbox Approval"
  paused state without IAM or configuration errors._
- Phase-2 story set (master-table rows, verbatim):
  | 2.1 | Author standard CloudFormation templates for the PDE CodeBuild projects (Lint, Deploy), ZTIE-safe prefixes | Phase 1 gate | ✅ | 2026-10-01 | |
  | 2.2 | Author the Step Functions state machine (Dev→Sandbox→Prod promotion + manual approval gates) | Phase 1 gate | ✅ | 2026-10-01 | |
  | 2.3 | Bootstrap the net-new PDE infra into the Hub via CLI, tightly-scoped IAM | 2.1, 2.2 | ✅ | 2026-10-02 | restore/phase-2-green |
  (Each story's recorded Validation Result is in governance/RUNBOOK.md under its detail block
   + its own story-N.N-VALIDATOR-HANDOVER.md; paste the specific lines you ask for. Story
   2.3's sealed PASS: pdlv-promotion-pipeline-stack CREATE_COMPLETE @ d19f92c, IAM
   least-privilege, pdlv-gate-probe reached AwaitSandboxApproval and stayed RUNNING.)

# WHAT TO FETCH (raw, pulled from the repo yourself at the phase tag — not curated by the builder)
    git fetch origin --tags
    git checkout 3c42d0313f34cd1d61e95576380b55506958edaf
    git cat-file -t restore/phase-2-green          # expect: tag (annotated)
    # FULL context at the tag (a diff is not enough — read the whole files):
    git show 3c42d03:infra/codebuild-projects.yaml        # pdlv-lint / pdlv-deploy + service role (Story 2.1)
    git show 3c42d03:infra/state-machine.yaml             # pdlv-promotion-pipeline + pdlv-gate-probe (Stories 2.2/2.3)
    git show 3c42d03:infra/validate_state_machine.py      # the 61-invariant offline proof + --self-test
    git show 3c42d03:governance/RUNBOOK.md                # phase/story ledger + VD + OD + RD
    git show 3c42d03:governance/BOM.md                    # the bill of materials (§2 inventory + §4 restore index)

# YOUR TASK — do these in order
1. From the gate requirement + the full source above, AUTHOR a Definition of Done for the
   PHASE 2 GATE: the concrete pass/fail conditions that must ALL hold for the INTEGRATED
   control plane to be done, stated BEFORE you see results. Include at least one adversarial
   check at a SEAM, e.g.: the state-machine execution role holds NO cross-account
   sts:AssumeRole + no wildcard/admin + its codebuild grant is scoped to the specific
   pdlv-deploy project ARN; the production pipeline has NO input-driven bypass (no
   gateMode/Choice skip of a Deploy or an approval); the gate-probe is structurally
   non-promoting (no codebuild/startBuild state, Fail terminal, publish+logs-only role);
   all Hub resources are pdlv- (never pde-), Project=PDE tagged.
2. Write the exact, ordered, copy-paste LIVE steps I run on the real system to test each DoD
   condition, labeling the account each runs in (all Hub 641628980935; I run
   `aws sts get-caller-identity` first and trust the OUTPUT). The offline proof available
   with no network:
      python3 infra/validate_state_machine.py            # expect: PASS — all invariants hold (the checker prints its own count; it was 61 at tag 3c42d03, 62 after the OD-012/CKV_AWS_111 reconciliation)
      python3 infra/validate_state_machine.py --self-test # guard flips to FAIL on every sabotage
   LIVE (Hub CloudShell): describe the deployed pdlv-codebuild + pdlv-promotion-pipeline-stack
   stacks + their landed roles/policies (least-privilege, pdlv-/Project=PDE), and START THE
   PROBE `pdlv-gate-probe` — show it reaches AwaitSandboxApproval and stays RUNNING on the
   .waitForTaskToken with no States.*/IAM error and no DeployDev/codebuild event. Do NOT send
   the task token; abort the probe after the proof. (See DOCS/session-briefs/story-2.3-LIVE-RUNBOOK.md
   STEP 4/5 for the exact commands; you author the acceptance, the runbook is the surface.)
3. RESTORE-POINT VALIDATION (REQUIRED — the gate validates the restore point, not just
   behaviour). A restore point you have never proven you can restore from is faith. Per BOM
   §4 the Phase-2 state manifest is "to be captured" (OD-010) — require the paired state
   manifest be captured (the RESTORE.md read-only Boto3 projection: the pdlv- CFN stacks'
   template_sha256/params/tags, the pdlv-promotion-pipeline + pdlv-gate-probe definition
   SHAs, the pdlv-* roles' trust + attached policies — see
   DOCS/session-briefs/RESTORE-MANIFEST-CHECKLIST.md) and VERIFIED against live state before
   the restore point counts as complete. Treat "state half not captured" as INCONCLUSIVE for
   the restore-point dimension, never a silent pass. Confirm restore/phase-2-green is
   annotated and that d19f92c is an ancestor of its target.
4. BOM RECONCILIATION (REQUIRED — deployed == inventoried, against live AWS). The BOM is the
   bill of materials: "if it is deployed/produced, it is in the inventory." Have me run
   `aws cloudformation list-stack-resources` for pdlv-codebuild and
   pdlv-promotion-pipeline-stack and confirm BOM §2 lists each produced resource with its
   real deployed identity (the two CodeBuild projects + service role; the promotion state
   machine + role + SNS topic + log group; the gate-probe + role + log group), and that
   nothing deployed for Phase 2 is missing from §2 and no §2 Phase-2 row is an orphan. A
   deployed resource absent from the BOM — or a BOM row with no live resource — is a FINDING.
5. I run them and paste back the RAW output (not my summary). If you need something missing,
   ask me for that specific command's output — do not assume.
6. Judge each DoD condition against the raw output, then SEAL a verdict:
   - PASS — every in-scope DoD condition met (incl. restore-point #3 + BOM #4), shown in raw output.
   - FAIL — one or more not met (name which + the evidence).
   - INCONCLUSIVE — the output doesn't let you decide; say exactly what's missing.
7. REQUIRED OUTPUT FORMAT — your verdict is NOT accepted as free-form prose. The FIRST
   thing in your reply MUST be the SEALED ONE-LINE RECORD, alone, in a fenced block, in
   EXACTLY this shape (same envelope the per-story handover uses, with a `phase 2` subject
   so it is unambiguous in the RUNBOOK):

   ```
   <PASS|FAIL|INCONCLUSIVE> — phase 2 gate: <what was checked / what failed / what's missing>, <YYYY-MM-DD>, confirmed by <who>
   ```

   Examples (shape only):
   - `PASS — phase 2 gate: live pdlv-promotion-pipeline-stack tagged Project=PDE, pdlv-gate-probe held AwaitSandboxApproval under least privilege, 62 offline invariants + self-test, restore point + BOM reconciled, 2026-10-03, confirmed by Independent Validator`
   - `FAIL — phase 2 gate: live stack missing Project=PDE tag (describe-stacks Tags=[]), 2026-10-03, confirmed by Independent Validator`
   - `INCONCLUSIVE — phase 2 gate: launch pad not bootstrapped (PHASE-2 LAUNCH-PAD VERIFY not PASS), nothing judged, 2026-10-03`

   AFTER that one-line block you may add your per-arm narrative + the raw-evidence
   references as supporting detail — but the one-liner leads, and it is the only thing the
   executor transcribes verbatim into the ledger. A verdict delivered WITHOUT this leading
   one-line block is INCOMPLETE — the executor will ask you to re-seal in-format rather than
   paraphrase your prose (the ledger must carry the sealed line, not an executor summary).

# RULES
- You author the DoD; you do NOT accept a rubric from the builder.
- Your SEALED VERDICT MUST lead with the one-line record block of step 7, verbatim-ready —
  not a prose paragraph the executor has to distil. Same format as a story verdict, with the
  `phase 2 gate:` subject.
- "Each story passed" is NOT a phase pass — judge the integrated live control plane.
- A phase gate is NOT passed until its RESTORE POINT is validated (#3) AND its BOM is
  reconciled against live AWS (#4), not just its behaviour.
- Treat the deferred live cross-account assume (VD-3b) as correctly out of scope — attack
  everything else (least privilege, the probe's non-promotability, the production pipeline's
  lack of a bypass, naming/tagging).
- Judge only from the RAW live output on the real system (and, for the committed template,
  its offline proof) — not from anyone's assurance.
- If this reached you curated by the builder rather than from the repo/stakeholder, say so
  and refuse — the inputs must come from the stakeholder/repo.
```

---

> **After the verdict:** the **executor** pastes the sealed one-line record into
> `governance/RUNBOOK.md` and reconciles the Phase-2 close — confirm `restore/phase-2-green`
> is complete (code tag + a captured, verified state manifest, clearing OD-010), the BOM §2
> inventory matches live AWS, and flip the Progress-Summary Phase-2 row ✅ (clearing OD-011).
> `check_docs.py` CHECK N hard-checks that a ✅ phase has its restore point recorded in
> BOM.md. The validator never edits the RUNBOOK; the executor never authors the DoD. A
> FAIL/INCONCLUSIVE opens a remediation item — it does not silently close the phase.
