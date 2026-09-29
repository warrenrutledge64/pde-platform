# Instructions for AI assistants (Gemini)

**Read [`AGENTS.md`](AGENTS.md) at the repository root and follow it fully.**

This project runs on a validation-gated, one-story-at-a-time operating system.
`AGENTS.md` is the entrypoint: it defines the session ritual, the binding
Validation & Advancement Gate, and the hard rules. In particular:

- "Done" means **validated live and recorded** in `governance/RUNBOOK.md` — never
  on inference, never because code merged.
- Run the **session ritual** first: close out the prior story, then check the
  **advancement gate** (a story cannot start until every dependency is ✅).
- **Never self-certify** a story done — the human validates, you record the result.
- **Never push to `main`** directly; branch + pull request only.
- End every session with a **warm handoff**: author the next story's brief + prompt
  with real Lessons Learned.

If you are acting as the strategic **planner** (deciding what to build next and
why), your plans still flow through `AGENTS.md`'s ritual and the RUNBOOK as the
source of truth. See `AGENTS.md` for the full operating system.
