#!/usr/bin/env python3
"""Offline structural validation for the PDE Hub-orchestrator-role template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / Checkov run
operator-side / in CI. This stdlib-only checker is the OFFLINE proof bar for the
Story 3.2 unified Hub orchestrator (RD-003/RD-004/RD-006/RD-009) — the middle
identity of the two-hop deploy chain (pdlv-codebuild-service-role ->
pde-hub-orchestrator -> pde-member-execution-<env>). It confirms the role is a
PURE PASS-THROUGH chokepoint: its only permission is sts:AssumeRole scoped to the
three named member role ARNs, its trust is pinned to EXACTLY the CodeBuild deploy
service role (never the Hub root), and a permissions boundary caps it at exactly
that so a future over-permissive identity-policy edit cannot escalate it.

Usage:
    python3 infra/validate_hub_orchestrator_role.py       # validate the real template
    python3 infra/validate_hub_orchestrator_role.py --self-test
        # prove the guard FAILS on broken input, in memory, with NO disk write.
Exit:   0 = all invariants hold (or self-test passed); 1 = one or more failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "hub-orchestrator-role.yaml"

# CloudFormation hard limit on the top-level template Description (cfn-lint E1003).
CFN_DESCRIPTION_MAX_BYTES = 1024


def _strip_comments(text: str) -> str:
    """Drop YAML comment content so invariants test the TEMPLATE, not the prose."""
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _description_bytes(raw_text: str) -> int:
    """Rendered byte length of the top-level folded ('>-') Description block."""
    m = re.search(r"\nDescription: >-\n(.*?)\n\n[^ ]", raw_text, re.DOTALL)
    if not m:
        return 0
    body = m.group(1)
    chunks: list[str] = []
    rendered = ""
    for line in body.split("\n"):
        if line.strip() == "":
            rendered += " ".join(chunks) + "\n"
            chunks = []
        else:
            chunks.append(line.strip())
    rendered += " ".join(chunks)
    return len(rendered.strip().encode("utf-8"))


def run_checks(template_text: str) -> list[tuple[str, bool]]:
    """Return the (name, ok) invariant list for a template's TEXT (pure function)."""
    raw = _strip_comments(template_text)

    # Pull out the role's assume-role (trust) policy block vs. its identity grant.
    trust_m = re.search(
        r"AssumeRolePolicyDocument:(?P<body>.*?)(?:\n      ManagedPolicyArns:|\n      Tags:)",
        raw, re.DOTALL,
    )
    trust = trust_m.group("body") if trust_m else ""

    return [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        (f"template Description within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit (cfn-lint E1003)",
         0 < _description_bytes(template_text) <= CFN_DESCRIPTION_MAX_BYTES),
        ("template Description is pure ASCII (no em-dash / smart quote breaks CreateRole)",
         _description_bytes_is_ascii(template_text)),
        # --- The orchestrator role itself ---
        ("declares exactly one IAM role (the orchestrator)",
         raw.count("Type: AWS::IAM::Role") == 1),
        ("role name is pinned to pde-hub-orchestrator (the Phase-1 member-trust principal)",
         bool(re.search(r'AllowedPattern:\s*"\^pde-hub-orchestrator\$"', raw))
         and bool(re.search(r"Default:\s*pde-hub-orchestrator\b", raw))),
        ("role attaches a PermissionsBoundary",
         "PermissionsBoundary: !Ref OrchestratorPermissionsBoundary" in raw),
        ("role has a bounded session duration",
         "MaxSessionDuration:" in raw),
        # --- Trust: pinned to EXACTLY the CodeBuild deploy service role (hop 1) ---
        ("trusts a SPECIFIC role ARN (the CodeBuild service role), via sts:AssumeRole",
         "sts:AssumeRole" in trust
         and "role/${CodeBuildServiceRoleName}" in trust),
        ("trust is NOT the Hub account root",
         ":root" not in trust),
        ("CodeBuild service-role param is pinned to the pdlv- deploy role",
         bool(re.search(r"Default:\s*pdlv-codebuild-service-role\b", raw))),
        ("trust does not name any member account id (members are the OUTBOUND target, not inbound)",
         not re.search(r"946509368326|586917955591|466494951534", trust)),
        # --- Identity + boundary: ONLY sts:AssumeRole into the three member roles ---
        ("the only action anywhere is sts:AssumeRole (pure pass-through, no local Hub power)",
         _only_action_is_assume_role(raw)),
        ("identity policy assumes the three SPECIFIC member roles (dev/sandbox/prod)",
         "role/${MemberRoleName}-dev" in raw
         and "role/${MemberRoleName}-sandbox" in raw
         and "role/${MemberRoleName}-prod" in raw),
        ("the two assume grants (identity + boundary) target member ARNs by !Sub (3 each = 6)",
         raw.count("role/${MemberRoleName}-dev") == 2
         and raw.count("role/${MemberRoleName}-sandbox") == 2
         and raw.count("role/${MemberRoleName}-prod") == 2),
        ("a permissions-boundary managed policy exists",
         "OrchestratorPermissionsBoundary:" in raw
         and raw.count("Type: AWS::IAM::ManagedPolicy") == 2),
        ("orchestrator is BLIND to the ExternalId secret (no ssm / no secretsmanager)",
         "ssm:" not in raw and "secretsmanager:" not in raw
         and "GetParameter" not in raw),
        ("orchestrator has NO local Hub power (no cloudformation / s3 / logs / kms grant)",
         not re.search(r"\b(cloudformation|s3|logs|kms|codebuild|dynamodb):", raw)),
        # --- Least privilege / no escalation ---
        ("no AdministratorAccess / PowerUser",
         "AdministratorAccess" not in raw and "PowerUserAccess" not in raw),
        ("no full wildcard action",
         not re.search(r"Action:\s*['\"]\*['\"]", raw)
         and "- \"*\"" not in raw and "- '*'" not in raw),
        ("no wildcard resource on any statement (inline or list item)",
         not re.search(r"Resource:\s*['\"]\*['\"]", raw)
         and not re.search(r"^\s*-\s*['\"]\*['\"]\s*$", raw, re.MULTILINE)),
        # --- ZTIE-safe naming (RD-009): pdlv- for the Hub STACK resources ---
        ("boundary + identity managed policies use the ${NamePrefix} pdlv- prefix",
         "${NamePrefix}hub-orchestrator-boundary" in raw
         and "${NamePrefix}hub-orchestrator-assume-members" in raw),
        ("name prefix parameter is exactly pdlv- (RD-009)",
         bool(re.search(r'AllowedPattern:\s*"\^pdlv-\$"', raw))),
        ("Project=PDE tag on the role",
         "Key: Project, Value: PDE" in raw),
        # --- Zero-touch root / ZTIE-safe account scope ---
        ("no reference to the management/root account 467866449172",
         "467866449172" not in raw),
        ("Hub-only: no Pipeline-Forensics (ZTIE) account 360999005254",
         "360999005254" not in raw),
        ("member account ids are the PDE members (dev/sandbox/prod)",
         "946509368326" in raw and "586917955591" in raw and "466494951534" in raw),
        ("exports the orchestrator role ARN + boundary ARN (pdlv- export names)",
         "pdlv-hub-orchestrator-role-arn" in raw
         and "pdlv-hub-orchestrator-boundary-arn" in raw),
    ]


def _only_action_is_assume_role(raw: str) -> bool:
    """Every `Action:` in the template is exactly sts:AssumeRole (pass-through)."""
    actions = re.findall(r"Action:\s*(.+)", raw)
    # Each Action line here is a scalar `sts:AssumeRole` (no list form in this template).
    return bool(actions) and all(a.strip() == "sts:AssumeRole" for a in actions)


def _description_bytes_is_ascii(raw_text: str) -> bool:
    m = re.search(r"\nDescription: >-\n(.*?)\n\n[^ ]", raw_text, re.DOTALL)
    if not m:
        return False
    try:
        m.group(1).encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def _report(checks: list[tuple[str, bool]]) -> int:
    width = max(len(n) for n, _ in checks)
    failed = 0
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{status}] {name.ljust(width)}")
    print()
    if failed:
        print(f"validate_hub_orchestrator_role: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_hub_orchestrator_role: PASS — all {len(checks)} orchestrator invariants hold")
    return 0


def self_test() -> int:
    """Prove the guard GUARDS — in memory, no disk write."""
    good = TEMPLATE.read_text(encoding="utf-8")

    sabotages: list[tuple[str, str, str]] = [
        # (label, broken_text, invariant-name substring that must now FAIL)
        ("trust widened to the Hub account root",
         good.replace(
             'AWS: !Sub "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/${CodeBuildServiceRoleName}"',
             'AWS: !Sub "arn:${AWS::Partition}:iam::${AWS::AccountId}:root"', 1),
         "trust is NOT the Hub account root"),
        ("boundary removed from the role",
         good.replace("PermissionsBoundary: !Ref OrchestratorPermissionsBoundary\n", "", 1),
         "role attaches a PermissionsBoundary"),
        ("local Hub power injected (cloudformation action)",
         good.replace("Action: sts:AssumeRole", "Action: cloudformation:CreateStack", 1),
         "the only action anywhere is sts:AssumeRole"),
        ("a local SSM read injected (orchestrator must stay blind to the secret)",
         good.replace(
             "            Action: sts:AssumeRole",
             "            Action: ssm:GetParameter", 1),
         "BLIND to the ExternalId secret"),
        ("wildcard resource injected on the identity grant",
         good.replace(
             '              - !Sub "arn:${AWS::Partition}:iam::${DevAccountId}:role/${MemberRoleName}-dev"',
             '              - "*"', 1),
         "no wildcard resource on any statement"),
        ("pde- Hub stack-resource namespace regression (boundary policy name)",
         good.replace("${NamePrefix}hub-orchestrator-boundary", "pde-hub-orchestrator-boundary", 1),
         "pdlv- prefix"),
    ]

    all_ok = True
    for label, broken, must_fail_substr in sabotages:
        checks = run_checks(broken)
        target = [(n, ok) for n, ok in checks if must_fail_substr in n]
        hit = bool(target) and all(not ok for _, ok in target)
        status = "PASS" if hit else "FAIL"
        if not hit:
            all_ok = False
        print(f"  [{status}] guard catches: {label}")
    print()
    if not all_ok:
        print("validate_hub_orchestrator_role --self-test: FAIL — a sabotage was NOT caught")
        return 1
    clean_fail = sum(1 for _, ok in run_checks(good) if not ok)
    if clean_fail:
        print(f"validate_hub_orchestrator_role --self-test: FAIL — clean template has {clean_fail} failing invariant(s)")
        return 1
    print("validate_hub_orchestrator_role --self-test: PASS — guard flips to FAIL on every sabotage; clean template passes")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    return _report(run_checks(TEMPLATE.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
