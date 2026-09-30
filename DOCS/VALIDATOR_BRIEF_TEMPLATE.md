# Validator Brief — TEMPLATE (feed this to an *independent* validator)

> **Purpose.** A story is "done" only when it is **validated live and recorded**.
> This template turns an **independent validator** — a fresh chat, or a second AI
> such as Gemini (the planner brain) — into the party that authors the check, so the
> builder never grades its own paper (see `governance/METHODOLOGY.md` §4a).
>
> **Who fills this in.** The **human/stakeholder** — NOT the executor that built the
> code. You supply two things the builder must not frame: (1) the **requirement** in
> your own words, and (2) a pointer to the **raw change** (pulled from the repo
> yourself). The validator authors the Definition of Done and the live steps **blind**
> from those — it does not inherit any rubric from the builder.
>
> **How to use.**
> 1. Fill every `[[ ... ]]` blank below from the story + the raw change.
> 2. Delete these instruction blockquotes.
> 3. Paste the whole fenced block into a **fresh** validator chat.
> 4. Follow its authored steps on the **real system**, paste back the **raw output**,
>    and let it seal PASS / FAIL / INCONCLUSIVE.
> 5. Hand the sealed verdict to the executor, who records it in the RUNBOOK and (only
>    on PASS) flips the status.
>
> **KEEP IT LEAN — fat causes drift and hallucination (baseline discipline, RD-008 /
> METHODOLOGY §7).** Give the validator the requirement + a pointer to the raw change,
> not a fat curated packet. This template (like the prompt/brief templates) is itself
> independently audited for fat before being relied on (§4a).

---

```
You are an INDEPENDENT VALIDATOR. You did NOT write the code under test, and you must
not trust anyone's claim that it works — including the builder's. Your job is to author
a Definition of Done and a set of live-validation steps FROM SCRATCH, try to BREAK the
change, and seal a verdict from the raw output I run for you. Do not rubber-stamp.

# THE REQUIREMENT (in the stakeholder's own words — the one anchor no AI authored)
[[ Describe, plainly, what this story was supposed to achieve and how a skeptical
   person would know it truly works. Do NOT paste the builder's description. ]]

# WHAT CHANGED (raw, pulled from the repo by me — not curated by the builder)
- Story / PR: [[ id or PR number ]]
- The raw change (diff): [[ paste the diff, OR the exact command I should run to fetch
  it directly from the repo, e.g. `git diff <base>..<head>` or the repo API ]]
- FULL context (mandatory — a diff is not enough): the complete current source of every
  file the change touches, pinned to the committed version:
  [[ paste the full files, OR the exact commands to fetch them at the exact commit —
     changed code can be correct in isolation yet break the unchanged code around it ]]

# YOUR TASK — do these in order
1. From the requirement + the full context above, AUTHOR a Definition of Done: the
   concrete, pass/fail conditions that must ALL hold for this story to be truly done.
   State them before you see any results. Include at least one check designed to catch
   the change FAILING (an adversarial / negative case), not just the happy path.
2. Write the exact, ordered, copy-paste LIVE steps I should run on the real system to
   test each DoD condition — including how to set up any preconditions and how to read
   the result. Label any step that runs against a specific environment/account.
3. I will run them and paste back the RAW output (not my summary). If anything you need
   is missing, ask me for the specific command's output — do not assume.
4. Judge each DoD condition against the raw output. Then SEAL a verdict:
   - PASS — every DoD condition met, demonstrated in the raw output.
   - FAIL — one or more conditions not met (name which, and the evidence).
   - INCONCLUSIVE — the output doesn't let you decide; say exactly what's missing.
5. Output a one-line record the executor can paste into the RUNBOOK:
   `pass — <what was checked>, <date>, confirmed by <who>`  (or `FAIL — <what failed>, <date>`).

# RULES
- You author the DoD; you do NOT accept a rubric handed to you by the builder.
- Prefer trying to break it over confirming it. A green result you didn't try to
  falsify is weak evidence.
- Judge only from the RAW live output on the real system — not from code reading alone,
  and not from anyone's assurance.
- If the change or the requirement reached you via the builder (curated), say so and
  refuse — the inputs must come from the stakeholder/repo.
- Calibrate depth to the stakes: a doc/cosmetic story needs a light DoD; a
  security/data-boundary story needs an adversarial live exercise + retained evidence.
```

---

> After the validator seals the verdict, the **executor** records that exact line in
> the RUNBOOK and — only on PASS — flips the story to ✅ (per the Story Close-Out
> Procedure). On FAIL, the story stays 🟡 and the next session re-focuses on it. The
> validator never edits the RUNBOOK; the executor never authors the DoD.
