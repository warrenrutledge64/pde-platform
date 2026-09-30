#!/usr/bin/env python3
"""Offline structural validation for the PDE cross-account trust-fabric template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / cfn-guard /
Checkov run operator-side / CI (see the Story 1.1 LIVE-RUNBOOK). This stdlib-only
checker is the OFFLINE proof bar: it confirms the Spoke execution-role template is
well-formed and that every RD-006 trust-fabric security invariant holds — in
particular the least-privilege + specific-Hub-role-trust + ExternalId properties.

Usage:  python3 infra/validate_trust_fabric.py
Exit:   0 = all invariants hold; 1 = one or more failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "spoke-execution-role.push-model.yaml"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _strip_comments(text: str) -> str:
    """Drop YAML comment lines so invariants test the TEMPLATE, not the prose.

    A '#' inside a quoted string is not a comment, but this template has none in
    quotes, so a simple 'first unquoted # to end-of-line' strip is safe and keeps
    the checker honest (e.g. an explanatory 'NOT AdministratorAccess' comment must
    not be mistaken for the policy actually granting AdministratorAccess).
    """
    out = []
    for line in text.splitlines():
        # Remove a trailing comment; keep the code part.
        hexs = line.split("#", 1)[0]
        out.append(hexs)
    return "\n".join(out)


def main() -> int:
    raw_with_comments = TEMPLATE.read_text(encoding="utf-8")
    raw = _strip_comments(raw_with_comments)
    flat = _norm(raw)

    checks: list[tuple[str, bool]] = [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- The Spoke execution role exists ---
        ("Spoke execution role is AWS::IAM::Role",
         "Type: AWS::IAM::Role" in raw),
        ("role has a bounded session duration",
         "MaxSessionDuration:" in raw),
        # --- RD-006: trust a SPECIFIC Hub role, never the Hub account root ---
        ("trust principal is a specific Hub ROLE ARN (role/<name>)",
         ":role/${HubDeployerRoleName}" in raw),
        ("trust principal is NOT the Hub account root",
         ":root" not in raw),
        ("trust action is sts:AssumeRole",
         "sts:AssumeRole" in raw),
        # --- Confused-deputy protection ---
        ("assume requires an ExternalId condition",
         "sts:ExternalId" in raw),
        ("ExternalId parameter is NoEcho (not echoed/committed)",
         bool(re.search(r"ExternalId:.*?NoEcho:\s*true", flat))),
        # --- Least privilege: NO wildcard admin ---
        ("permissions are a scoped managed policy, not AdministratorAccess",
         "AdministratorAccess" not in raw),
        ("no full wildcard action (\"Action: '*'\" / Action: \\\"*\\\")",
         not re.search(r"Action:\s*['\"]\*['\"]", raw)
         and "- \"*\"" not in raw and "- '*'" not in raw),
        ("CFN stack ops scoped to the pde- stack name prefix",
         "stack/${RolePrefix}*" in raw),
        ("grants concrete CloudFormation actions",
         "cloudformation:CreateStack" in raw
         and "cloudformation:ExecuteChangeSet" in raw),
        # --- ZTIE co-existence / naming discipline ---
        ("PDE naming prefix parameter present",
         "RolePrefix:" in raw and "pde-" in raw),
        ("resources tagged Project=PDE",
         "Value: PDE" in raw),
        ("role tagged with Component=trust-fabric",
         "trust-fabric" in raw),
        # --- Per-environment parameterization (deploy to each Spoke) ---
        ("environment is constrained to dev/sandbox/prod",
         bool(re.search(r"AllowedValues:\s*\[dev, sandbox, prod\]", flat))),
        ("Hub account id parameter defaults to 641628980935",
         "641628980935" in raw),
        # --- NOT deployed into the management account ---
        ("no reference to the management/root account 467866449172",
         "467866449172" not in raw),
        # --- Outputs export the role ARN for the Hub to consume ---
        ("exports the Spoke execution role ARN",
         "pde-spoke-execution-role-arn-" in raw),
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
    print(f"validate_trust_fabric: PASS — all {len(checks)} trust-fabric invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
