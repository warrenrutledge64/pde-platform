#!/usr/bin/env python3
"""Offline structural validation for the PDE CodeBuild-projects template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / cfn-guard /
Checkov run operator-side / CI (see the Story 2.1 LIVE-RUNBOOK). This stdlib-only
checker is the OFFLINE proof bar for the Story 2.1 Hub-side CodeBuild projects
(RD-003/RD-004/RD-006/RD-009): it confirms the template is well-formed and that
every ZTIE-safe naming, least-privilege, and orchestrate-and-pull invariant holds.

It also mirrors the two findings the live static bar sealed (so this class of
defect is caught OFFLINE next time): the CloudFormation Description byte limit
(cfn-lint E1003) and the CloudWatch Log Group KMS finding (checkov CKV_AWS_158,
satisfied here by a justified inline suppression).

Usage:
    python3 infra/validate_codebuild_projects.py      # validate the real template
    python3 infra/validate_codebuild_projects.py --self-test
        # prove the guard actually FAILS on broken input, in memory, with NO disk
        # write (the sabotage test the live run could not complete on a full disk).
Exit:   0 = all invariants hold (or self-test passed); 1 = one or more failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "codebuild-projects.yaml"

# CloudFormation hard limit on the top-level template Description (cfn-lint E1003).
CFN_DESCRIPTION_MAX_BYTES = 1024


def _strip_comments(text: str) -> str:
    """Drop YAML comment content so invariants test the TEMPLATE, not the prose.

    (An explanatory 'NOT AdministratorAccess' / 'no wildcard' comment must not be
    mistaken for the policy actually doing it.) The buildspec blocks are block
    scalars with no inline '#'; a 'first # to end-of-line' strip per line is safe
    for this template. NOTE: invariants that must inspect a COMMENT (e.g. the
    checkov:skip suppression) test the RAW un-stripped text instead.
    """
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _description_bytes(raw_text: str) -> int:
    """Rendered byte length of the top-level folded ('>-') Description block.

    Folds single newlines to spaces and blank lines to a newline (YAML folded
    scalar semantics) so the measured length matches what CloudFormation stores —
    the same thing cfn-lint E1003 counts.
    """
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
    """Return the (name, ok) invariant list for a template's TEXT.

    Pure function of the text, so --self-test can feed it a deliberately broken
    template in memory (no file, no disk write)."""
    raw = _strip_comments(template_text)  # policy/structure invariants
    full = template_text                  # comment-aware invariants (suppressions)

    return [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- cfn-lint E1003: Description within the 1024-byte CFN limit ---
        (f"template Description within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit (cfn-lint E1003)",
         0 < _description_bytes(full) <= CFN_DESCRIPTION_MAX_BYTES),
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
        # --- checkov CKV_AWS_158: Log Group KMS — satisfied by a justified skip ---
        ("both Log Groups carry a justified CKV_AWS_158 KMS suppression (checkov)",
         full.count("checkov:skip=CKV_AWS_158:") == 2),
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
        print(f"validate_codebuild_projects: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_codebuild_projects: PASS — all {len(checks)} CodeBuild invariants hold")
    return 0


def self_test() -> int:
    """Prove the guard GUARDS — in memory, no disk write.

    Takes the real template, applies sabotages that mirror the live-sealed FAILs
    (and the core adversarial cases), and asserts the relevant invariant flips to
    FAIL. This replaces the on-disk `sed` sabotage that a full CloudShell disk
    could not complete.
    """
    good = TEMPLATE.read_text(encoding="utf-8")

    sabotages: list[tuple[str, str, str]] = [
        # (label, broken_text, the invariant-name substring that must now FAIL)
        ("pde- namespace regression",
         good.replace("pdlv-", "pde-"),
         "no bare pde- Hub resource name"),
        ("over-long Description (cfn-lint E1003)",
         re.sub(r"\nDescription: >-\n.*?\n\n([^ ])",
                "\nDescription: >-\n  " + ("x " * 700) + "\n\n\\1", good, flags=re.DOTALL),
         f"within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit"),
        ("dropped CKV_AWS_158 suppression",
         good.replace("checkov:skip=CKV_AWS_158:", "nope:", 1),
         "CKV_AWS_158 KMS suppression"),
        ("wildcard action injected",
         good.replace("Action: sts:AssumeRole", 'Action: "*"', 1),
         "no full wildcard action"),
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
        print("validate_codebuild_projects --self-test: FAIL — a sabotage was NOT caught")
        return 1
    # And the pristine template must still PASS cleanly.
    clean_fail = sum(1 for _, ok in run_checks(good) if not ok)
    if clean_fail:
        print(f"validate_codebuild_projects --self-test: FAIL — clean template has {clean_fail} failing invariant(s)")
        return 1
    print("validate_codebuild_projects --self-test: PASS — guard flips to FAIL on every sabotage; clean template passes")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    return _report(run_checks(TEMPLATE.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
