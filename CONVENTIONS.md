# Conventions for AI assistants

**Read [`AGENTS.md`](AGENTS.md) at the repository root and follow it fully.**

(Aider and some other tools read a `CONVENTIONS.md` file. This one simply routes
you to the real entrypoint.)

This project runs on a validation-gated, one-story-at-a-time operating system.
Key rules from `AGENTS.md`:

- "Done" means **validated live and recorded** in `governance/RUNBOOK.md` — not
  merged, not inferred.
- Run the **session ritual** first: close out the prior story, then check the
  **advancement gate** (a story cannot start until every dependency is ✅).
- **Never self-certify** a story done — the human validates, you record.
- **Never push to `main`** directly; branch + pull request only.
- End every session with a **warm handoff** (next story's brief + prompt, real
  Lessons Learned).

`AGENTS.md` has the complete operating system and the reading order.
