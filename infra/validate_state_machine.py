#!/usr/bin/env python3
"""Offline structural validation for the PDE Step Functions state-machine template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / cfn-guard /
Checkov run operator-side / CI (see the Story 2.2 LIVE-RUNBOOK). This stdlib-only
checker is the OFFLINE proof bar for the Story 2.2 Hub-side promotion state machine
(RD-003/RD-004/RD-006/RD-009): it confirms the template is well-formed, that the
embedded Amazon States Language (ASL) definition sequences Dev -> Sandbox -> Prod
with NATIVE manual-approval paused states (.waitForTaskToken), that every promotion
starts the Story 2.1 pdlv-deploy CodeBuild project, and that every ZTIE-safe naming
and least-privilege invariant holds.

It also mirrors the two findings the Story 2.1 live static bar sealed (so this class
of defect is caught OFFLINE here too): the CloudFormation Description byte limit
(cfn-lint E1003) and the CloudWatch Log Group KMS finding (checkov CKV_AWS_158,
satisfied by a justified inline suppression).

Usage:
    python3 infra/validate_state_machine.py      # validate the real template
    python3 infra/validate_state_machine.py --self-test
        # prove the guard actually FAILS on broken input, in memory, with NO disk
        # write (the disk-independent sabotage test, per the Story 2.1 OD-007 lesson).
Exit:   0 = all invariants hold (or self-test passed); 1 = one or more failed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "state-machine.yaml"

# CloudFormation hard limit on the top-level template Description (cfn-lint E1003).
CFN_DESCRIPTION_MAX_BYTES = 1024


def _strip_comments(text: str) -> str:
    """Drop YAML comment content so invariants test the TEMPLATE, not the prose.

    (An explanatory 'NOT AdministratorAccess' / 'no wildcard' comment must not be
    mistaken for the policy actually doing it.) The DefinitionString block is a block
    scalar of JSON with no inline '#'; a 'first # to end-of-line' strip per line is
    safe for this template. NOTE: invariants that must inspect a COMMENT (e.g. the
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


def _extract_asl(raw_text: str) -> dict | None:
    """Pull the inline ``DefinitionString: |`` block and parse it as JSON (ASL).

    The block is an 8-space-indented JSON literal terminated by the resource's
    ``Tags:`` key. Returns the parsed object, or None if it is absent/unparseable
    (so the structural ASL invariants fail loudly rather than silently pass).
    """
    m = re.search(r"\n      DefinitionString: \|\n(.*?)\n      Tags:", raw_text, re.DOTALL)
    if not m:
        return None
    block = m.group(1)
    dedented = "\n".join(
        line[8:] if line.startswith(" " * 8) else line for line in block.split("\n")
    )
    try:
        return json.loads(dedented)
    except (ValueError, TypeError):
        return None


def run_checks(template_text: str) -> list[tuple[str, bool]]:
    """Return the (name, ok) invariant list for a template's TEXT.

    Pure function of the text, so --self-test can feed it a deliberately broken
    template in memory (no file, no disk write)."""
    raw = _strip_comments(template_text)  # policy/structure invariants
    full = template_text                  # comment-aware invariants (suppressions)
    asl = _extract_asl(template_text)     # parsed Amazon States Language definition
    states = (asl or {}).get("States", {}) if isinstance(asl, dict) else {}

    def _state(name: str) -> dict:
        s = states.get(name, {})
        return s if isinstance(s, dict) else {}

    def _is_startbuild_sync(name: str) -> bool:
        s = _state(name)
        return s.get("Type") == "Task" and s.get("Resource") == "arn:aws:states:::codebuild:startBuild.sync"

    def _is_approval_pause(name: str) -> bool:
        s = _state(name)
        return (
            s.get("Type") == "Task"
            and s.get("Resource") == "arn:aws:states:::sns:publish.waitForTaskToken"
        )

    def _deploy_env(name: str, env: str) -> bool:
        """The deploy task overrides TARGET_ENV=<env> and passes a TARGET_ROLE_ARN
        + EXTERNAL_ID (the member-role assume inputs), per RD-006."""
        params = _state(name).get("Parameters", {})
        if params.get("ProjectName") != "${DeployProjectName}":
            return False
        overrides = params.get("EnvironmentVariablesOverride", [])
        names = {o.get("Name"): o.get("Value") for o in overrides if isinstance(o, dict)}
        return (
            names.get("TARGET_ENV") == env
            and "TARGET_ROLE_ARN" in names
            and "EXTERNAL_ID" in names
        )

    return [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- cfn-lint E1003: Description within the 1024-byte CFN limit ---
        (f"template Description within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit (cfn-lint E1003)",
         0 < _description_bytes(full) <= CFN_DESCRIPTION_MAX_BYTES),
        # --- The state machine exists and is STANDARD (approval pauses can outlast EXPRESS) ---
        ("declares one AWS::StepFunctions::StateMachine",
         raw.count("Type: AWS::StepFunctions::StateMachine") == 1),
        ("state machine is STANDARD type (manual-approval pause can outlast EXPRESS)",
         "StateMachineType: STANDARD" in raw),
        # --- ASL is present and parses as JSON ---
        ("inline ASL DefinitionString parses as JSON",
         asl is not None),
        ("ASL StartAt is DeployDev",
         isinstance(asl, dict) and asl.get("StartAt") == "DeployDev"),
        # --- Dev -> Sandbox -> Prod sequence via the three deploy tasks ---
        ("DeployDev is a codebuild:startBuild.sync task",
         _is_startbuild_sync("DeployDev")),
        ("DeploySandbox is a codebuild:startBuild.sync task",
         _is_startbuild_sync("DeploySandbox")),
        ("DeployProd is a codebuild:startBuild.sync task",
         _is_startbuild_sync("DeployProd")),
        ("DeployDev overrides TARGET_ENV=dev + role/external-id",
         _deploy_env("DeployDev", "dev")),
        ("DeploySandbox overrides TARGET_ENV=sandbox + role/external-id",
         _deploy_env("DeploySandbox", "sandbox")),
        ("DeployProd overrides TARGET_ENV=prod + role/external-id",
         _deploy_env("DeployProd", "prod")),
        ("promotion order is Dev -> AwaitSandboxApproval -> Sandbox -> AwaitProdApproval -> Prod",
         _state("DeployDev").get("Next") == "AwaitSandboxApproval"
         and _state("AwaitSandboxApproval").get("Next") == "DeploySandbox"
         and _state("DeploySandbox").get("Next") == "AwaitProdApproval"
         and _state("AwaitProdApproval").get("Next") == "DeployProd"
         and _state("DeployProd").get("Next") == "PromotionSucceeded"),
        # --- NATIVE manual-approval paused states before Sandbox and before Prod ---
        ("manual-approval pause before Sandbox (waitForTaskToken, not a timer)",
         _is_approval_pause("AwaitSandboxApproval")),
        ("manual-approval pause before Prod (waitForTaskToken, not a timer)",
         _is_approval_pause("AwaitProdApproval")),
        ("exactly two waitForTaskToken approval pauses",
         raw.count("sns:publish.waitForTaskToken") == 2),
        ("approval pauses carry the Step Functions task token ($$.Task.Token)",
         raw.count('"taskToken.$": "$$.Task.Token"') == 2),
        ("the pause is NOT faked with a Wait/timer state",
         '"Type": "Wait"' not in raw),
        # --- The deploy tasks START the Story 2.1 pdlv-deploy project ---
        ("deploy tasks start the pdlv-deploy project (DefinitionSubstitutions ${DeployProjectName})",
         '"ProjectName": "${DeployProjectName}"' in raw
         and "DeployProjectName: !Ref DeployProjectName" in raw),
        ("deploy project param defaults to pdlv-deploy",
         bool(re.search(r"Default:\s*pdlv-deploy\b", raw))),
        # --- ZTIE-safe naming (RD-009): pdlv-, never pde- ---
        ("name prefix parameter is exactly pdlv- (RD-009)",
         bool(re.search(r'AllowedPattern:\s*"\^pdlv-\$"', raw))),
        ("prefix default is pdlv-",
         bool(re.search(r"Default:\s*pdlv-\s*$", raw, re.MULTILINE))),
        ("state machine / role / topic names use the ${NamePrefix} prefix",
         '!Sub "${NamePrefix}promotion-pipeline"' in raw
         and '!Sub "${NamePrefix}promotion-pipeline-role"' in raw
         and '!Sub "${NamePrefix}promotion-approval"' in raw),
        ("no bare pde- Hub resource name (ZTIE's namespace)",
         not re.search(r'(StateMachineName|RoleName|TopicName|LogGroupName|ManagedPolicyName):\s*[!"\s]*[^\n]*"?pde-', raw)),
        ("exports use the pdlv- prefix",
         "pdlv-promotion-pipeline-arn" in raw
         and "pdlv-promotion-pipeline-role-arn" in raw),
        # --- Project=PDE tagging on every taggable resource ---
        ("resources tagged Project=PDE",
         "Value: PDE" in raw),
        ("every taggable resource is Project=PDE-tagged (topic + log group + role + state machine = 4; managed policies have no Tags)",
         raw.count("Key: Project, Value: PDE") == 4),
        # --- checkov CKV_AWS_26: SNS at-rest encryption on the approval topic ---
        #     (REAL SSE, not a skip — the topic carries the task token + decision).
        ("approval SNS topic has at-rest encryption (checkov CKV_AWS_26)",
         "KmsMasterKeyId:" in raw),
        # --- checkov CKV_AWS_158: Log Group KMS — satisfied by a justified skip ---
        ("the Log Group carries a justified CKV_AWS_158 KMS suppression (checkov)",
         full.count("checkov:skip=CKV_AWS_158:") == 1),
        # --- Least privilege: NO wildcard admin (Universal Criterion 3) ---
        ("no AdministratorAccess",
         "AdministratorAccess" not in raw),
        ("no PowerUserAccess / attached AWS-managed admin policy ARN",
         "iam::aws:policy/AdministratorAccess" not in raw
         and "iam::aws:policy/PowerUserAccess" not in raw),
        ("no full wildcard action",
         not re.search(r"Action:\s*['\"]\*['\"]", raw)
         and '- "*"' not in raw and "- '*'" not in raw),
        ("no codebuild:* wildcard (start only the specific deploy project)",
         "codebuild:*" not in raw),
        ("no sns:* wildcard (publish only to the approval topic)",
         "sns:*" not in raw),
        # --- The orchestrator's ONLY codebuild power is scoped to the deploy project ARN ---
        ("codebuild actions are start/stop/describe only (no broad codebuild grant)",
         "codebuild:StartBuild" in raw
         and "codebuild:StopBuild" in raw
         and "codebuild:BatchGetBuilds" in raw),
        ("codebuild power is scoped to the specific project ARN (project/${DeployProjectName})",
         "project/${DeployProjectName}" in raw),
        ("orchestrator grants NO cross-account deploy power — member role ARNs are only promotion inputs, never an IAM grant Resource (that power stays in the 2.1 CodeBuild role)",
         not re.search(r"Resource:\s*\n\s*-\s*!Sub\s*\"arn:\$\{AWS::Partition\}:iam::.*role/\$\{MemberRoleName\}", raw)),
        ("sns:Publish is scoped to the approval topic (Ref ApprovalTopic), not *",
         "!Ref ApprovalTopic" in raw and "sns:Publish" in raw),
        # --- EventBridge managed-rule permissions for the codebuild:startBuild.sync
        #     integration (live-sealed FAIL class, Story 2.3 attempt 1, 2026-10-01):
        #     at CreateStateMachine time Step Functions must be able to MANAGE the
        #     StepFunctionsGetEventsFor* rule, or the deploy rolls back with
        #     "is not authorized to create managed-rule". The role needs the COMPLETE
        #     lifecycle action set, and the resource must cover the rule-name FAMILY
        #     (not one literal rule) — while staying least-privilege (NOT events:*,
        #     NOT Resource "*"). ---
        ("SFN role has the complete .sync managed-rule action set (Put/Describe/Delete rule + Put/Remove targets)",
         all(a in raw for a in (
             "events:PutRule", "events:PutTargets", "events:DescribeRule",
             "events:DeleteRule", "events:RemoveTargets"))),
        ("the .sync managed-rule actions are scoped to the StepFunctionsGetEventsFor* rule-name family (resolves the CreateStateMachine managed-rule denial)",
         "rule/StepFunctionsGetEventsFor*" in raw),
        ("still least-privilege: no events:* wildcard, no Resource \"*\" on the events policy",
         "events:*" not in raw),
        # --- CloudFormation ORDERING: the state machine must DependsOn its managed
        #     policies (live-sealed FAIL class, Story 2.3 attempt 5, 2026-10-01): without
        #     it, CreateStateMachine fires before SyncEventsPolicy is attached/propagated
        #     and Step Functions' events:PutRule is denied ("not authorized to create
        #     managed-rule", SDK Attempt Count 11). DependsOn forces the attachments to
        #     complete first — a pure ordering fix, no privilege change. ---
        ("the state machine DependsOn its managed policies (ordering: policies attached before CreateStateMachine)",
         bool(re.search(
             r"PromotionStateMachine:\s*\n\s*Type:\s*AWS::StepFunctions::StateMachine\s*\n"
             r"(?:.*\n)*?\s*DependsOn:\s*\n"
             r"(?:\s*-\s*\w+\s*\n)*?\s*-\s*SyncEventsPolicy\b",
             raw))),
        # --- Execution role is scoped + trusted only by Step Functions ---
        ("a Step Functions execution role exists",
         "StateMachineExecutionRole:" in raw and "Type: AWS::IAM::Role" in raw),
        ("execution role trusts only states.amazonaws.com",
         "Service: states.amazonaws.com" in raw),
        ("service-trust is confused-deputy scoped to this account (aws:SourceAccount)",
         '"aws:SourceAccount": !Ref "AWS::AccountId"' in raw),
        ("execution role has a bounded session duration",
         "MaxSessionDuration:" in raw),
        ("permissions are scoped managed policies attached by Ref",
         "!Ref StartDeployPolicy" in raw
         and "!Ref PublishApprovalPolicy" in raw
         and "!Ref StateMachineLogsPolicy" in raw),
        # --- Logging on the state machine ---
        ("state machine logs to its OWN pdlv- log group",
         "LoggingConfiguration:" in raw
         and "!GetAtt StateMachineLogGroup.Arn" in raw),
        ("log group has a bounded retention",
         "RetentionInDays:" in raw),
        # --- ExternalId is a NoEcho secret (not committed real) ---
        ("ExternalId parameter is NoEcho (confused-deputy secret, not committed real)",
         bool(re.search(r"ExternalId:\s*\n(?:.*\n)*?\s*NoEcho:\s*true", raw))),
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
        print(f"validate_state_machine: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_state_machine: PASS — all {len(checks)} state-machine invariants hold")
    return 0


def self_test() -> int:
    """Prove the guard GUARDS — in memory, no disk write.

    Takes the real template, applies sabotages that mirror the live-sealed FAIL class
    (and the core adversarial cases), and asserts the relevant invariant flips to
    FAIL. Disk-independent, per the Story 2.1 OD-007 lesson (a full CloudShell disk
    must never be able to invalidate the guard test).
    """
    good = TEMPLATE.read_text(encoding="utf-8")

    sabotages: list[tuple[str, str, str]] = [
        # (label, broken_text, the invariant-name substring that must now FAIL)
        ("pde- namespace regression (prefix param flipped)",
         good.replace('AllowedPattern: "^pdlv-$"', 'AllowedPattern: "^pde-$"', 1),
         "name prefix parameter is exactly pdlv-"),
        ("pde- namespace regression (exports flipped)",
         good.replace("pdlv-promotion-pipeline-arn", "pde-promotion-pipeline-arn"),
         "exports use the pdlv- prefix"),
        ("over-long Description (cfn-lint E1003)",
         re.sub(r"\nDescription: >-\n.*?\n\n([^ ])",
                "\nDescription: >-\n  " + ("x " * 700) + "\n\n\\1", good, flags=re.DOTALL),
         f"within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit"),
        ("dropped CKV_AWS_158 suppression",
         good.replace("checkov:skip=CKV_AWS_158:", "nope:", 1),
         "CKV_AWS_158 KMS suppression"),
        ("dropped SNS at-rest encryption (CKV_AWS_26)",
         good.replace("KmsMasterKeyId: alias/aws/sns", "", 1),
         "approval SNS topic has at-rest encryption"),
        ("wildcard action injected",
         good.replace("Action: sns:Publish", 'Action: "*"', 1),
         "no full wildcard action"),
        ("codebuild:* broadening injected",
         good.replace("codebuild:StartBuild", "codebuild:*", 1),
         "no codebuild:* wildcard"),
        ("approval pause faked with a Wait/timer",
         good.replace("arn:aws:states:::sns:publish.waitForTaskToken",
                      "arn:aws:states:::sns:publish", 1),
         "exactly two waitForTaskToken approval pauses"),
        ("promotion order broken (Dev skips the Sandbox approval)",
         good.replace('"Next": "AwaitSandboxApproval"', '"Next": "DeploySandbox"', 1),
         "promotion order is Dev"),
        # The live-sealed FAIL (Story 2.3 attempt 1): the .sync managed-rule scope
        # reverted to a SINGLE literal rule — must re-fail the rule-name-family check.
        ("SFN managed-rule scope reverted to a single literal rule (the attempt-1 FAIL)",
         good.replace("rule/StepFunctionsGetEventsFor*", "rule/SomeOtherRule", 1),
         "StepFunctionsGetEventsFor* rule-name family"),
        # Incomplete managed-rule lifecycle actions (DeleteRule dropped).
        ("SFN managed-rule action set incomplete (DeleteRule dropped)",
         good.replace("- events:DeleteRule\n", "", 1),
         "complete .sync managed-rule action set"),
        # Over-broad fix regression: events:* must still be rejected.
        ("events:* broadening injected",
         good.replace("events:PutTargets", "events:*", 1),
         "no events:* wildcard"),
        # The attempt-5 FAIL class: drop the state machine's DependsOn on its policies
        # (the CreateStateMachine-before-policy-attached ordering race) — must re-fail.
        ("state machine DependsOn on managed policies removed (the attempt-5 ordering race)",
         re.sub(r"\n    DependsOn:\n(?:      - \w+\n)+", "\n", good, count=1),
         "DependsOn its managed policies"),
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
        print("validate_state_machine --self-test: FAIL — a sabotage was NOT caught")
        return 1
    # And the pristine template must still PASS cleanly.
    clean_fail = sum(1 for _, ok in run_checks(good) if not ok)
    if clean_fail:
        print(f"validate_state_machine --self-test: FAIL — clean template has {clean_fail} failing invariant(s)")
        return 1
    print("validate_state_machine --self-test: PASS — guard flips to FAIL on every sabotage; clean template passes")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    return _report(run_checks(TEMPLATE.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
