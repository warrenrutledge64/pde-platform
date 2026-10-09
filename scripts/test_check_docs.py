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
        """Regression: a glyph mentioned in PROSE inside a Ready-Now/Blocked/
        Build-Tier table — which is keyed on the same story id as the summary
        table — must not be mistaken for that story's status.

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


# A runbook with a Progress Summary + two phase sections. Phase 1 is story-complete
# (both stories ✅) AND its summary row is ✅ (correctly closed); Phase 2 has an open
# story and its summary row is 🟡 (correctly in progress). This is the honest tree.
PHASE_RUNBOOK = """# Runbook

## Progress Summary

| Phase | Scope | Gate | Status |
|-------|-------|------|--------|
| **1** | Foundation | health 200 live | \u2705 Done |
| **2** | Features | feature live | \U0001f7e1 In Progress |

## Phase 1 \u2014 Foundation  \u2705

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 1.1 | Skeleton | \u2014 | \u2705 | 2026-01-07 | |
| 1.2 | Persistence | 1.1 | \u2705 | 2026-01-09 | restore/phase-1-green |

**1.1 \u2014 Skeleton**  \u2705 _Done (validated)_
- **Validation Result:** pass \u2014 health 200 live, 2026-01-07, confirmed by maintainer.

**1.2 \u2014 Persistence**  \u2705 _Done (validated)_
- **Validation Result:** pass \u2014 round-trip green, 2026-01-09, confirmed by maintainer.

## Phase 2 \u2014 Features  \U0001f7e1

| Story | Title | Depends on | Status | Completed | Restore tag |
|-------|-------|-----------|--------|-----------|-------------|
| 2.1 | Shorten | 1.2 | \u2705 | 2026-01-12 | |
| 2.2 | Redirect | 2.1 | \U0001f7e1 | | |

**2.1 \u2014 Shorten**  \u2705 _Done (validated)_
- **Validation Result:** pass \u2014 live shorten returned a code, 2026-01-12, confirmed by maintainer.

**2.2 \u2014 Redirect**  \U0001f7e1 _In Progress_
- **Validation Result:** _pending._
"""


class PhaseGateTests(unittest.TestCase):
    """CHECK N: the Progress Summary must stay honest about each phase."""

    def test_honest_tree_has_no_hard_n_and_no_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), PHASE_RUNBOOK)
            self.assertEqual(check_docs.check_n_phase_gate(gov), [])
            self.assertEqual(check_docs.phase_gate_advisories(gov), [])

    def test_phase_marked_done_while_story_open_fires_hard_n(self) -> None:
        """Mark Phase 2's summary row ✅ while 2.2 is still 🟡 -> hard CHECK N."""
        runbook = PHASE_RUNBOOK.replace(
            "| **2** | Features | feature live | \U0001f7e1 In Progress |",
            "| **2** | Features | feature live | \u2705 Done |",
        )
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), runbook)
            violations = check_docs.check_n_phase_gate(gov)
            self.assertEqual(len(violations), 1, violations)
            self.assertEqual(violations[0].check, "CHECK N")
            self.assertIn("phase 2", violations[0].detail)

    def test_story_complete_but_unclosed_phase_is_advisory_not_hard(self) -> None:
        """Phase 1 fully ✅ but its summary row 🟡 -> advisory, never a hard fail."""
        runbook = PHASE_RUNBOOK.replace(
            "| **1** | Foundation | health 200 live | \u2705 Done |",
            "| **1** | Foundation | health 200 live | \U0001f7e1 In Progress |",
        )
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), runbook)
            self.assertEqual(check_docs.check_n_phase_gate(gov), [])  # no hard fail
            advisories = check_docs.phase_gate_advisories(gov)
            self.assertEqual(len(advisories), 1, advisories)
            self.assertEqual(advisories[0].check, "CHECK N (advisory)")
            self.assertIn("PHASE-GATE CLOSE OWED", advisories[0].detail)

    def test_missing_runbook_is_silent_pass(self) -> None:
        """Fail-open: no RUNBOOK.md -> CHECK N + advisory both no-op."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "governance").mkdir()
            gov = Path(tmp) / "governance"
            self.assertEqual(check_docs.check_n_phase_gate(gov), [])
            self.assertEqual(check_docs.phase_gate_advisories(gov), [])

    def test_no_progress_summary_is_no_op(self) -> None:
        """A runbook with phases but no Progress Summary -> CHECK N no-ops (nothing
        to compare the roll-up against)."""
        runbook = PHASE_RUNBOOK.split("## Phase 1", 1)[1]
        runbook = "# Runbook\n\n## Phase 1" + runbook
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), runbook)
            self.assertEqual(check_docs.check_n_phase_gate(gov), [])


class RestorePointCompletenessTests(unittest.TestCase):
    """CHECK N restore-point arm: a ✅ phase must have a restore point RECORDED in BOM.

    In PHASE_RUNBOOK, phase 1 rolls up ✅ and its summary row is ✅ (closed). The arm
    reads BOM.md: a ✅ phase needs a BOM row naming a ``restore/`` tag; and IF the repo
    captures state manifests (a restore-manifests/ dir exists) that row must also name a
    ``manifest-*.json``. Fail-open without BOM.md.
    """

    def test_no_bom_is_fail_open(self) -> None:
        """PHASE_RUNBOOK alone (no BOM.md) -> the restore-point arm no-ops."""
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), PHASE_RUNBOOK)
            bom_viol = [v for v in check_docs.check_n_phase_gate(gov) if v.file == "BOM.md"]
            self.assertEqual(bom_viol, [], "no BOM.md -> restore-point arm no-ops")

    def test_closed_phase_with_bom_restore_tag_passes(self) -> None:
        """A ✅ phase with a BOM row naming a restore/ tag (no manifests dir) is clean."""
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), PHASE_RUNBOOK)
            (gov / "BOM.md").write_text(
                "# BOM\n\n| Artifact | Type | Name | Phase | Restore point |\n"
                "|---|---|---|---|---|\n"
                "| svc | service | svc | 1 | restore/phase-1-green |\n",
                encoding="utf-8",
            )
            bom_viol = [v for v in check_docs.check_n_phase_gate(gov) if v.file == "BOM.md"]
            self.assertEqual(bom_viol, [], f"a ✅ phase with a recorded restore tag is clean: {bom_viol}")

    def test_closed_phase_without_restore_tag_in_bom_fires(self) -> None:
        """A ✅ phase whose BOM row names NO restore/ tag fires the restore-point arm."""
        with tempfile.TemporaryDirectory() as tmp:
            gov = _gov(Path(tmp), PHASE_RUNBOOK)
            (gov / "BOM.md").write_text(
                "# BOM\n\n| Artifact | Type | Name | Phase | Restore point |\n"
                "|---|---|---|---|---|\n"
                "| svc | service | svc | 1 | (none captured) |\n",
                encoding="utf-8",
            )
            bom_viol = [v for v in check_docs.check_n_phase_gate(gov) if v.file == "BOM.md"]
            self.assertEqual(len(bom_viol), 1, f"a ✅ phase with no recorded restore point must fire: {bom_viol}")

    def test_manifest_half_required_only_when_repo_captures_manifests(self) -> None:
        """IF a restore-manifests/ dir exists, a ✅ phase's BOM row must ALSO name a manifest."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gov = _gov(root, PHASE_RUNBOOK)
            (root / "restore-manifests").mkdir()      # repo captures manifests
            # BOM names the tag but NOT a manifest -> the manifest half must fire.
            (gov / "BOM.md").write_text(
                "# BOM\n\n| Artifact | Type | Name | Phase | Restore point |\n"
                "|---|---|---|---|---|\n"
                "| svc | service | svc | 1 | restore/phase-1-green |\n",
                encoding="utf-8",
            )
            bom_viol = [v for v in check_docs.check_n_phase_gate(gov) if v.file == "BOM.md"]
            self.assertEqual(len(bom_viol), 1, f"manifest-capturing repo needs the paired manifest: {bom_viol}")
            # Now name a manifest too -> clean.
            (gov / "BOM.md").write_text(
                "# BOM\n\n| Artifact | Type | Name | Phase | Restore point |\n"
                "|---|---|---|---|---|\n"
                "| svc | service | svc | 1 | restore/phase-1-green; restore-manifests/manifest-20260101T000000Z.json |\n",
                encoding="utf-8",
            )
            bom_viol = [v for v in check_docs.check_n_phase_gate(gov) if v.file == "BOM.md"]
            self.assertEqual(bom_viol, [], f"tag + manifest named -> clean: {bom_viol}")


class SplitBrainLiveRunbookTests(unittest.TestCase):
    """CHECK O: no builder-authored LIVE-RUNBOOK for an OPEN story."""

    def _tree(self, root: Path, opt_in: bool = True) -> Path:
        # CHECK O is OPT-IN: a project enables it by placing the marker in a living
        # governance doc. Append it to the RUNBOOK unless the test wants it OFF.
        runbook = PHASE_RUNBOOK + (
            f"\n\n<!-- {check_docs._CHECK_O_OPT_IN} -->\n" if opt_in else "\n"
        )
        _gov(root, runbook)
        (root / "DOCS" / "session-briefs").mkdir(parents=True)
        return root

    def test_open_story_live_runbook_fires_o_when_opted_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))  # opt-in marker present
            # 2.2 is OPEN (🟡) in PHASE_RUNBOOK.
            (root / "DOCS" / "session-briefs" / "story-2.2-LIVE-RUNBOOK.md").write_text(
                "# how to prove 2.2 live\nStep 1: curl ...", encoding="utf-8"
            )
            violations = check_docs.check_o_no_builder_live_runbook(
                root / "governance", root
            )
            self.assertEqual(len(violations), 1, violations)
            self.assertEqual(violations[0].check, "CHECK O")
            self.assertIn("2.2", violations[0].detail)

    def test_open_story_live_runbook_is_silent_without_opt_in(self) -> None:
        """Default OFF: no opt-in marker -> CHECK O does not fire even for an OPEN
        story's builder-authored LIVE-RUNBOOK (pde-platform's permitted doctrine)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp), opt_in=False)
            (root / "DOCS" / "session-briefs" / "story-2.2-LIVE-RUNBOOK.md").write_text(
                "# operator runbook for 2.2\nStep 1: curl ...", encoding="utf-8"
            )
            self.assertEqual(
                check_docs.check_o_no_builder_live_runbook(root / "governance", root),
                [],
                "without the opt-in marker CHECK O must stay silent",
            )

    def test_closed_story_live_runbook_is_grandfathered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            # 2.1 is CLOSED (✅); its LIVE-RUNBOOK is frozen history.
            (root / "DOCS" / "session-briefs" / "story-2.1-LIVE-RUNBOOK.md").write_text(
                "# frozen history for closed 2.1", encoding="utf-8"
            )
            self.assertEqual(
                check_docs.check_o_no_builder_live_runbook(root / "governance", root),
                [],
            )

    def test_missing_session_briefs_dir_is_no_op(self) -> None:
        """Fail-open: no DOCS/session-briefs/ -> CHECK O no-ops."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _gov(root, PHASE_RUNBOOK)
            self.assertEqual(
                check_docs.check_o_no_builder_live_runbook(root / "governance", root),
                [],
            )


class CheckQAuthorshipBarrierTests(unittest.TestCase):
    """CHECK Q: a seat-owned artifact must declare the seat the matrix assigns its type.

    The barrier (AGENTS.md §4.1): the party that BUILDS the code must not author the
    requirement it is judged against. A ``*-requirement.md`` is Planner-owned; a
    ``Author-Seat: Builder`` declaration on it is the breach. Fail-open on an artifact
    with no declared seat (adopt-forward, not retroactive).
    """

    def _tree(self, root: Path) -> Path:
        _gov(root, PHASE_RUNBOOK)
        (root / "DOCS" / "session-briefs").mkdir(parents=True)
        return root

    def test_builder_authored_requirement_fires(self) -> None:
        """A requirement declaring the Builder seat is the §4.1 breach -> CHECK Q."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            (root / "DOCS" / "session-briefs" / "story-2.2-requirement.md").write_text(
                "Author-Seat: Designer / Builder (Kiro)\n\n# Requirement 2.2\nObjective: ...",
                encoding="utf-8",
            )
            violations = check_docs.check_q_authorship_barrier(root / "governance", root)
            self.assertEqual(len(violations), 1, violations)
            self.assertEqual(violations[0].check, "CHECK Q")
            self.assertIn("story-2.2-requirement.md", violations[0].file)
            self.assertIn("builder", violations[0].detail)

    def test_planner_authored_requirement_passes(self) -> None:
        """The correct seat on a requirement is clean (tolerates a decorated token)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            (root / "DOCS" / "session-briefs" / "story-2.2-requirement.md").write_text(
                "Author-Seat: Planner / Validator (Gemini)\n\n# Requirement 2.2\n...",
                encoding="utf-8",
            )
            self.assertEqual(
                check_docs.check_q_authorship_barrier(root / "governance", root), []
            )

    def test_requirement_without_declared_seat_is_fail_open(self) -> None:
        """Adopt-forward: a requirement with no Author-Seat line is NOT flagged.

        This is why the pre-existing story-3.3-requirement.md (authored before the
        convention) keeps the real repo green until it is re-stamped.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            (root / "DOCS" / "session-briefs" / "story-3.3-requirement.md").write_text(
                "# Requirement 3.3\nObjective: no front-matter seat line here.",
                encoding="utf-8",
            )
            self.assertEqual(
                check_docs.check_q_authorship_barrier(root / "governance", root), []
            )

    def test_non_seat_owned_artifact_is_ignored(self) -> None:
        """A builder-owned type (e.g. a PROMPT) is not a CHECK Q target even if it
        declares the Builder seat — CHECK Q enforces only the requirement barrier."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            (root / "DOCS" / "session-briefs" / "story-2.2-PROMPT.md").write_text(
                "Author-Seat: Builder\n\n# Prompt 2.2\n...", encoding="utf-8"
            )
            self.assertEqual(
                check_docs.check_q_authorship_barrier(root / "governance", root), []
            )

    def test_missing_session_briefs_dir_is_no_op(self) -> None:
        """Fail-open: no DOCS/session-briefs/ -> CHECK Q no-ops."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _gov(root, PHASE_RUNBOOK)
            self.assertEqual(
                check_docs.check_q_authorship_barrier(root / "governance", root), []
            )

    def test_declared_seat_helper_normalises(self) -> None:
        self.assertEqual(
            check_docs._declared_author_seat("Author-Seat: Planner / Validator (Gemini)"),
            "planner",
        )
        self.assertEqual(
            check_docs._declared_author_seat("author-seat: Designer / Builder (Kiro)"),
            "builder",
        )
        self.assertIsNone(check_docs._declared_author_seat("no seat line here"))


if __name__ == "__main__":
    unittest.main()
