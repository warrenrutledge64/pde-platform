#!/usr/bin/env python3
"""Offline structural validation for the PDE CodeBuild-projects template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / cfn-guard /
Checkov run operator-side / CI (see the Story 2.1 LIVE-RUNBOOK). This stdlib-only
checker is the OFFLINE proof bar for the Story 2.1 Hub-side CodeBuild projects
(RD-003/RD-004/RD-006/RD-009): it confirms the template is well-formed and that
every ZTIE-safe naming, least-privilege, and orchestrate-and-pull invariant holds.

Usage:  python3 infra/validate_codebuild_projects.py
Exit:   0 = all invariants hold; 1 = one or more failed.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "codebuild-projects.yaml"


def _strip_comments(text: str) -> str:
    """Drop YAML comment content so invariants test the TEMPLATE, not the prose.

    (An explanatory 'NOT AdministratorAccess' / 'no wildcard' comment must not be
    mistaken for the policy actually doing it.) The buildspec blocks are block
    scalars with no inline '#'; a 'first # to end-of-line' strip per line is safe
    for this template.
    """
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def main() -> int:
    raw = _strip_comments(TEMPLATE.read_text(encoding="utf-8"))

    checks: list[tuple[str, bool]] = [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- Both CodeBuild projects exist (Lint + Deploy) ---
        ("declares two AWS::CodeBuild::Project resources",
         raw.count("Type: AWS::CodeBuild::Project") == 2),
        ("Lint project present",
         "LintProject:" in raw),
        ("Deploy project present",
         "DeployProject:" in raw),
        # --- ZTIE-safe naming (RD-009): pdlv-, never pde- ---
        ("name prefix parameter is exactly pdlv- (RD-009)",
         bool(re.search(r'AllowedPattern:\s*"\^pdlv-\$"', raw))),
        ("prefix default is pdlv-",
         bool(re.search(r"Default:\s*pdlv-", raw))),
        ("project names use the ${NamePrefix} prefix",
         '!Sub "${NamePrefix}lint"' in raw
         and '!Sub "${NamePrefix}deploy"' in raw),
        ("no bare pde- Hub resource name (ZTIE's namespace)",
         not re.search(r'(Name|RoleName|LogGroupName|ManagedPolicyName):\s*[!"\s]*[^\n]*"?pde-', raw)),
        ("exports use the pdlv- prefix",
         "pdlv-codebuild-lint-project-name" in raw
         and "pdlv-codebuild-deploy-project-name" in raw),
        # --- Project=PDE tagging on every resource ---
        ("resources tagged Project=PDE",
         "Value: PDE" in raw),
        ("every taggable resource is Project=PDE-tagged (2 log groups + role + 2 projects = 5; managed policies have no Tags)",
         raw.count("Key: Project, Value: PDE") == 5),
        # --- Least privilege: NO wildcard admin (Universal Criterion 3) ---
        ("no AdministratorAccess",
         "AdministratorAccess" not in raw),
        ("no full wildcard action",
         not re.search(r"Action:\s*['\"]\*['\"]", raw)
         and "- \"*\"" not in raw and "- '*'" not in raw),
        ("no wildcard resource on an IAM policy statement",
         not re.search(r"Resource:\s*['\"]\*['\"]", raw)),
        ("no attached AWS-managed admin/poweruser policy ARN",
         "iam::aws:policy/AdministratorAccess" not in raw
         and "iam::aws:policy/PowerUserAccess" not in raw),
        # --- RD-006 orchestrate-and-pull: cross-account power is ONLY AssumeRole
        #     into the SPECIFIC member roles, no broad Hub deploy policy ---
        ("the only cross-account action is sts:AssumeRole",
         "sts:AssumeRole" in raw),
        ("assume targets the SPECIFIC member execution roles (role/<name>-<env>)",
         "role/${MemberRoleName}-dev" in raw
         and "role/${MemberRoleName}-sandbox" in raw
         and "role/${MemberRoleName}-prod" in raw),
        ("deploy project has NO direct cloudformation:* grant (deploy runs in-member)",
         "cloudformation:CreateStack" not in raw
         and "cloudformation:ExecuteChangeSet" not in raw),
        ("member role name param is the Story 1.1 role (pde-member-execution)",
         bool(re.search(r"Default:\s*pde-member-execution\b", raw))),
        # --- Service role is scoped + trusted only by CodeBuild ---
        ("a CodeBuild service role exists",
         "CodeBuildServiceRole:" in raw and "Type: AWS::IAM::Role" in raw),
        ("service role trusts only codebuild.amazonaws.com",
         "Service: codebuild.amazonaws.com" in raw),
        ("service-trust is confused-deputy scoped to this account (aws:SourceAccount)",
         '"aws:SourceAccount": !Ref "AWS::AccountId"' in raw),
        ("service role has a bounded session duration",
         "MaxSessionDuration:" in raw),
        ("permissions are scoped managed policies attached by Ref",
         "!Ref CodeBuildLogsPolicy" in raw
         and "!Ref CodeBuildAssumeMemberPolicy" in raw),
        # --- Logs scoped to this project's OWN log groups (not logs:* on *) ---
        ("logs scoped to the project's own log group ARNs",
         "!GetAtt LintLogGroup.Arn" in raw
         and "!GetAtt DeployLogGroup.Arn" in raw),
        ("log groups have a bounded retention",
         "RetentionInDays:" in raw),
        # --- Hardening on both projects ---
        ("CodeBuild containers are not privileged",
         raw.count("PrivilegedMode: false") == 2
         and "PrivilegedMode: true" not in raw),
        ("both projects have a build timeout",
         raw.count("TimeoutInMinutes:") == 2),
        ("Lint buildspec runs the static bar (cfn-lint / checkov)",
         "cfn-lint" in raw and "checkov" in raw),
        # --- ZTIE-safe / zero-touch-root ---
        ("no reference to the management/root account 467866449172",
         "467866449172" not in raw),
        ("Hub-only: no Pipeline-Forensics (ZTIE) account 360999005254",
         "360999005254" not in raw),
        ("member account ids are the PDE members (dev/sandbox/prod)",
         "946509368326" in raw and "586917955591" in raw and "466494951534" in raw),
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
        print(f"validate_codebuild_projects: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_codebuild_projects: PASS — all {len(checks)} CodeBuild invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
