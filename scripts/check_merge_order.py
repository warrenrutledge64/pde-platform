#!/usr/bin/env python3
"""Merge-order guard — stop a deliverable from merging ahead of its close-out.

THE TRAP THIS PREVENTS (observed on PDE Story 2.2, PRs #24 and #25):
    A feature PR that ships a deliverable (infra/**) gets merged into `main`
    BEFORE the story's validated close-out commits (status -> ✅, the Validation
    Debt entry cleared, the gate disarmed, the dated Validation Result) are on the
    branch. The deliverable lands on `main` with a STALE ledger: the story reads
    🟡 on the source-of-truth branch even though it passed, and the close-out has
    to be reconciled afterwards in a follow-up PR (the fix-after-merge trap).

THE RULE THIS ENCODES:
    Never merge a deliverable (an infra/** change) into `main` while the
    Validation & Advancement Gate is still ARMED. A PR that changes infra/**
    must ALSO carry the close-out that empties the Validation Debt Register
    (gate DISARMED) at its head before it is safe to merge. Deliverable and
    close-out land together, in one mergeable state.

HOW IT RUNS (checkout-proof, plan-independent):
    As a GitHub Actions job on the pull_request event — the platform checks out
    the exact PR head, so this grades the real state about to merge, and it works
    on a private/free repo where server-side branch protection is NOT enforced.
    It is a RED/GREEN signal: the convention (see CONTRIBUTING.md) is "merge only
    when green." It can also be run locally against any base ref.

Scope note: a PR may legitimately CHANGE infra/** while the story is still in
    progress and the gate is ARMED — that is normal pre-validation work. This
    guard is about MERGING to `main`, so it only objects when a deliverable change
    coincides with an ARMED gate on the branch that is proposed for merge. Once the
    close-out disarms the gate, the same PR goes green.

Exit codes:
    0  OK (docs-only change, or deliverable change with the gate DISARMED)
    1  FAIL (a deliverable change while the gate is ARMED — close-out not landed)
    2  usage / environment error
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNBOOK = REPO_ROOT / "governance" / "RUNBOOK.md"

# A "deliverable" change = anything under infra/ that is a deployable template,
# EXCLUDING the parked/deferred lineage (infra/deferred/, re-validated at its own
# pickup story) and the offline checkers themselves (they are tooling, not a
# deployed artifact). Keep this list aligned with the static-bar's active scope.
DELIVERABLE_RE = re.compile(r"^infra/(?!deferred/)[^/]+\.(ya?ml)$")

GATE_LINE_RE = re.compile(r"\*\*Gate status:\*\*\s*\*\*(ARMED|DISARMED)\*\*", re.IGNORECASE)


def _git(args: list[str]) -> str:
    out = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout.strip()


def changed_files(base_ref: str) -> list[str]:
    """Files changed on HEAD relative to the merge-base with base_ref."""
    merge_base = _git(["merge-base", base_ref, "HEAD"])
    if not merge_base:
        # Fall back to a direct diff if no common ancestor is resolvable.
        merge_base = base_ref
    diff = _git(["diff", "--name-only", f"{merge_base}..HEAD"])
    return [line for line in diff.splitlines() if line.strip()]


def gate_status(runbook_text: str) -> str | None:
    """Return 'ARMED' / 'DISARMED' from the RUNBOOK's Gate status line, or None."""
    m = GATE_LINE_RE.search(runbook_text)
    return m.group(1).upper() if m else None


def evaluate(files: list[str], runbook_text: str) -> tuple[int, str]:
    deliverables = [f for f in files if DELIVERABLE_RE.match(f)]
    if not deliverables:
        return 0, (
            "check_merge_order: OK -- no deliverable (infra/**) change in this "
            "diff; merge-order guard does not apply."
        )

    status = gate_status(runbook_text)
    if status is None:
        return 2, (
            "check_merge_order: ERROR -- could not find the '**Gate status:** "
            "**ARMED|DISARMED**' line in governance/RUNBOOK.md; cannot verify "
            "merge order."
        )

    if status == "ARMED":
        listing = "\n  - ".join(deliverables)
        return 1, (
            "check_merge_order: FAIL -- this PR changes deliverable(s) while the "
            "Validation & Advancement Gate is ARMED:\n  - "
            f"{listing}\n\n"
            "Merging now would land a deliverable on `main` ahead of its validated "
            "close-out (the fix-after-merge trap; see PDE Story 2.2 / OD-008).\n"
            "Before merging, land the close-out on THIS branch so the gate is "
            "DISARMED at head: record the sealed Validation Result, flip the story "
            "✅, and clear its Validation Debt entry. Then this check goes green.\n"
            "See CONTRIBUTING.md -> 'Merge order: deliverable + close-out land "
            "together'."
        )

    return 0, (
        "check_merge_order: OK -- deliverable change with the gate DISARMED "
        "(Validation Debt Register empty at head); safe to merge."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="origin/main",
        help="base ref to diff HEAD against (default: origin/main)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="explicit changed-file list (bypasses git diff; useful in tests/CI)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run in-memory sabotage checks and exit",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if not RUNBOOK.exists():
        print(
            "check_merge_order: ERROR -- governance/RUNBOOK.md not found.",
            file=sys.stderr,
        )
        return 2

    files = args.files if args.files is not None else changed_files(args.base)
    runbook_text = RUNBOOK.read_text(encoding="utf-8")
    code, message = evaluate(files, runbook_text)
    stream = sys.stdout if code == 0 else sys.stderr
    print(message, file=stream)
    return code


def _self_test() -> int:
    """Prove the guard flags the trap and clears when the close-out lands."""
    armed = "**Gate status:** **ARMED** — the register is non-empty."
    disarmed = "**Gate status:** **DISARMED** — the register is empty."

    cases = [
        # (files, runbook_text, expected_exit, label)
        (["governance/RUNBOOK.md"], armed, 0, "docs-only while ARMED -> OK"),
        (["infra/state-machine.yaml"], armed, 1, "deliverable while ARMED -> FAIL"),
        (["infra/state-machine.yaml"], disarmed, 0, "deliverable while DISARMED -> OK"),
        (["infra/deferred/x.yaml"], armed, 0, "deferred-only while ARMED -> OK"),
        (["infra/validate_x.py"], armed, 0, "checker-only while ARMED -> OK"),
        (["infra/state-machine.yaml"], "no gate line here", 2, "missing gate line -> ERROR"),
    ]
    ok = True
    for files, text, expected, label in cases:
        code, _ = evaluate(files, text)
        status = "PASS" if code == expected else "FAIL"
        if code != expected:
            ok = False
        print(f"  [{status}] {label} (got exit {code}, expected {expected})")

    print(
        "check_merge_order --self-test: "
        + ("PASS -- all sabotage cases behaved as expected" if ok else "FAIL")
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
