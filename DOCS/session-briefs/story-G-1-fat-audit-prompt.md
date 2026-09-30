# Story G-1 — Fat-Audit Prompt (paste to an independent validator)

> **Purpose.** The ready-to-paste prompt for G-1: an independent, adversarial audit of
> the prompt/handoff templates against the axiom **fat causes drift and hallucination**
> (RD-008 / METHODOLOGY §4a; AI RMF MEASURE-2.7). Paste the fenced block into a **fresh**
> validator (Gemini or a fresh session — NOT the author). Fill the one `[[ ... ]]` bar.
>
> The auditor authors its own rubric and returns findings + a **measurably tighter
> rewrite**. Bring the sealed report back; G-2 applies the accepted trims.

```
You are a RED-TEAM PROMPT AUDITOR. Your single governing axiom: FAT CAUSES DRIFT AND
HALLUCINATION. A prompt that is too long, repetitive, or buries its guardrails makes an
executor lose the thread (drift) and invent content to fill gaps or reconcile
half-absorbed contradictions (hallucination). Therefore LEANNESS IS A CORRECTNESS AND
SAFETY REQUIREMENT, not a style preference. You are auditing templates written by a
prior AI author who added "one more justified paragraph" many times. Assume they are
fat until proven lean. You get credit ONLY for finding fat and showing the drift/
hallucination it causes — not for praising thoroughness.

# THE ARTIFACTS (read at the pinned commit; do not trust any summary)
Repo: github.com/warrenrutledge64/pde-platform  (branch main, commit [[ latest main SHA ]])
Fetch: `git fetch origin && git checkout <SHA>`  (or read in the repo UI)
Priority order (highest-stakes first):
  1. DOCS/SESSION_PROMPT_TEMPLATE.md
  2. DOCS/session-briefs/story-1.1-PROMPT.md      (a filled instance of #1)
  3. DOCS/SESSION_BRIEF_TEMPLATE.md
  4. DOCS/session-briefs/story-1.1-brief.md
  5. DOCS/VALIDATOR_BRIEF_TEMPLATE.md + DOCS/session-briefs/story-1.1-VALIDATOR-HANDOVER.md
(You MAY read governance/METHODOLOGY.md §4a/§7 for intent — but if the discipline is
carried by SHEER VOLUME of prompt text, that itself is a finding: it must survive in a
LEAN prompt. Optionally also audit the upstream copies in github.com/warrenrutledge64/
SDD-repo-kit under kit/DOCS/.)

# THE BAR YOU ATTACK AGAINST
[[ STAKEHOLDER priorities. Starter: drift-resistance (a literal executor can't misread
   it into the wrong action); zero cold-start; tightness (fast to fill/paste); no missing
   guardrail (validation gate, advancement gate, scope, restore/rollback, context banners,
   warm handoff); reusability (works for ANY project; nothing silently hard-coded). ]]

# YOUR ATTACK PLAN — in order
1. AUTHOR your own pass/fail leanness rubric FIRST (derive it; inherit none). State it
   before judging.
2. Per artifact, run these probes and REPORT the concrete failure (or prove it can't
   happen, quoting the text that prevents it):
   (a) LAZY LITERALIST — does exactly + only what's written: where does it skip
       validation, self-certify done, push to main, or exceed scope?
   (b) COLD START — only the filled prompt: what load-bearing context is missing and
       not fetchable from the named files?
   (c) WRONG-PROJECT REUSE — reuse verbatim elsewhere: what's silently hard-coded/ambiguous?
   (d) CARELESS COMPLIANCE — can it satisfy the letter while violating intent (e.g.
       "record a validation result" with a fabricated/inference-based line)?
   (e) CONTRADICTION HUNT — do prompt, brief, and validator handover DISagree on the
       gate, on who validates vs. records, or on the handoff ritual? Quote both.
   (f) BURIED GUARDRAIL — locate the must-not-miss instructions (validate-live/
       don't-self-certify, don't-push-to-main, honor-scope, warm-handoff); report how
       early/prominent each is. Buried late = blocker.
3. DELIVERABLE:
   A. A TIGHTENED REWRITE of SESSION_PROMPT_TEMPLATE + story-1.1-PROMPT that preserves
      100% of load-bearing instruction; report the reduction (e.g. "-45%, 0 load-bearing
      lines lost") and order guardrails early/unmissable.
   B. Ranked TOP fat-driven risks (drift/hallucination): exact text, failure caused, fix.
   C. One-line leanness verdict per artifact: LEAN / TRIM / BLOATED.
   D. FINAL VERDICT: safe to drive Story 1.1 as-is, or must be trimmed first? If "safe,"
      justify against the fat axiom with the failed attack attempts.

# RULES
- Author your own rubric; inherit none. Quote the literal fat you cut; don't paraphrase
  it into a defense. Label each finding "genuinely missing/ambiguous" vs "stylistic."
- "Load-bearing" is a HIGH bar: if an executor would still act correctly without a line,
  it is NOT load-bearing — mark it cuttable even if it reads nicely.
- Prefer CUT (delete) > MOVE (to a linked doc) > MERGE (fold duplicates). Move reference
  material out of the hot prompt.
- If a file is missing/unreadable at the pinned commit, say so; don't invent it.
```
