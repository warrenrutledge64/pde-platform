# Copilot / AI instructions

**Read [`AGENTS.md`](../AGENTS.md) at the repository root and follow it fully.**

This project runs on a validation-gated, one-story-at-a-time operating system
defined in `AGENTS.md`. Key rules:

- "Done" means **validated live and recorded** in `governance/RUNBOOK.md` — not
  merged, not inferred.
- Run the **session ritual** first: close out the prior story, then check the
  **advancement gate** (a story cannot start until every dependency is ✅).
- **Never self-certify** a story done — the human validates, you record the result.
- **Never push to `main`** directly; branch + pull request only.
- End every session with a **warm handoff**: author the next story's brief + prompt
  with real Lessons Learned.

`AGENTS.md` has the complete operating system and the reading order.
