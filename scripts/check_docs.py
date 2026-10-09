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
  CHECK N  -- (phase-gate) the hand-kept Progress Summary disagrees with the phase
              roll-up derived from the story rows. A phase marked ✅ while a story
              in it is open HARD-fails; a story-complete-but-unclosed phase is a
              loud "PHASE-GATE CLOSE OWED" advisory printed every run (the skipped
              end-of-phase gate — never auto-closed). No-op without a Progress
              Summary / phase sections.
  CHECK O  -- (split-brain) an OPEN story has a builder-authored
              ``*-LIVE-RUNBOOK.md`` under DOCS/session-briefs/. The builder does
              not author live-proof steps; the validator authors them blind (§4a).
              Closed-story LIVE-RUNBOOKs are frozen history (grandfathered).
  CHECK Q  -- (authorship barrier, AGENTS.md §4.1 / RD-013) a seat-owned session
              artifact declares an ``Author-Seat:`` other than the one the §3
              authority matrix assigns its type -- e.g. a ``*-requirement.md``
              authored by the Builder (the thing-under-test framing its own
              judgment). Fail-open: no declared seat -> not flagged (adopt-forward).
  CHECK R  -- (Moderator-lane barrier, RD-014) the same engine, Moderator lane: a
              Moderator run artifact (``*-moderator.md`` / ``*-moderator-attestation.md``
              / ``*-gate-record.md``) authored by the Builder. The Builder authors the
              gate DEFINITIONS (governance) but NOTHING for a run. The enforced set is
              the ``_SEAT_OWNED_ARTIFACTS`` dial -- extensible without new logic.

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


def _status_cell_glyph(row: str) -> str | None:
    """Return the status glyph of a summary-table row, or None.

    A story's status lives in its own **cell** of the phase summary table (e.g.
    ``| 1.1 | Title | deps | ⬜ | ... |``). Other tables in the runbook — the
    Ready-Now / Blocked / Build-Tier tables — are *also* keyed on a story id and
    may legitimately mention a glyph inside *prose* (e.g. ``| 1.2 | 2 | 1.1 not
    yet ✅ |``). Those prose mentions are not the story's status and must not be
    read as one.

    The discriminator: a real status cell contains a glyph as its **sole
    significant token** (only the glyph, ignoring surrounding whitespace). A prose
    cell mixes the glyph with words. So we split the row into pipe-delimited cells
    and accept a glyph only from a cell whose stripped content *is* exactly that
    glyph. If several cells qualify (they should not), the leftmost wins.
    """
    for cell in row.split("|"):
        stripped = cell.strip()
        if stripped in STATUS_GLYPHS:
            return stripped
    return None


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
            # Status is the glyph that is the SOLE content of one of the row's
            # cells (a real status cell) -- NOT a glyph embedded in prose in an
            # auxiliary table (Ready-Now / Blocked / Build-Tier), which is keyed
            # on the same story id but is not a status statement.
            g = _status_cell_glyph(line)
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


# ---------------------------------------------------------------------------
# CHECK N -- phase-gate: the hand-kept Progress Summary must not lie about a phase.
# ---------------------------------------------------------------------------
#
# The end-of-phase validation (run the gate, capture the restore point, flip the
# phase row ✅) is the easiest discipline to skip, because nothing fires when a
# phase quietly reaches "every story ✅". CHECK N makes it mechanical: it derives
# each phase's TRUE status from the story rows under its ``## Phase N`` section and
# compares it to the glyph in that phase's Progress-Summary row. Fail-open: if the
# runbook has no Progress Summary or no phase sections (a fresh / partially-adopted
# template, where phases are still ``{{PHASE_ID}}`` placeholders), it is a no-op.

# A ``## Phase <label> — <name>  <glyph>`` section heading. The label is whatever
# sits between "Phase" and the em/en dash or the glyph (a number, "P1", a name).
_PHASE_HEADING_RE = re.compile(r"^##\s+Phase\s+(?P<label>.+?)\s*(?:[—–-].*)?$")
# A Progress-Summary row: ``| **<label>** | scope | gate | <status> |``. The label
# is read from the first cell (bold-stripped); the status is the row's status cell.
_SUMMARY_ROW_RE = re.compile(r"^\|\s*\*{0,2}(?P<label>[^|*]+?)\*{0,2}\s*\|.*\|\s*$")


def _norm_phase_label(label: str) -> str:
    """Normalise a phase label so a ``## Phase`` heading and a Progress-Summary
    row key the same (strip glyphs/emphasis/whitespace; take the leading token)."""
    text = label
    for g in STATUS_GLYPHS:
        text = text.replace(g, "")
    text = text.replace("*", "").strip()
    # Key on the leading token (e.g. "1" from "1 — Foundation", "P1" from "P1").
    return text.split()[0] if text.split() else text


def _rollup_phase_status(runbook_text: str) -> dict[str, str]:
    """Derive each phase's true status by rolling up the story rows beneath its
    ``## Phase`` heading: ✅ only if every story row is ✅; else 🟡 if any story is
    started/done; else ⬜. Returns ``{normalised_label: glyph}`` (empty if no
    phase sections / no story rows are found -> CHECK N no-ops)."""
    IN_PROGRESS, BLOCKED = STATUS_GLYPHS[1], STATUS_GLYPHS[2]
    NOT_STARTED = STATUS_GLYPHS[0]
    rollup: dict[str, list[str]] = {}
    current: str | None = None
    for line in runbook_text.splitlines():
        hm = _PHASE_HEADING_RE.match(line)
        if hm:
            current = _norm_phase_label(hm.group("label"))
            rollup.setdefault(current, [])
            continue
        if line.startswith("## "):  # left the phase section (some other heading)
            current = None
            continue
        if current is None:
            continue
        m = STORY_ROW_RE.match(line)
        if m:
            g = _status_cell_glyph(line)
            if g is not None:
                rollup[current].append(g)
    result: dict[str, str] = {}
    for label, glyphs in rollup.items():
        if not glyphs:
            continue  # a phase heading with no story-table rows -> cannot roll up
        gs = set(glyphs)
        if gs == {DONE}:
            result[label] = DONE
        elif gs & {DONE, IN_PROGRESS, BLOCKED}:
            result[label] = IN_PROGRESS
        else:
            result[label] = NOT_STARTED
    return result


def _summary_phase_status(runbook_text: str) -> dict[str, str]:
    """Read the hand-kept Progress Summary table's ``{normalised_label: glyph}``.

    Only rows inside the ``## Progress Summary`` section are read. Fail-open: no
    section / no parseable rows -> empty map (CHECK N no-ops)."""
    result: dict[str, str] = {}
    in_section = False
    for line in runbook_text.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## Progress Summary"
            continue
        if not in_section or "|" not in line:
            continue
        # Skip header + separator rows.
        low = line.lower()
        if "phase" in low and "status" in low and "scope" in low:
            continue
        if set(line.strip()) <= set("|-: "):
            continue
        rm = _SUMMARY_ROW_RE.match(line)
        if rm is None:
            continue
        # The Progress Summary status cell carries a glyph + a label (e.g.
        # "✅ Done", "🟡 In Progress"), so read the FIRST glyph of the LAST
        # non-empty cell rather than requiring a bare-glyph cell.
        cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        g = _first_glyph(cells[-1]) if cells else None
        if g is None:
            continue
        label = _norm_phase_label(rm.group("label"))
        if label and label.lower() != "phase":
            result.setdefault(label, g)
    return result


def check_n_phase_gate(gov_dir: Path) -> list[Violation]:
    """CHECK N (hard): a Progress-Summary phase row may never claim a phase is MORE
    complete than its stories.

    Hard-fails only the contradiction direction — the phase row is ✅ while a story
    under its ``## Phase`` section is still open. The opposite direction (every
    story ✅ but the phase row not yet ✅ — the skipped end-of-phase gate) is a
    non-blocking advisory (``phase_gate_advisories``): closing a phase is a
    stakeholder-confirmed act, surfaced on every run but never auto-tripped. Fail-
    open: no Progress Summary / no phase story rows -> no-op.
    """
    runbook = gov_dir / "RUNBOOK.md"
    if not runbook.exists():
        return []
    text = runbook.read_text(encoding="utf-8")
    rollup = _rollup_phase_status(text)
    summary = _summary_phase_status(text)
    violations: list[Violation] = []
    for label, shown in sorted(summary.items()):
        true_g = rollup.get(label)
        if true_g is None or shown != DONE or true_g == DONE:
            continue
        violations.append(
            Violation(
                "CHECK N",
                "RUNBOOK.md",
                f"phase {label}: the Progress Summary marks it ✅ but a story under "
                "its section is not ✅; a phase may not be done while a story it "
                "contains is open (reconcile the phase row to its stories)",
            )
        )
    # Restore-point completeness: a ✅ phase must have a restore point RECORDED, because a
    # phase close is a coordinated code+state baseline (a restore point you can return to),
    # not just a green behaviour run. Checked against BOM.md (the restore-point index). The
    # DEPTH is fail-open + generic: a ✅ phase whose stories roll up ✅ must have a BOM row for
    # that phase naming a ``restore/`` tag. IF the repo captures state manifests (a
    # ``restore-manifests/`` dir exists — the heavier, ZTIE-style discipline), that row must
    # ALSO name a ``manifest-*.json`` (an annotated tag PAIRED WITH a verified state manifest,
    # RESTORE.md rule 4). A project that does not capture manifests is not flagged for the
    # manifest half. Fail-open: no BOM.md -> skipped.
    bom = gov_dir / "BOM.md"
    if bom.exists():
        bom_text = bom.read_text(encoding="utf-8")
        # Does the repo capture state manifests? (any restore-manifests/ dir up the tree)
        captures_manifests = any(
            (d / "restore-manifests").is_dir() for d in (gov_dir, gov_dir.parent)
        )
        # The numeric/token core of a phase label (e.g. "0" from "Phase 0", "1" from
        # "P1") so a BOM row's Phase cell can be matched to the phase.
        for label in sorted(lbl for lbl, g in summary.items() if g == DONE):
            if rollup.get(label) != DONE:
                continue  # premature ✅ already reported as the contradiction above
            has_tag = has_manifest = produces = False
            for line in bom_text.splitlines():
                if "|" not in line or not re.search(rf"\b{re.escape(label)}\b", line):
                    continue
                # A BOM §2 inventory row for this phase = the phase PRODUCES materials.
                # (A row that only indexes a restore point is caught by has_tag below.)
                produces = True
                if "restore/" in line:
                    has_tag = True
                    if re.search(r"manifest-[0-9A-Za-z]+\.json", line):
                        has_manifest = True
            # A phase that produces NO deployed materials (a docs-only / bootstrap
            # phase — no BOM §2 inventory row names it) has no coordinated code+state
            # baseline to restore, so a restore point is not required of it. Only
            # require a restore point for a phase that actually produces/deploys
            # something. (Fail-open on bootstrap phases — matches the documented
            # "a restore/phase-0-green tag is optional and not cut" convention.)
            if not produces:
                continue
            if not has_tag:
                violations.append(
                    Violation(
                        "CHECK N",
                        "BOM.md",
                        f"phase {label} is marked ✅ (closed) but BOM.md records no "
                        "restore point (a restore/ tag) for it; a phase closes to a "
                        "coordinated restore point, not on a behaviour run alone "
                        "(record its restore/phase-N-green baseline in BOM.md).",
                    )
                )
            elif captures_manifests and not has_manifest:
                violations.append(
                    Violation(
                        "CHECK N",
                        "BOM.md",
                        f"phase {label} is ✅ and this repo captures state manifests, "
                        "but its BOM restore-point row names no paired "
                        "restore-manifests/manifest-*.json; a complete restore point is "
                        "an annotated tag PAIRED WITH a verified state manifest "
                        "(RESTORE.md). Record + verify the manifest, then name it.",
                    )
                )
    return violations


def phase_gate_advisories(gov_dir: Path) -> list[Violation]:
    """ADVISORY (non-blocking): name every phase that is STORY-COMPLETE but not yet
    CLOSED — every story ✅ while the Progress-Summary row is not ✅. The end-of-
    phase gate (run the check, capture the restore point, flip the row) was not
    recorded. Surfaced on every run so a skipped phase-gate can never silently
    slip; never auto-closed (closing a phase is a stakeholder-confirmed act)."""
    runbook = gov_dir / "RUNBOOK.md"
    if not runbook.exists():
        return []
    text = runbook.read_text(encoding="utf-8")
    rollup = _rollup_phase_status(text)
    summary = _summary_phase_status(text)
    advisories: list[Violation] = []
    for label, true_g in sorted(rollup.items()):
        if true_g != DONE or summary.get(label) == DONE:
            continue
        advisories.append(
            Violation(
                "CHECK N (advisory)",
                "RUNBOOK.md",
                f"phase {label} is STORY-COMPLETE (every story ✅) but its phase row "
                "is not ✅: PHASE-GATE CLOSE OWED — run the end-of-phase gate, "
                "capture/confirm the restore point, then flip the Progress Summary "
                "row to ✅. A story-complete phase is NOT a closed phase.",
            )
        )
    return advisories


# ---------------------------------------------------------------------------
# CHECK O -- split-brain: the builder does not author live-proof steps.
# ---------------------------------------------------------------------------
#
# The split-brain discipline (§4a) says the party that built the code does not
# frame how it is judged — the independent validator authors the live steps + DoD.
# A ``*-LIVE-RUNBOOK.md`` committed for an OPEN story is the concrete artifact-form
# of a breach (the builder writing "how to prove it live"). CHECK O hard-fails that
# for forward work; LIVE-RUNBOOKs for closed (✅) stories are frozen history and are
# grandfathered. Fail-open: no session-briefs dir -> no-op.

# A story's open/closed status is read from the RUNBOOK summary-table rows.
_LIVE_RUNBOOK_RE = re.compile(r"^(?:story-)?(?P<id>" + _STORY_ID + r")-LIVE-RUNBOOK\.md$")


def _runbook_story_statuses(gov_dir: Path) -> dict[str, str]:
    """Return ``{story_id: glyph}`` from the RUNBOOK summary-table rows."""
    runbook = gov_dir / "RUNBOOK.md"
    if not runbook.exists():
        return {}
    statuses: dict[str, str] = {}
    for line in runbook.read_text(encoding="utf-8").splitlines():
        m = STORY_ROW_RE.match(line)
        if not m:
            continue
        g = _status_cell_glyph(line)
        if g is not None:
            statuses.setdefault(m.group(1), g)
    return statuses


# CHECK O is OPT-IN. The strict "the builder authors NO live-proof steps, not even an
# operator runbook" doctrine (ZTIE's RD-055) is one valid stance; another valid stance
# (e.g. pde-platform) is that a builder-authored operator LIVE-RUNBOOK is a legitimate
# turnkey execution surface the independent validator ADOPTS / reorders / extends while
# still authoring the acceptance criteria itself. The split-brain guarantee (the builder
# does not author the DoD/verdict) holds under BOTH. So CHECK O only fires where a project
# has EXPLICITLY opted in by placing this marker in a living governance doc (RUNBOOK /
# METHODOLOGY / CONVENTIONS). Default OFF -> a project that uses operator runbooks is not
# broken; a project that wants the strict rule declares it.
_CHECK_O_OPT_IN = "check-o: enforce no-builder-live-runbook"


def _check_o_enabled(gov_dir: Path, repo_root: Path) -> bool:
    """True iff the project opted into CHECK O via the marker in a living gov doc."""
    for base in (gov_dir, repo_root):
        for name in ("RUNBOOK.md", "METHODOLOGY.md", "CONVENTIONS.md"):
            p = base / name
            if p.exists() and _CHECK_O_OPT_IN in p.read_text(encoding="utf-8"):
                return True
    return False


def check_o_no_builder_live_runbook(gov_dir: Path, repo_root: Path) -> list[Violation]:
    """CHECK O (split-brain, OPT-IN): no builder-authored ``*-LIVE-RUNBOOK.md`` for an
    OPEN story. The validator authors the live steps + DoD blind (§4a); the builder must
    not frame "how to prove it live." Closed-story LIVE-RUNBOOKs are frozen history and
    grandfathered.

    OPT-IN: only fires where the project declares the strict doctrine via the
    ``check-o: enforce no-builder-live-runbook`` marker in a living governance doc. A
    project whose doctrine permits a builder-authored OPERATOR runbook (that the
    validator adopts/extends while still authoring the DoD itself) simply does not place
    the marker and is unaffected. Fail-open: no marker / no session-briefs dir -> no-op.
    """
    if not _check_o_enabled(gov_dir, repo_root):
        return []
    IN_PROGRESS, BLOCKED = STATUS_GLYPHS[1], STATUS_GLYPHS[2]
    # Session artifacts live under DOCS/session-briefs/ (root or governance/).
    candidates = [
        repo_root / "DOCS" / "session-briefs",
        gov_dir / "DOCS" / "session-briefs",
        gov_dir / "session-briefs",
    ]
    briefs = next((d for d in candidates if d.is_dir()), None)
    if briefs is None:
        return []
    statuses = _runbook_story_statuses(gov_dir)
    violations: list[Violation] = []
    for path in sorted(briefs.glob("*-LIVE-RUNBOOK.md")):
        m = _LIVE_RUNBOOK_RE.match(path.name)
        if not m:
            continue
        if statuses.get(m.group("id")) not in {IN_PROGRESS, BLOCKED}:
            continue  # closed / unknown stories are frozen history -> grandfathered
        violations.append(
            Violation(
                "CHECK O",
                f"DOCS/session-briefs/{path.name}",
                f"story {m.group('id')} is OPEN but has a builder-authored "
                "LIVE-RUNBOOK; the builder does not author live-proof steps — the "
                "independent validator authors the live steps + DoD blind (§4a). "
                "Remove it (closed-story LIVE-RUNBOOKs are grandfathered).",
            )
        )
    return violations


# ---------------------------------------------------------------------------
# CHECK Q -- authorship barrier: the thing-under-test must not frame its own judgment.
# ---------------------------------------------------------------------------
#
# The split-brain / Troikauge barrier (AGENTS.md §4.1) says the party that BUILDS the
# code never frames HOW it is judged: the Planner authors the requirement (the "what/why"
# that the independent Validator derives its Definition of Done from), and the Builder
# authors only the operator runbook + the validator handover's pinned-target + a
# stakeholder requirement blank. A Builder-authored requirement is the concrete breach —
# the thing-under-test writing its own acceptance envelope.
#
# This was a PROSE-only barrier (§4.1 + the §3 authority matrix) with no mechanical guard,
# exactly the "when a prose precondition keeps getting skipped, make it mechanical"
# class (METHODOLOGY §7). CHECK Q makes it mechanical via a declared **Author-Seat:**
# front-matter line each seat-owned session artifact must carry, naming the seat that
# authored it. The check fails when an artifact's declared seat does not match the seat
# the authority matrix assigns that artifact TYPE (e.g. a ``*-requirement.md`` that
# declares ``Author-Seat: Builder`` — the builder framing its own judgment).
#
# Why a declared marker and not git authorship? In a solo-operator repo every commit is
# the same human identity across all seats, so a git-blame/branch heuristic produces only
# false positives. The declared seat is the robust, reviewable signal (stakeholder choice,
# Story G-5). Fail-OPEN and depth-adaptive: an artifact with NO Author-Seat line is not
# flagged (the convention is adopt-forward, not retroactive); no session-briefs dir -> no-op.

# ===========================================================================
# THE AUTHORSHIP-BARRIER DIAL — the single source of truth both CHECK Q (§4.1,
# RD-013) and CHECK R (Moderator lane, RD-014) read.
# ===========================================================================
#
# This table IS the enforcement dial. Each entry maps a filename-suffix pattern of a
# SEAT-OWNED session artifact to the ONE seat the authority matrix (AGENTS.md §3) allows
# to author it. A committed artifact that DECLARES a different seat HARD-fails. To make
# the barrier "heavier" later, ADD a (pattern, seat) row here — no new logic, no new
# check function. To relax, remove a row. This is the deliberate "reasonable now, heavier
# if needed" seam (stakeholder direction, Story G-5/RD-014): the coverage is data, not code.
#
# What is intentionally NOT listed: builder-owned surfaces (operations / prompt) and the
# validator handover — the barrier guards the artifacts that FRAME A JUDGMENT or RECORD A
# GATE, not every file. Two breaches are enforced:
#   * requirement  -> planner   (RD-013/§4.1): the judgment INPUT must not be builder-authored.
#   * moderator record/attestation -> moderator (RD-014): a MODERATOR-lane run artifact must
#     not be builder-authored — the Builder authors the gate DEFINITIONS (governance, matrix-
#     allowed) but NOTHING for a specific run (no record, attestation, or scaffold).
#
# Why a declared marker and not git authorship? In a solo-operator repo every commit is the
# same human identity across all seats, so a git-blame/branch heuristic produces only false
# positives. The declared seat is the robust, reviewable signal. Fail-OPEN + adopt-forward:
# an artifact with NO Author-Seat line is not flagged; no session-briefs dir -> no-op. Note
# the chat-pasted / un-committed vector is uncatchable by ANY checker and is covered instead
# by the seat-refusal doctrine (AGENTS.md / MODERATOR_PROTOCOL.md) — adding checker logic
# there would be theatre, so this guard honestly covers only the committed-artifact vector.
_SEAT_OWNED_ARTIFACTS: tuple[tuple[re.Pattern[str], str], ...] = (
    # CHECK Q (RD-013/§4.1): the requirement is the Planner's; a builder-authored
    # requirement is the thing-under-test framing its own judgment.
    (re.compile(r"-requirement\.md$"), "planner"),
    # CHECK R (RD-014): Moderator-lane run artifacts are the Moderator's; a builder-authored
    # one is the builder authoring in the Moderator's lane. (Add Moderator-record filename
    # shapes here to turn the dial heavier.)
    (re.compile(r"-moderator-attestation\.md$"), "moderator"),
    (re.compile(r"-moderator\.md$"), "moderator"),
    (re.compile(r"-gate-record\.md$"), "moderator"),
)
# The check-id + §-citation each seat-owned type reports when it fails, keyed by required
# seat (so a Violation names the right governance anchor without a second lookup table).
_SEAT_RULE: dict[str, tuple[str, str]] = {
    "planner": ("CHECK Q", "the requirement it is judged against (§4.1 / RD-013)"),
    "moderator": (
        "CHECK R",
        "a Moderator-lane run artifact (the builder authors the gate DEFINITIONS only, "
        "never a run record/attestation — RD-014)",
    ),
}
# ``Author-Seat: <seat>`` anywhere near the top of a seat-owned artifact (front-matter or
# an authoring blockquote). Case-insensitive; the seat token is normalised to lower-case.
_AUTHOR_SEAT_RE = re.compile(r"author-seat:\s*([A-Za-z/ ]+)", re.IGNORECASE)
# A declared seat is matched by the words it contains (tolerates "Planner / Validator",
# "Designer / Builder (Kiro)", "Moderator (Copilot)", etc.). Order matters only for display.
_SEAT_WORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("builder", ("builder", "designer")),
    ("planner", ("planner",)),
    ("moderator", ("moderator",)),
    ("validator", ("validator",)),
)


def _declared_author_seat(text: str) -> str | None:
    """Return the normalised declared author seat of an artifact, or None if absent.

    Normalises to a coarse seat word (``planner`` / ``builder`` / ``moderator`` /
    ``validator``) so a decorated declaration (``Author-Seat: Planner / Validator
    (Gemini)``) still compares cleanly; returns the raw lower-cased token if it matches
    none (so a typo'd seat is visibly reported rather than silently passing).

    Note: ``builder`` is checked first so a combined "Designer / Builder" never slips
    past as something else; a legitimate Moderator/Planner artifact declares its own
    single seat, so no real artifact is mis-bucketed by the ordering."""
    m = _AUTHOR_SEAT_RE.search(text)
    if not m:
        return None
    raw = m.group(1).strip().lower()
    for seat, words in _SEAT_WORDS:
        if any(w in raw for w in words):
            return seat
    return raw


def _check_authorship_barrier(gov_dir: Path, repo_root: Path) -> list[Violation]:
    """Shared engine for CHECK Q (§4.1/RD-013) and CHECK R (RD-014): a seat-owned session
    artifact must not DECLARE an author seat other than the one the authority matrix
    assigns its TYPE (per the ``_SEAT_OWNED_ARTIFACTS`` dial).

    Fail-OPEN: an artifact with no ``Author-Seat:`` line is not flagged (adopt-forward,
    not retroactive); no session-briefs dir -> no-op. Only the committed-artifact vector
    is enforced here (the chat/un-committed vector is covered by the seat-refusal doctrine).
    """
    candidates = [
        repo_root / "DOCS" / "session-briefs",
        gov_dir / "DOCS" / "session-briefs",
        gov_dir / "session-briefs",
    ]
    briefs = next((d for d in candidates if d.is_dir()), None)
    if briefs is None:
        return []
    violations: list[Violation] = []
    for path in sorted(briefs.glob("*.md")):
        required = next(
            (seat for pat, seat in _SEAT_OWNED_ARTIFACTS if pat.search(path.name)), None
        )
        if required is None:
            continue  # not a seat-owned type the dial enforces
        declared = _declared_author_seat(path.read_text(encoding="utf-8"))
        if declared is None:
            continue  # fail-open: no declared seat -> not flagged (adopt-forward)
        if declared != required:
            check_id, framed = _SEAT_RULE.get(required, ("CHECK Q/R", "its judgment"))
            violations.append(
                Violation(
                    check_id,
                    f"DOCS/session-briefs/{path.name}",
                    f"declares 'Author-Seat: {declared}' but the authority matrix "
                    f"(AGENTS.md §3) assigns this artifact type to the {required} seat; "
                    f"the builder must not author {framed}. Re-author it in the correct seat.",
                )
            )
    return violations


# Back-compat shim: CHECK Q is now one lane of the shared authorship-barrier engine.
# (Kept as a named entry point so callers/tests that reference it directly still work.)
def check_q_authorship_barrier(gov_dir: Path, repo_root: Path) -> list[Violation]:
    """CHECK Q + CHECK R (authorship barrier): delegates to the shared engine. CHECK Q
    (§4.1/RD-013) enforces the requirement->Planner lane; CHECK R (RD-014) enforces the
    Moderator-record->Moderator lane. Both read the ``_SEAT_OWNED_ARTIFACTS`` dial."""
    return _check_authorship_barrier(gov_dir, repo_root)


def run_checks(repo_root: Path) -> list[Violation]:
    gov = _governance_dir(repo_root)
    out: list[Violation] = []
    out += check_g_done_without_validation(gov)
    out += check_s_status_consistency(gov)
    out += check_p_stray_placeholders(gov)
    out += check_l_dangling_links(gov, repo_root)
    out += check_m_repo_map(repo_root)
    out += check_n_phase_gate(gov)
    out += check_o_no_builder_live_runbook(gov, repo_root)
    out += check_q_authorship_barrier(gov, repo_root)
    return out


def check_locks(repo_root: Path, base: str, head: str) -> list[Violation]:
    """Delegate to check_locks (input-poisoning systemic locks) if present.

    Git-sourced HARD locks (Lock 2/3/4) over base..head; fail-open when git / the
    refs are absent, so this is a no-op outside a diffable range. HARD lock findings
    become blocking violations; the Lock-1 advisory is surfaced via run_advisories.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import check_locks as _locks
    except ImportError:
        return []
    return [
        Violation(f.lock, f.where, f.detail)
        for f in _locks.run_locks(repo_root, base, head)
        if f.severity == "HARD"
    ]


def lock_advisories(repo_root: Path, base: str, head: str) -> list[Violation]:
    """The non-blocking ADVISORY lock findings (currently Lock 1 — un-cited givens)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import check_locks as _locks
    except ImportError:
        return []
    return [
        Violation(f.lock, f.where, f.detail)
        for f in _locks.run_locks(repo_root, base, head)
        if f.severity == "ADVISORY"
    ]


def run_advisories(repo_root: Path) -> list[Violation]:
    """Non-blocking advisories (printed, never affect the exit code)."""
    return phase_gate_advisories(_governance_dir(repo_root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=".", help="repo root to check (default: cwd)")
    parser.add_argument(
        "--base",
        default=None,
        help="base ref for the input-poisoning LOCKS (e.g. origin/main); omit to skip "
        "the git-sourced locks (Lock 2/3/4 hard + the Lock-1 advisory)",
    )
    parser.add_argument("--head", default="HEAD", help="head ref for the locks (default: HEAD)")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the input-poisoning LOCKS sabotage self-test and exit",
    )
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)

    if args.self_test:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            import check_locks as _locks
            return _locks._self_test()
        except ImportError:
            print("check_docs: check_locks not present; nothing to self-test")
            return 0

    # Non-blocking advisories (phase-gate "close owed" + Lock-1 un-cited givens).
    # Printed on every run so a skipped gate or a smuggled given can never silently
    # slip; never affects the exit code.
    advisories = run_advisories(repo_root)
    if args.base:
        advisories += lock_advisories(repo_root, args.base, args.head)
    if advisories:
        print(f"check_docs: ADVISORY -- {len(advisories)} note(s) (does not block):")
        for a in advisories:
            print(f"  {a.render()}")

    violations = run_checks(repo_root)
    if args.base:
        violations += check_locks(repo_root, args.base, args.head)
    if violations:
        print(f"check_docs: FAIL -- {len(violations)} violation(s):")
        for v in violations:
            print(f"  {v.render()}")
        return 1
    print("check_docs: PASS -- governance docs are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
