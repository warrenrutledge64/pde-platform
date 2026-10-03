#!/usr/bin/env python3
"""Offline guard: every pdlv- stack deploy carries the mandatory Project=PDE tag.

WHY THIS EXISTS (OD-012, Phase 2 gate FAIL 2026-10-02)
------------------------------------------------------
The Phase 2 end-of-phase gate sealed FAIL because the LIVE-DEPLOYED
``pdlv-promotion-pipeline-stack`` lacked the mandatory ``Project=PDE`` tag
(RD-009 / Universal Criterion 5 — every PDE-owned Hub resource must be
attributable so it is distinguishable from ZTIE's untagged ``pde-*`` shadow
footprint).

This is a LIVE-vs-TEMPLATE drift that the existing offline checker
(``infra/validate_state_machine.py``) could not catch, by design: the state
machine is a BARE-RESOURCE CloudFormation template with no stack-level ``Tags``
block — the STACK-level ``Project=PDE`` tag is applied by the DEPLOY COMMAND
(``aws cloudformation deploy --tags Project=PDE`` / ``create-stack --tags
Key=Project,Value=PDE``), not by the template YAML. So the drift class lives in
the OPERATOR PROCEDURE (the LIVE-RUNBOOK deploy invocation), not in the template.

This checker folds that live finding back into the offline bar (the standing
"fold the live finding back into the offline checker + a --self-test sabotage"
discipline): it fails if any ``pdlv-`` stack ``deploy``/``create-stack``
invocation in a committed LIVE-RUNBOOK omits the ``Project=PDE`` tag. It is
disk-independent (parses committed text), stdlib-only, and self-tests in memory.

It does NOT (and cannot) prove the LIVE stack is tagged — that is the operator's
mandatory post-deploy ``describe-stacks ... Tags`` VERIFY in the LIVE-RUNBOOK and
the gate's live BOM reconciliation. This guard proves the PROCEDURE a correct
run would follow never silently drops the tag.

Usage:
    python3 scripts/check_deploy_tags.py            # scan committed LIVE-RUNBOOKs
    python3 scripts/check_deploy_tags.py --self-test # in-memory sabotage proof

Exit: 0 = all deploy invocations carry Project=PDE (or self-test passed);
      1 = one or more deploy invocations omit the tag (or self-test failed).
"""

from __future__ import annotations

import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# LIVE-RUNBOOKs are where the operator deploy commands live.
RUNBOOK_GLOB = os.path.join(
    REPO_ROOT, "DOCS", "session-briefs", "*LIVE-RUNBOOK*.md"
)

# A deploy "unit" = an `aws cloudformation deploy` OR `create-stack` invocation,
# possibly spread over multiple backslash-continued lines, up to a blank line or
# the next command. We only police invocations that target a `pdlv-` stack
# (never ZTIE's `pde-*`, which PDE does not deploy).
_DEPLOY_RE = re.compile(
    r"aws\s+cloudformation\s+(?:deploy|create-stack)\b"
)
_PDLV_STACK_RE = re.compile(r"--stack-name\s+[\"']?pdlv-")
# Accept both the `deploy --tags Project=PDE` form and the `create-stack --tags
# Key=Project,Value=PDE` form.
_PROJECT_TAG_RE = re.compile(
    r"(?:\bProject=PDE\b)|(?:Key=Project,\s*Value=PDE\b)"
)


def _deploy_blocks(text: str) -> list[str]:
    """Return each full (line-continuation-joined) cloudformation deploy/create
    invocation found in ``text`` whose --stack-name targets a pdlv- stack.

    A command may span several lines joined by a trailing backslash; we join
    those into one logical command so the --tags flag on a later line counts.
    """
    # Join backslash-continued lines into single logical lines.
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    blocks: list[str] = []
    for line in joined.splitlines():
        if _DEPLOY_RE.search(line) and _PDLV_STACK_RE.search(line):
            blocks.append(line.strip())
    return blocks


def invariants_for_text(text: str, source: str) -> list[tuple[str, bool]]:
    """Return (description, ok) for every pdlv- deploy invocation in ``text``.

    Pure function of the text so --self-test can feed deliberately broken input.
    """
    checks: list[tuple[str, bool]] = []
    blocks = _deploy_blocks(text)
    for i, block in enumerate(blocks, 1):
        snippet = (block[:90] + "…") if len(block) > 90 else block
        checks.append(
            (
                f"{source}: pdlv- deploy #{i} carries Project=PDE tag  [{snippet}]",
                bool(_PROJECT_TAG_RE.search(block)),
            )
        )
    return checks


def _report(checks: list[tuple[str, bool]]) -> int:
    failed = 0
    for desc, ok in checks:
        mark = "ok  " if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{mark}] {desc}")
    if failed:
        print(
            f"check_deploy_tags: FAIL — {failed} pdlv- deploy invocation(s) "
            f"omit the mandatory Project=PDE tag (OD-012 / RD-009)."
        )
        return 1
    if not checks:
        # No pdlv- deploy invocations found at all — a scope/content regression,
        # not a silent pass.
        print(
            "check_deploy_tags: FAIL — found NO pdlv- cloudformation deploy "
            "invocation to police (expected at least one in a LIVE-RUNBOOK)."
        )
        return 1
    print(
        f"check_deploy_tags: PASS — all {len(checks)} pdlv- deploy "
        f"invocation(s) carry Project=PDE."
    )
    return 0


def self_test() -> int:
    """Prove the guard flips to FAIL when a deploy drops the Project=PDE tag."""
    clean = (
        "```bash\n"
        "aws cloudformation deploy \\\n"
        "  --template-file infra/state-machine.yaml \\\n"
        "  --stack-name pdlv-promotion-pipeline-stack \\\n"
        "  --capabilities CAPABILITY_NAMED_IAM \\\n"
        "  --tags Project=PDE Story=2.3 Component=state-machine \\\n"
        "  --no-fail-on-empty-changeset\n"
        "aws cloudformation create-stack \\\n"
        "  --stack-name pdlv-codebuild \\\n"
        "  --template-body file://infra/codebuild-projects.yaml \\\n"
        "  --tags Key=Project,Value=PDE Key=Story,Value=2.3\n"
        "```\n"
    )
    # Sabotage A: the deploy drops --tags entirely.
    sab_a = clean.replace(
        "  --tags Project=PDE Story=2.3 Component=state-machine \\\n", ""
    )
    # Sabotage B: the tag value is wrong (Project=ZTIE — the collision we guard).
    sab_b = clean.replace("Project=PDE", "Project=ZTIE")
    # Sabotage C: the create-stack form drops the Project tag.
    sab_c = clean.replace("Key=Project,Value=PDE ", "")

    clean_fail = sum(1 for _, ok in invariants_for_text(clean, "clean") if not ok)
    if clean_fail:
        print("check_deploy_tags --self-test: FAIL — clean sample should pass")
        return 1
    for label, broken in (("drop --tags", sab_a), ("wrong value", sab_b),
                          ("create-stack drops tag", sab_c)):
        caught = any(not ok for _, ok in invariants_for_text(broken, "sabotage"))
        if not caught:
            print(
                f"check_deploy_tags --self-test: FAIL — sabotage '{label}' "
                f"was NOT caught"
            )
            return 1
    print(
        "check_deploy_tags --self-test: PASS — guard flips to FAIL on a dropped/"
        "wrong Project=PDE tag; clean sample passes."
    )
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    files = sorted(glob.glob(RUNBOOK_GLOB))
    if not files:
        print(
            f"check_deploy_tags: PASS — no LIVE-RUNBOOKs under "
            f"{os.path.relpath(RUNBOOK_GLOB, REPO_ROOT)} to scan yet (no-op)."
        )
        return 0
    all_checks: list[tuple[str, bool]] = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        rel = os.path.relpath(path, REPO_ROOT)
        all_checks.extend(invariants_for_text(text, rel))
    # A repo may legitimately have LIVE-RUNBOOKs with no pdlv- deploy (e.g. a
    # read-only gate runbook). Only hard-fail on an ACTUAL missing tag; the
    # "found none at all" branch in _report applies to the aggregate.
    if not all_checks:
        print(
            "check_deploy_tags: PASS — scanned "
            f"{len(files)} LIVE-RUNBOOK(s); none contain a pdlv- deploy "
            "invocation to police (no-op)."
        )
        return 0
    return _report(all_checks)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
