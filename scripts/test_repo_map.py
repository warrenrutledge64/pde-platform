#!/usr/bin/env python3
"""Self-contained tests for the repo-map kit (generator + gate).

Run:  python3 -m unittest scripts.test_repo_map   (from the repo root)
  or: python3 scripts/test_repo_map.py

Stdlib only. Each test builds a throwaway git repo in a tempdir so the generator
and gate exercise a real ``git ls-tree``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_repo_map
import gen_repo_map


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _seed_repo(root: Path) -> None:
    """Create a small committed repo with a couple of directories + files."""
    (root / "src").mkdir(parents=True)
    (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")


def _regen_map_staged(root: Path, annotations: Path | None = None) -> None:
    """Write docs/REPO_MAP.md from the git INDEX (staged) tree, labelled 'main'.

    Uses read_index so the map reflects what the next commit will contain -- the
    same view the gate compares against -- so no amend dance is needed.
    """
    entries = gen_repo_map.read_index(root)
    short_sha, subject = gen_repo_map.resolve_ref(root, "HEAD")
    struct = gen_repo_map.analyze(entries)
    name = gen_repo_map._repo_name(root)
    ann = gen_repo_map.load_annotations(annotations) if annotations else None
    warnings = gen_repo_map.validate_annotations(ann, entries) if ann else []
    text = gen_repo_map.render(name, "main", short_sha, subject, struct, entries, ann, warnings)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "REPO_MAP.md").write_text(text, encoding="utf-8")


def _write_fresh_map(root: Path, annotations: Path | None = None) -> None:
    """Adopt docs/REPO_MAP.md in a single commit using the --staged view.

    Stage the map placeholder, regenerate from the index (which now includes the
    map path), stage again, and commit once -- the index view already counts the
    map file, so the committed map matches its own tree with no amend.
    """
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "REPO_MAP.md").write_text("placeholder\n", encoding="utf-8")
    _git(root, "add", "-A")
    _regen_map_staged(root, annotations)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "map")


class GeneratorTests(unittest.TestCase):
    def test_maps_real_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            entries = gen_repo_map.read_tree(root, "HEAD")
            struct = gen_repo_map.analyze(entries)
            names = {n.name for n in struct.top_dirs}
            self.assertIn("src", names)
            self.assertIn("README.md", struct.root_files)

    def test_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            out1 = gen_repo_map.main(["--repo", str(root), "--ref", "HEAD"])
            out2 = gen_repo_map.main(["--repo", str(root), "--ref", "HEAD"])
            self.assertEqual(out1, 0)
            self.assertEqual(out2, 0)

    def test_repo_name_without_origin_remote(self) -> None:
        """Regression: _repo_name must not abort when there is no origin remote."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            # No remote configured -> falls back to the directory name.
            self.assertEqual(gen_repo_map._repo_name(root), root.name)

    def test_index_includes_staged_but_uncommitted_files(self) -> None:
        """read_index reflects staged files that HEAD does not yet contain."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            (root / "staged_only.txt").write_text("s\n", encoding="utf-8")
            _git(root, "add", "staged_only.txt")
            index_paths = {e.path for e in gen_repo_map.read_index(root)}
            head_paths = {e.path for e in gen_repo_map.read_tree(root, "HEAD")}
            self.assertIn("staged_only.txt", index_paths)
            self.assertNotIn("staged_only.txt", head_paths)


class GateTests(unittest.TestCase):
    def test_fresh_map_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            _write_fresh_map(root)
            self.assertEqual(check_repo_map.check(root), [])

    def test_no_map_is_silent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            # No docs/REPO_MAP.md committed -> gate is a silent PASS (opt-in).
            self.assertEqual(check_repo_map.check(root), [])

    def test_stale_map_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            _write_fresh_map(root)
            # Add a new tracked dir/file without regenerating the map.
            (root / "newpkg").mkdir()
            (root / "newpkg" / "m.py").write_text("y = 2\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "add pkg")
            problems = check_repo_map.check(root)
            self.assertTrue(any("stale map" in p for p in problems), problems)

    def test_annotation_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_repo(root)
            ann = root / "docs" / "repo-map.annotations.json"
            (root / "docs").mkdir(exist_ok=True)
            ann.write_text(json.dumps({"roles": {"src": "code"}}), encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "ann")
            _write_fresh_map(root, annotations=ann)
            # Now point an annotation at a path that does not exist.
            ann.write_text(
                json.dumps({"roles": {"src": "code", "ghost": "bogus"}}), encoding="utf-8"
            )
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "break ann")
            problems = check_repo_map.check(root)
            self.assertTrue(any("annotation drift" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
