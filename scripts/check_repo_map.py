#!/usr/bin/env python3
"""Gate: the generated repo structure map is accurate and fresh.

Standalone counterpart to the ZTIE-Issues ``check_docs.py`` CHECK M, shipped in
the project-os template so every effort inherits a drift-proof structure map from
day one. It governs the two ways ``docs/REPO_MAP.md`` can lie:

  1. ANNOTATION DRIFT -- a role/group label in ``docs/repo-map.annotations.json``
     targets a path that no longer exists in the tree.
  2. STALE MAP -- the committed ``docs/REPO_MAP.md`` differs from a fresh
     regeneration at the current tree.

Portable + fail-open on absence: if the map artifacts are not present yet (a fresh
template checkout), this is a silent PASS -- adopting the map is opt-in. Once
``docs/REPO_MAP.md`` exists, the gate enforces freshness.

Usage:
    python3 scripts/check_repo_map.py            # check the current repo (cwd/HEAD)
    python3 scripts/check_repo_map.py --repo .   # explicit

Exit codes:
    0  PASS (map fresh, or map not adopted yet)
    1  FAIL (annotation drift and/or stale map)
    2  usage / environment error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# gen_repo_map.py lives beside this file in scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import gen_repo_map as repo_map
except ImportError:
    sys.exit("error: scripts/gen_repo_map.py not found next to this checker")


def _map_body(text: str) -> str:
    """Drop the volatile header lines (ref/sha/tip-commit) so the freshness
    comparison is over structure + interpretation, not the moving commit pointer."""
    return "\n".join(
        line
        for line in text.splitlines()
        if not line.startswith("> **Repo:**")
        and not line.startswith("> **Tip commit:**")
    )


def check(repo_root: Path) -> list[str]:
    """Return a list of human-readable problem strings (empty == PASS)."""
    map_path = repo_root / "docs" / "REPO_MAP.md"
    ann_path = repo_root / "docs" / "repo-map.annotations.json"
    if not map_path.exists():
        return []  # map not adopted yet -> nothing to enforce

    try:
        # Compare against the INDEX (what the commit will contain), so the gate and
        # a --staged regeneration agree and the map never lags by its own new files.
        entries = repo_map.read_index(repo_root)
    except SystemExit:
        # git unavailable / not a repo: cannot verify, do not block.
        return []

    problems: list[str] = []
    ann = None
    if ann_path.exists():
        ann = repo_map.load_annotations(ann_path)
        for warning in repo_map.validate_annotations(ann, entries):
            problems.append(f"annotation drift: {warning}")

    short_sha, subject = repo_map.resolve_ref(repo_root, "HEAD")
    struct = repo_map.analyze(entries)
    name = repo_map._repo_name(repo_root)
    warnings = repo_map.validate_annotations(ann, entries) if ann else []
    fresh = repo_map.render(name, "main", short_sha, subject, struct, entries, ann, warnings)
    committed = map_path.read_text(encoding="utf-8")
    if _map_body(committed) != _map_body(fresh):
        problems.append(
            "stale map: docs/REPO_MAP.md differs from a fresh regeneration -- re-run "
            "`python3 scripts/gen_repo_map.py --ref HEAD --ref-label main "
            "--annotations docs/repo-map.annotations.json -o docs/REPO_MAP.md`"
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="path to the git repo (default: cwd)")
    args = parser.parse_args(argv)
    problems = check(Path(args.repo))
    if problems:
        print(f"check_repo_map: FAIL -- {len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("check_repo_map: PASS -- repo structure map is accurate and fresh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
