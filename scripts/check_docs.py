#!/usr/bin/env python3
"""Governance-doc consistency gate (generic).

Enforces the parts of the "work-like-this" operating system that a machine can
check, so the ledger never quietly lies. Portable + fail-open: every check is a
no-op when the file it inspects is absent, so this runs safely in a repo that has
only partially adopted the kit.

Checks:
  CHECK G  -- a ✅ (done) story in governance/RUNBOOK.md has no recorded, dated
              `Validation Result` line. "Done" must rest on a recorded pass.
  CHECK S  -- a story's status glyph in the RUNBOOK summary table disagrees with
              the glyph in that story's detail-block header. The two views must
              tell the same story so the ledger never half-lies.
  CHECK P  -- a stray ``{{placeholder}}`` left in a LIVING governance doc
              (RUNBOOK / PROJECT_PLAN / BOM / RESTORE / METHODOLOGY). Templates
              under DOCS/ are exempt (placeholders are expected there).
  CHECK L  -- a repo-relative ``*.md`` link in a governance doc whose target does
              not exist on disk (a dangling link).
  CHECK M  -- (if the repo-map is adopted) docs/REPO_MAP.md is stale or an
              annotation targets a missing path. Delegates to check_repo_map.

Usage:
    python3 scripts/check_docs.py                 # check cwd
    python3 scripts/check_docs.py --repo-root .   # explicit

Exit codes:
    0  PASS
    1  FAIL (one or more violations)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# The living governance docs placeholders must be filled in (unlike the DOCS/
# templates, where {{...}} is expected).
LIVING_DOCS = ("RUNBOOK.md", "PROJECT_PLAN.md", "BOM.md", "RESTORE.md", "METHODOLOGY.md")
DONE = "\u2705"  # ✅
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

# The four story-status glyphs of the operating system's state machine.
STATUS_GLYPHS = ("\u2b1c", "\U0001f7e1", "\u26d4", "\u2705")  # ⬜ 🟡 ⛔ ✅
# A story id like "1.1" or "4.4a" (optional trailing letter for sub-stories).
_STORY_ID = r"\d+\.\d+[a-z]?"
# Summary-table row:  | 1.1 | title... | deps | <glyph> | completed | tag |
STORY_ROW_RE = re.compile(r"^\|\s*(" + _STORY_ID + r")\s*\|.*$")
# Detail-block header: **1.1 — Title**  <glyph> _Label_   (may carry a suffix)
STORY_HEADER_RE = re.compile(r"^\*\*(" + _STORY_ID + r")\b.*?\*\*\s*(.*)$")


@dataclass
class Violation:
    check: str
    file: str
    detail: str

    def render(self) -> str:
        return f"[{self.check}] {self.file}: {self.detail}"


def _governance_dir(repo_root: Path) -> Path:
    """Governance docs live under governance/ once installed; fall back to root."""
    gov = repo_root / "governance"
    return gov if gov.exists() else repo_root


def check_g_done_without_validation(gov_dir: Path) -> list[Violation]:
    """A ✅ story row must carry a dated Validation Result somewhere nearby."""
    runbook = gov_dir / "RUNBOOK.md"
    if not runbook.exists():
        return []
    text = runbook.read_text(encoding="utf-8")
    violations: list[Violation] = []
    # Heuristic: for every detail block header marked ✅ Done, require a
    # "Validation Result:" line that is not the literal "pending" placeholder.
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if DONE in line and "Done" in line and line.lstrip().startswith(("**", "#")):
            window = "\n".join(lines[i : i + 12])
            m = re.search(r"Validation Result:\**\s*(.+)", window)
            if not m or "pending" in m.group(1).lower() or not m.group(1).strip():
                header = line.strip().strip("*# ")
                violations.append(
                    Violation(
                        "CHECK G",
                        "RUNBOOK.md",
                        f"story '{header[:60]}' is ✅ but has no recorded, dated "
                        "Validation Result (a done story must rest on a recorded pass)",
                    )
                )
    return violations


def _first_glyph(text: str) -> str | None:
    """Return the first status glyph found in ``text`` (left to right), or None."""
    best_pos = len(text) + 1
    best: str | None = None
    for g in STATUS_GLYPHS:
        i = text.find(g)
        if i != -1 and i < best_pos:
            best_pos, best = i, g
    return best


def check_s_status_consistency(gov_dir: Path) -> list[Violation]:
    """A story's summary-table glyph must match its detail-block header glyph.

    The RUNBOOK states each story's status twice -- once as a cell in the phase
    summary table, once in the story's detail-block header. When those two drift
    apart the ledger half-lies (the exact defect that let a whole runbook read
    "Not Started" in its tables while every detail header said "In Progress").
    """
    runbook = gov_dir / "RUNBOOK.md"
    if not runbook.exists():
        return []
    lines = runbook.read_text(encoding="utf-8").splitlines()

    table_status: dict[str, str] = {}
    header_status: dict[str, str] = {}

    for line in lines:
        m = STORY_ROW_RE.match(line)
        if m:
            # Status is the first glyph in the row's cells after the id cell.
            after_id = line.split("|", 2)[2] if line.count("|") >= 2 else line
            g = _first_glyph(after_id)
            if g is not None:
                # First row for an id wins (defensive against duplicate ids).
                table_status.setdefault(m.group(1), g)
            continue
        h = STORY_HEADER_RE.match(line)
        if h:
            g = _first_glyph(h.group(2))
            if g is not None:
                header_status.setdefault(h.group(1), g)

    violations: list[Violation] = []
    for sid in sorted(set(table_status) & set(header_status)):
        t, hh = table_status[sid], header_status[sid]
        if t != hh:
            violations.append(
                Violation(
                    "CHECK S",
                    "RUNBOOK.md",
                    f"story {sid}: summary-table status '{t}' disagrees with "
                    f"detail-block header status '{hh}' (the two views must match)",
                )
            )
    return violations


def check_p_stray_placeholders(gov_dir: Path) -> list[Violation]:
    """No {{placeholder}} left in a living governance doc."""
    violations: list[Violation] = []
    for name in LIVING_DOCS:
        path = gov_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        found = sorted(set(PLACEHOLDER_RE.findall(text)))
        if found:
            sample = ", ".join(found[:5])
            violations.append(
                Violation(
                    "CHECK P",
                    name,
                    f"unfilled placeholder(s) remain: {sample}"
                    + (" …" if len(found) > 5 else ""),
                )
            )
    return violations


def check_l_dangling_links(gov_dir: Path, repo_root: Path) -> list[Violation]:
    """A repo-relative *.md link in a governance doc must resolve on disk."""
    violations: list[Violation] = []
    for name in LIVING_DOCS:
        path = gov_dir / name
        if not path.exists():
            continue
        for target in MD_LINK_RE.findall(path.read_text(encoding="utf-8")):
            link = target.split("#", 1)[0].strip()
            if not link or link.startswith(("http://", "https://", "mailto:")):
                continue
            if not link.endswith(".md"):
                continue
            resolved = (path.parent / link).resolve()
            if not resolved.exists():
                violations.append(
                    Violation("CHECK L", name, f"dangling link -> {target}")
                )
    return violations


def check_m_repo_map(repo_root: Path) -> list[Violation]:
    """Delegate to check_repo_map if present + adopted."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import check_repo_map
    except ImportError:
        return []
    return [
        Violation("CHECK M", "docs/REPO_MAP.md", p)
        for p in check_repo_map.check(repo_root)
    ]


def run_checks(repo_root: Path) -> list[Violation]:
    gov = _governance_dir(repo_root)
    out: list[Violation] = []
    out += check_g_done_without_validation(gov)
    out += check_s_status_consistency(gov)
    out += check_p_stray_placeholders(gov)
    out += check_l_dangling_links(gov, repo_root)
    out += check_m_repo_map(repo_root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=".", help="repo root to check (default: cwd)")
    args = parser.parse_args(argv)
    violations = run_checks(Path(args.repo_root))
    if violations:
        print(f"check_docs: FAIL -- {len(violations)} violation(s):")
        for v in violations:
            print(f"  {v.render()}")
        return 1
    print("check_docs: PASS -- governance docs are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
