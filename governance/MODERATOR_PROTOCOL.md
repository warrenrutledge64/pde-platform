# MODERATOR_PROTOCOL.md — Copilot's mechanical gates

> **This file defines the Moderator seat's gates.** In the Split-Gauge operating
> model (see [`AGENTS.md`](AGENTS.md)), Copilot is the **Moderator**: a mechanical
> gatekeeper that runs *before* independent validation and **refuses to let a
> validation run start against the wrong target.** It does not judge whether the
> deliverable is correct — that is the Validator's job (Gemini, blind) and the
> Human's (reading raw output). The Moderator's single purpose is to make a class
> of *execution failures* impossible to start:
>
> - **stale infrastructure** (the live resource was never redeployed from the
>   branch under test),
> - **missing secrets** (a required secret/parameter is absent or still a
>   placeholder),
> - **wrong account** (the operator is pointed at the wrong AWS account/region),
> - **non-deployed code** (the branch's template was never applied to the target).
>
> Every one of those produces a verdict that *looks real but tested nothing*
> (see [`METHODOLOGY.md`](METHODOLOGY.md) §7, and the Story 2.3 / Story 3.2
> histories in [`RUNBOOK.md`](RUNBOOK.md)). The durable fix for a repeatedly-skipped
> prose precondition is a **mechanical check**, not more prose — that is what these
> gates are.
>
> **Scope.** Governance definition only. This file specifies *what each gate must
> prove and its stop semantics*; it does not change pipeline execution logic. The
> concrete per-story checks (e.g.
> [`../scripts/preflight_story_3_2.py`](../scripts/preflight_story_3_2.py)) are the
> mechanical instances of these gate definitions.

---

## Principles (apply to every gate)

- **Mechanical, not judgmental.** A gate reads the *actual live state* (or the
  *actual branch/PR head*) and compares it to an expected baseline. It never
  interprets correctness, never authors a Definition of Done, and never seals a
  verdict.
- **Fail-closed, non-zero exit.** A gate's default answer is **STOP**. It passes
  only when it affirmatively proves its precondition; any uncertainty
  (unreadable resource, missing credential) exits non-zero. There is no "probably
  fine."
- **Checkout-proof where possible.** Prefer reading the exact PR head in CI over a
  hand-pasted clone — a human clone/checkout is the single most common way a
  validation cycle is wasted (wrong repo, a literal `<TOKEN>` placeholder the shell
  mis-parses, or a stale pre-fix commit).
- **Marker-based, not deploy-line-based.** To prove "the branch is live," a gate
  reads a **branch-specific marker** off the deployed resource (a new tag/version/
  policy statement/env var) — never the green deploy line, which lies when the
  wrong checkout was deployed.
- **Offline self-test.** Every mechanical gate ships a `--self-test` that proves it
  would catch the exact stale/wrong state it exists to block, with no live calls.
- **Produces a record, blocks on red.** A gate emits a dated pass/stop record the
  Builder and Human can read; a red gate is a **hard stop** — validation does not
  start (see [`AGENTS.md`](AGENTS.md) §5).

**Exit code contract (uniform across gates):**

| Exit | Meaning | Next action |
|:----:|---------|-------------|
| `0` | Precondition proven — safe to proceed to the next gate / to validation. | Continue. |
| `1` | Precondition **violated** (stale / missing / wrong / non-deployed). | **STOP.** Fix the target, re-run the gate. Do **not** validate. |
| `2` | Could not read a required input (credentials / unreadable resource). | **STOP.** Environment issue — resolve access, re-run. Not a verdict. |

---

## The four gates (run in order)

```
 Pre-Execution Gate  →  Deployment Gate  →  Preflight Gate  →  Live Result Gate
   (before deploy)       (deploy proven)     (live matches)     (output usable)
        │                     │                   │                   │
        └── wrong branch /    └── branch not      └── stale infra /   └── verdict
            missing secret /      actually            wrong account       judged
            armed gate            applied                                 stale output
```

Each gate is a precondition for the next. A red gate stops the chain; later gates
do not run until the earlier one is green.

---

### Gate 1 — Pre-Execution Gate

**Runs:** before any deploy or validation, on the branch/PR about to be exercised.

**Blocks:** missing secrets, placeholder values, a wrong-branch checkout, and
merging/validating while the gate is ARMED.

**Proves (all must hold):**
- The working tree is a real clone of the **correct repo** on the **expected
  branch** at a known head (`git rev-parse HEAD` resolves; the remote is the
  intended GitHub repo, not a stale/mis-typed URL).
- Every **required secret / SSM parameter** named by the story is **present and not
  a placeholder** — no `<paste-...>`, `<TOKEN>`, `YOUR_...`, `{{...}}`, or empty
  value survives.
- The **Validation & Advancement gate state** in [`RUNBOOK.md`](RUNBOOK.md) is
  consistent with the action (e.g. not merging a deliverable while the gate is
  **ARMED** — delegates to
  [`../scripts/check_merge_order.py`](../scripts/check_merge_order.py)).

**Stops on:** a placeholder secret, an unreadable/missing parameter, a checkout on
the wrong repo or branch, or an ARMED-gate deliverable merge.

---

### Gate 2 — Deployment Gate

**Runs:** immediately after the deploy step, before the live resource is exercised.

**Blocks:** non-deployed code — the "green deploy line but nothing changed" trap.

**Proves (all must hold):**
- The branch's template(s) were **actually applied** to the target (the stack
  reached a terminal success state — e.g. `CREATE_COMPLETE` / `UPDATE_COMPLETE` —
  and is **not** stuck in `ROLLBACK_COMPLETE` or a `*_FAILED` state).
- No **dead stack** blocks the deploy: a `ROLLBACK_COMPLETE` / `*_FAILED` `pdlv-`
  stack is detected and must be cleaned before the deploy can be considered valid
  (the Story 2.3 dead-stack class — CloudFormation cannot update a
  `ROLLBACK_COMPLETE` stack in place, so a re-deploy silently applies nothing).
- The deployed resource carries the **branch-specific marker** the story
  introduced (a new tag / version / policy statement / env var) — read off the live
  resource, **not** inferred from the deploy's exit code.

**Stops on:** a rolled-back/failed stack, a dead stack left in place, or a live
resource missing the branch marker (i.e. the branch was never really deployed).

---

### Gate 3 — Preflight Gate

**Runs:** after deploy is proven, immediately before the pipeline/validation is
triggered.

**Blocks:** stale infrastructure and wrong-account execution — the live resource
not matching the story's baseline, or the operator pointed at the wrong account.

**Proves (all must hold):**
- The operator's identity is the **expected account/region** for each command block
  (`aws sts get-caller-identity` matches — e.g. Pipeline-Hub `641628980935` for Hub
  reads, the member account for member reads). A banner comment does **not** change
  the account; the gate asserts the real identity.
- The **live resources match the story's baseline, not a prior version** — trust
  relationships, IAM scope, tags, state-machine definition, and any policy the
  story changed are read live and compared to the expected baseline (the
  mechanical instance for Story 3.2 is
  [`../scripts/preflight_story_3_2.py`](../scripts/preflight_story_3_2.py): Hub
  orchestrator trust/boundary + member role tag/scope + state-machine ASL must all
  match the Story-3.2 baseline, else hard-fail).
- No **leftover placeholder** survives on the live resource (e.g. a
  `<paste-the-new-value>` ExternalId, an old `Story=1.1` tag where `Story=3.2` is
  expected).

**Stops on:** a wrong-account identity, a live resource that still reflects a prior
story's shape, or a placeholder/stale value on the deployed thing. A verdict whose
findings all describe a *prior* version of the resource is the signature of this
miss — treat it as an execution failure to re-run, not a deliverable defect.

---

### Gate 4 — Live Result Gate

**Runs:** after the validation steps have been executed live, before the result is
accepted into the record.

**Blocks:** a verdict sealed against stale or unusable output — the result that
"looks real but tested nothing."

**Proves (all must hold):**
- The raw output under judgment came from the **target proven green by Gates 1–3**
  (the pinned head / the marker-verified resource), not a cached, prior, or
  wrong-account run.
- The output is **complete and genuinely exercised** — not a false-negative from an
  absent file or an aborted step (e.g. an adversarial grep returning "none found"
  because the file was never retrieved, not because the code is clean).
- The sealed verdict is one of `PASS` / `FAIL` / `INCONCLUSIVE` and, if the output
  is insufficient to decide, the correct seal is **INCONCLUSIVE / execution
  failure** — never a `PASS` on absence of evidence.

**Stops on:** output that cannot be tied to the proven target, truncated/aborted
runs, or false-negative "clean" readings against absent artifacts.

> The Live Result Gate does **not** author or re-judge the Validator's DoD — it only
> certifies that *what the Validator judged was the real, proven target's real
> output.* The verdict itself remains the Validator's (Gemini, blind), recorded
> verbatim by the Builder.

---

## What the Moderator must never do

- **Never author a Definition of Done or seal a PASS/FAIL/INCONCLUSIVE verdict.**
  That is the Validator seat (Gemini) and the Human. The Moderator only certifies
  preconditions.
- **Never modify a deliverable** (`infra/**`, `scripts/**` logic) to make a gate
  pass. A red gate means *fix the target or the environment*, not *loosen the gate*.
- **Never flip a story status or edit the RUNBOOK.** Only the Builder writes status,
  and only to record a sealed verdict (see [`AGENTS.md`](AGENTS.md) §4.5).
- **Never curate the evidence the Validator sees.** The Validator's inputs come from
  the Human/repo, un-curated (the §4 information barriers in
  [`AGENTS.md`](AGENTS.md)). A moderator-assembled "here's what to look at" packet
  would re-introduce the grading-your-own-paper failure the barriers exist to stop.
- **Never pass on uncertainty.** If a required input can't be read, exit `2` and
  stop — do not assume the precondition holds.

---

## Relationship to the rest of the system

- **[`AGENTS.md`](AGENTS.md)** — defines the Moderator seat and the information
  barriers these gates protect.
- **[`METHODOLOGY.md`](METHODOLOGY.md) §7** — the universal disciplines these gates
  mechanize: *deploy the branch and prove the live resource changed before you
  validate it*, and *when a prose precondition keeps getting skipped, make it
  mechanical.*
- **[`RUNBOOK.md`](RUNBOOK.md)** — the Validation & Advancement Gate state the
  Pre-Execution Gate reads; the source of truth for status (which the Moderator
  never writes).
- **`scripts/`** — the concrete mechanical instances
  ([`../scripts/preflight_story_3_2.py`](../scripts/preflight_story_3_2.py),
  [`../scripts/check_merge_order.py`](../scripts/check_merge_order.py),
  [`../scripts/check_deploy_tags.py`](../scripts/check_deploy_tags.py)). New stories
  add their own gate instances following these four definitions, each shipping an
  offline `--self-test`.

---

*The Moderator does not decide whether the work is good — it guarantees that when
the Validator and the Human decide, they are judging the real, deployed, correct-
account target, and nothing else.*
