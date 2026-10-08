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
        # --- RD-006 orchestrate-and-pull, Story 3.2 TWO-HOP: the service role's only
        #     cross-account power is sts:AssumeRole into the SINGLE Hub orchestrator
        #     role (hop 1); the orchestrator does the member assume (hop 2). No broad
        #     Hub deploy policy; the service role holds NO direct member-assume. ---
        ("the only cross-account action is sts:AssumeRole",
         "sts:AssumeRole" in raw),
        ("service-role assume targets ONLY the Hub orchestrator role (hop 1)",
         "role/${OrchestratorRoleName}" in raw),
        # The member ARN may appear ONLY as the hop-2 TARGET_ROLE_ARN env-var VALUE
        # (what the buildspec assumes), NEVER as an IAM policy Resource grant on the
        # service role. So: no policy-list "- ...role/${MemberRoleName}-<env>" line.
        ("service role has NO direct member-role assume GRANT (orchestrator does hop 2)",
         not re.search(r"-\s+!Sub\s+\"arn:[^\"]*role/\$\{MemberRoleName\}-(dev|sandbox|prod)\"", raw)),
        ("orchestrator role name param defaults to pdlv-hub-orchestrator (RD-009; pdlv--only pattern)",
         bool(re.search(r"Default:\s*pdlv-hub-orchestrator\b", raw))
         and bool(re.search(r"OrchestratorRoleName:.*?AllowedPattern:\s*\"\^pdlv-", raw, re.DOTALL))),
        ("deploy project has NO direct cloudformation:* GRANT (deploy runs in-member)",
         "cloudformation:CreateStack" not in raw
         and "cloudformation:ExecuteChangeSet" not in raw),
        ("member role name param is the Story 1.1 role (pde-member-execution)",
         bool(re.search(r"Default:\s*pde-member-execution\b", raw))),
        # --- Story 3.2 secret-at-the-edge: the two /pdlv/ SecureStrings are resolved
        #     at runtime (PARAMETER_STORE), scoped to EXACTLY those two params, and
        #     NEVER passed as plaintext / committed. ---
        ("ExternalId + repo token resolved via PARAMETER_STORE (not PLAINTEXT secrets)",
         raw.count("Type: PARAMETER_STORE") == 2),
        ("the ExternalId SSM param is /pdlv/ namespaced",
         bool(re.search(r"Default:\s*/pdlv/[A-Za-z0-9_./-]*external-id", raw))),
        ("the repo-token SSM param is /pdlv/ namespaced",
         bool(re.search(r"Default:\s*/pdlv/[A-Za-z0-9_./-]*repo-token", raw))),
        ("ssm:GetParameter scoped to the two named /pdlv/ parameter ARNs only",
         "ssm:GetParameter" in raw
         and "parameter${ExternalIdParameterName}" in raw
         and "parameter${RepoTokenParameterName}" in raw),
        # CodeBuild resolves PARAMETER_STORE env vars via the BATCH action
        # ssm:GetParameters (plural) — a DISTINCT IAM action from the singular
        # ssm:GetParameter. Omitting it denies DeployDev at DOWNLOAD_SOURCE with
        # "not authorized to perform: ssm:GetParameters" (Story 3.2 Attempt 9).
        ("ssm:GetParameters (plural, the PARAMETER_STORE batch action) is granted",
         bool(re.search(r"ssm:GetParameters\b", raw))),
        ("kms:Decrypt is constrained to via-SSM only (kms:ViaService)",
         "kms:Decrypt" in raw and "kms:ViaService" in raw),
        ("no plaintext ExternalId / repo-token value in the template",
         "set-this-at-deploy-time" not in raw
         and "x-access-token:ghp_" not in raw),
        # --- The deploy buildspec is a REAL two-hop deploy, not a stub ---
        ("deploy buildspec performs HOP 1 (assume the orchestrator)",
         "assume-role --role-arn \"$ORCHESTRATOR_ROLE_ARN\"" in raw),
        ("deploy buildspec performs HOP 2 (assume the member with --external-id)",
         "assume-role --role-arn \"$TARGET_ROLE_ARN\"" in raw
         and "--external-id \"$EXTERNAL_ID\"" in raw),
        ("deploy buildspec fast-fails on an empty ExternalId / repo token",
         "EXTERNAL_ID is empty" in raw and "REPO_TOKEN is empty" in raw),
        ("deploy buildspec keeps secrets out of the log (set +x)",
         "set +x" in raw),
        ("deploy buildspec runs a REAL cloudformation deploy of the artifact",
         "cloudformation deploy" in raw and "$ARTIFACT_STACK_NAME" in raw),
        ("the in-member deploy carries the Project=PDE stack tag (OD-012)",
         bool(re.search(r"--tags\s+Project=PDE\b", raw))),
        ("deploy buildspec VERIFIES the live result (describe-stacks + describe-table)",
         "cloudformation describe-stacks" in raw and "dynamodb describe-table" in raw),
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
        ("references the Dev member account id (the default hop-2 target)",
         "946509368326" in raw),
        ("no Sandbox/Prod member ids needed here (two-hop: orchestrator targets members)",
         "586917955591" not in raw and "466494951534" not in raw),
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
        # Story 3.2: a plaintext ExternalId secret regression (back to PARAMETER_STORE
        # -> PLAINTEXT) must be caught — the secret must stay resolved at the edge.
        ("ExternalId downgraded from PARAMETER_STORE to PLAINTEXT",
         good.replace("Type: PARAMETER_STORE", "Type: PLAINTEXT", 1),
         "resolved via PARAMETER_STORE"),
        # VD-9 Attempt 9: dropping ssm:GetParameters (plural) — the PARAMETER_STORE
        # batch action CodeBuild actually calls — must be caught. Its absence is the
        # live "not authorized to perform: ssm:GetParameters" DeployDev denial.
        ("ssm:GetParameters (plural) dropped — the live Attempt-9 DeployDev denial",
         good.replace("              - ssm:GetParameters\n", "", 1),
         "ssm:GetParameters"),
        # Story 3.2: dropping the hop-2 --external-id (the Phase-1 member trust needs
        # it) must be caught.
        ("hop-2 --external-id dropped",
         good.replace('--external-id "$EXTERNAL_ID"', ""),
         "performs HOP 2"),
        # Story 3.2: broadening the service-role assume back to a direct member-role
        # grant (bypassing the orchestrator chokepoint) must be caught.
        ("direct member-assume grant re-introduced on the service role",
         good.replace(
             '              - !Sub "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/${OrchestratorRoleName}"',
             '              - !Sub "arn:${AWS::Partition}:iam::${DevAccountId}:role/${MemberRoleName}-dev"',
             1),
         "NO direct member-role assume GRANT"),
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
