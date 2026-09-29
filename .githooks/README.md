# Git hooks (opt-in)

Repo-tracked hooks that keep the generated structure map fresh.

## Install (once per clone)

```bash
git config core.hooksPath .githooks
```

Points git at this directory. Nothing is installed globally; no file outside the
repo is touched.

## What runs

- **`pre-commit`** — runs [`scripts/check_repo_map.py`](../scripts/check_repo_map.py)
  and blocks the commit if `docs/REPO_MAP.md` is stale or an annotation is broken. It
  is a **silent PASS until a map is adopted**, so it never blocks a fresh checkout.

## Bypass

`git commit --no-verify` skips the hook. Use sparingly and only when you understand
why the gate is complaining.
