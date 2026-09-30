#!/usr/bin/env python3
"""Offline structural validation for the PDE member-execution-role template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / cfn-guard /
Checkov run operator-side / CI (see the Story 1.1 LIVE-RUNBOOK). This stdlib-only
checker is the OFFLINE proof bar for the RD-006 **orchestrate-and-pull** tier-1
trust fabric: it confirms the member execution-role template is well-formed and
that every trust-direction + least-privilege invariant holds.

Usage:  python3 infra/validate_trust_fabric.py
Exit:   0 = all invariants hold; 1 = one or more failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "member-execution-role.yaml"


def _strip_comments(text: str) -> str:
    """Drop YAML comment content so invariants test the TEMPLATE, not the prose.

    (An explanatory 'NOT AdministratorAccess' / 'not :root' comment must not be
    mistaken for the policy actually granting it.) This template has no '#' inside
    quoted strings, so a 'first # to end-of-line' strip per line is safe.
    """
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def main() -> int:
    raw = _strip_comments(TEMPLATE.read_text(encoding="utf-8"))
    flat = _norm(raw)

    checks: list[tuple[str, bool]] = [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- The member execution role exists ---
        ("member execution role is AWS::IAM::Role",
         "Type: AWS::IAM::Role" in raw),
        ("role has a bounded session duration",
         "MaxSessionDuration:" in raw),
        # --- RD-006 orchestrate-and-pull: trust a SPECIFIC Hub role, not root ---
        ("trust principal is a specific Hub ROLE ARN (role/<name>)",
         ":role/${HubOrchestratorRoleName}" in raw),
        ("trust principal is NOT the Hub account root",
         ":root" not in raw),
        ("trust action is sts:AssumeRole",
         "sts:AssumeRole" in raw),
        ("trust is the Hub ORCHESTRATOR role (orchestrate-and-pull, not a pusher)",
         "HubOrchestratorRoleName" in raw),
        # --- Confused-deputy protection ---
        ("assume requires an ExternalId condition",
         "sts:ExternalId" in raw),
        ("ExternalId parameter is NoEcho (not echoed/committed)",
         bool(re.search(r"ExternalId:.*?NoEcho:\s*true", flat))),
        # --- Least privilege: NO wildcard admin ---
        ("permissions are a scoped managed policy, not AdministratorAccess",
         "AdministratorAccess" not in raw),
        ("no full wildcard action",
         not re.search(r"Action:\s*['\"]\*['\"]", raw)
         and "- \"*\"" not in raw and "- '*'" not in raw),
        ("local CFN ops scoped to the pde- stack name prefix",
         "stack/${RolePrefix}*" in raw),
        ("grants concrete CloudFormation actions",
         "cloudformation:CreateStack" in raw
         and "cloudformation:ExecuteChangeSet" in raw),
        # --- Local execution scoped to THIS member account ---
        ("CFN ops scoped to this member account (AWS::AccountId)",
         "${AWS::AccountId}:stack/${RolePrefix}*" in raw),
        # --- ZTIE co-existence / naming + model discipline ---
        ("PDE naming prefix parameter present",
         "RolePrefix:" in raw and "pde-" in raw),
        ("resources tagged Project=PDE",
         "Value: PDE" in raw),
        ("tagged Model=orchestrate-and-pull",
         "orchestrate-and-pull" in raw),
        ("environment constrained to dev/sandbox/prod",
         bool(re.search(r"AllowedValues:\s*\[dev, sandbox, prod\]", flat))),
        ("Hub account id parameter defaults to 641628980935",
         "641628980935" in raw),
        # --- NOT deployed into the management account ---
        ("no reference to the management/root account 467866449172",
         "467866449172" not in raw),
        # --- Outputs export the role ARN for the Hub orchestrator to direct ---
        ("exports the member execution role ARN",
         "pde-member-execution-role-arn-" in raw),
    ]

    width = max(len(n) for n, _ in checks)
    failed = 0
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{status}] {name.ljust(width)}")

    print()
    if failed:
        print(f"validate_trust_fabric: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_trust_fabric: PASS — all {len(checks)} orchestrate-and-pull invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
