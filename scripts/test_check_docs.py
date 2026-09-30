#!/usr/bin/env python3
"""Self-contained tests for the governance-doc consistency gate (check_docs).

Run:  python3 -m unittest scripts.test_check_docs   (from the repo root)
  or: python3 scripts/test_check_docs.py

Stdlib only. Each test builds a throwaway governance/ tree in a tempdir and runs
the individual check functions against it, so the gate is exercised end to end
without touching the real repo.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_docs

# --- runbook fragments -----------------------------------------------------

# A consistent runbook: summary-table row and detail header agree for every id.
CONSISTENT_RUNBOOK = """# Runbook

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 1.1 | Initialize repo | \u2014 | \u2b1c | | |
| 1.2 | Configure tables | 1.1 | \U0001f7e1 | | |
| 1.3 | Ingestion API | 1.2 | \u2705 | 2026-09-28 | |

**1.1 \u2014 Initialize repo**  \u2b1c _Not Started_
- Steps: stand up the skeleton.

**1.2 \u2014 Configure tables**  \U0001f7e1 _In Progress_
- Steps: define schema.

**1.3 \u2014 Ingestion API**  \u2705 _Done (validated)_
- **Validation Result:** pass \u2014 uploaded a resume, 2026-09-28, confirmed by human.
"""

# A drifting runbook: 1.2's table cell says Not Started, its header says In Progress.
DRIFTING_RUNBOOK = CONSISTENT_RUNBOOK.replace(
    "| 1.2 | Configure tables | 1.1 | \U0001f7e1 | | |",
    "| 1.2 | Configure tables | 1.1 | \u2b1c | | |",
)

# A runbook whose real summary table + detail headers agree, but which ALSO has
# an auxiliary "Blocked" table keyed on the same story ids that mentions a glyph in
# PROSE (e.g. "1.1 not yet ✅"). The prose glyph must NOT be read as story status.
AUX_TABLE_PROSE_GLYPH_RUNBOOK = """# Runbook

## Ready-Now / Blocked

| Story | Tier | Blocked on |
|-------|------|------------|
| 1.2 | 2 | 1.1 not yet \u2705 |
| 1.3 | 3 | 1.2 not yet \u2705 |

## Build Tiers

| Tier | Story | Depends on |
|------|-------|-----------|
| 1 | 1.1 | \u2014 |

## Phase 1

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 1.1 | Initialize repo | \u2014 | \u2b1c | | |
| 1.2 | Configure tables | 1.1 | \U0001f7e1 | | |
| 1.3 | Ingestion API | 1.2 | \u2b1c | | |

**1.1 \u2014 Initialize repo**  \u2b1c _Not Started_
- Steps: stand up the skeleton.

**1.2 \u2014 Configure tables**  \U0001f7e1 _In Progress_
- Steps: define schema.

**1.3 \u2014 Ingestion API**  \u2b1c _Not Started_
- Steps: build the API.
"""

# Header carrying a trailing suffix after the status label (as Story 4.4 does).
SUFFIXED_HEADER_RUNBOOK = """# Runbook

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 4.4 | Resume-update flow \u2014 *(proposed)* | 1.3, 4.2 | \u2b1c | | |

**4.4 \u2014 Resume-update flow**  \u2b1c _Not Started_  *(proposed \u2014 planner to ratify)*
- Steps: add the update control.
"""


def _gov(root: Path, runbook: str) -> Path:
    gov = root / "governance"
    gov.mkdir(parents=True)
    (gov / "RUNBOOK.md").write_text(runbook, encoding="utf-8")
    return gov


class StatusConsistencyTests(unittest.TestCase):
    def test_consistent_runbook_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), CONSISTENT_RUNBOOK)
            self.assertEqual(check_docs.check_s_status_consistency(gov), [])

    def test_drift_between_table_and_header_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), DRIFTING_RUNBOOK)
            violations = check_docs.check_s_status_consistency(gov)
            self.assertEqual(len(violations), 1, violations)
            self.assertEqual(violations[0].check, "CHECK S")
            self.assertIn("1.2", violations[0].detail)

    def test_prose_glyph_in_auxiliary_table_is_not_read_as_status(self) -> None:
        """Regression (PDE Story 0.1): a glyph mentioned in PROSE inside a
        Ready-Now/Blocked/Build-Tier table — which is keyed on the same story id
        as the summary table — must not be mistaken for that story's status.

        Before the fix, ``| 1.2 | 2 | 1.1 not yet ✅ |`` injected a ✅ as story
        1.2's 'table status', which then falsely disagreed with 1.2's 🟡 detail
        header. The real summary table + headers here are fully consistent, so the
        check must report NO violations.
        """
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), AUX_TABLE_PROSE_GLYPH_RUNBOOK)
            self.assertEqual(check_docs.check_s_status_consistency(gov), [])

    def test_suffix_after_status_label_is_tolerated(self) -> None:
        """A trailing '*(proposed ...)*' after the glyph must not break parsing."""
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), SUFFIXED_HEADER_RUNBOOK)
            self.assertEqual(check_docs.check_s_status_consistency(gov), [])

    def test_missing_runbook_is_silent_pass(self) -> None:
        """Portable + fail-open: no RUNBOOK.md -> no-op (not a crash)."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "governance").mkdir()
            self.assertEqual(
                check_docs.check_s_status_consistency(Path(tmp) / "governance"), []
            )

    def test_regression_all_headers_in_progress_while_tables_not_started(self) -> None:
        """The original Story-0 defect: every table cell ⬜ but every header 🟡."""
        runbook = CONSISTENT_RUNBOOK
        # Force all three detail headers to In Progress, leave the table as-is.
        runbook = runbook.replace("\u2b1c _Not Started_", "\U0001f7e1 _In Progress_")
        runbook = runbook.replace(
            "\u2705 _Done (validated)_", "\U0001f7e1 _In Progress_"
        )
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), runbook)
            violations = check_docs.check_s_status_consistency(gov)
            details = [v.detail for v in violations]
            # 1.1 (⬜ vs 🟡) and 1.3 (✅ vs 🟡) drift; 1.2 was already 🟡 in both.
            self.assertEqual(len(violations), 2, details)
            self.assertTrue(any(d.startswith("story 1.1:") for d in details), details)
            self.assertTrue(any(d.startswith("story 1.3:") for d in details), details)


class GlyphHelperTests(unittest.TestCase):
    def test_first_glyph_picks_leftmost(self) -> None:
        self.assertEqual(
            check_docs._first_glyph("junk \u2705 then \u2b1c"), "\u2705"
        )

    def test_first_glyph_none_when_absent(self) -> None:
        self.assertIsNone(check_docs._first_glyph("no glyphs here"))

    def test_status_cell_glyph_reads_a_sole_token_cell(self) -> None:
        self.assertEqual(
            check_docs._status_cell_glyph("| 1.1 | Title | \u2014 | \u2b1c | | |"),
            "\u2b1c",
        )

    def test_status_cell_glyph_ignores_prose_glyph(self) -> None:
        """A glyph sharing a cell with words is prose, not a status cell."""
        self.assertIsNone(
            check_docs._status_cell_glyph("| 1.2 | 2 | 1.1 not yet \u2705 |")
        )

    def test_status_cell_glyph_none_when_no_glyph(self) -> None:
        self.assertIsNone(check_docs._status_cell_glyph("| 1 | 1.1 | \u2014 |"))


if __name__ == "__main__":
    unittest.main()
