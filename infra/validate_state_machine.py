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
    # The PRODUCTION pipeline is the FIRST state machine in the file, so its is the
    # first DefinitionString block — this keeps the existing DeployDev/sequence
    # invariants pointed at the real pipeline (not the gate probe added in Story 2.3).
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


def _definition_block(raw_text: str, sm_resource: str) -> str:
    """Return the raw text of the DefinitionString JSON for a named state-machine
    resource (``PromotionStateMachine`` / ``GateProbeStateMachine``), or "" if absent.

    Used to scope security invariants to the RIGHT state machine — e.g. "the probe
    references no codebuild" must read the probe's definition, not the pipeline's.
    """
    m = re.search(
        sm_resource + r":\s*\n.*?DefinitionString: \|\n(.*?)\n      Tags:",
        raw_text, re.DOTALL)
    return m.group(1) if m else ""


def _iam_description_values(raw_text: str) -> list[str]:
    """Return the text of every IAM-resource Description that AWS will validate.

    IAM Role / ManagedPolicy descriptions must match AWS's regex
    [\\u0009\\u000A\\u000D\\u0020-\\u007E\\u00A1-\\u00FF]* — a stray em-dash / smart
    quote (common on paste) makes CreateRole fail and rolls the whole stack back
    (Story 2.3 attempt 9). We approximate "an IAM resource's Description" as any
    ``Description:`` whose nearest preceding ``Type:`` is an IAM type. Returns the
    rendered description strings (folded ``>-`` blocks joined) for the ASCII check.
    """
    lines = raw_text.split("\n")
    # find line indexes of IAM resource Type declarations
    iam_type_lines = [
        i for i, ln in enumerate(lines)
        if re.search(r"Type:\s*AWS::IAM::(Role|ManagedPolicy)\b", ln)
    ]
    results: list[str] = []
    for i, ln in enumerate(lines):
        m = re.match(r"(\s*)Description:\s*(.*)$", ln)
        if not m:
            continue
        # is the nearest preceding Type: an IAM type?
        preceding_type = max((t for t in iam_type_lines if t < i), default=None)
        # and is there no other Type: between it and here (i.e. same resource)?
        if preceding_type is None:
            continue
        between = [j for j, l2 in enumerate(lines)
                   if preceding_type < j < i and re.match(r"\s*Type:\s*\S", l2)]
        if between:
            continue
        indent, first = m.group(1), m.group(2).strip()
        if first in (">-", "|", ">", "|-"):
            # folded/literal block: gather deeper-indented following lines
            body = []
            for nxt in lines[i + 1:]:
                if nxt.strip() == "":
                    body.append("")
                    continue
                if len(nxt) - len(nxt.lstrip()) > len(indent):
                    body.append(nxt.strip())
                else:
                    break
            results.append(" ".join(body).strip())
        else:
            results.append(first.strip('"'))
    return results


_IAM_DESCRIPTION_RE = re.compile(r"[^\u0009\u000A\u000D\u0020-\u007E\u00A1-\u00FF]")


def _probe_definition(raw_text: str) -> str:
    return _definition_block(raw_text, "GateProbeStateMachine")


def _promotion_definition(raw_text: str) -> str:
    return _definition_block(raw_text, "PromotionStateMachine")


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
        """The deploy task overrides TARGET_ENV=<env> and TARGET_ROLE_ARN (the hop-2
        member-role target), per RD-006. Story 3.2: it must NOT carry a plaintext
        EXTERNAL_ID override — the ExternalId is resolved at the CodeBuild edge from
        the Hub SSM SecureString, so it never enters the state-machine execution
        history."""
        params = _state(name).get("Parameters", {})
        if params.get("ProjectName") != "${DeployProjectName}":
            return False
        overrides = params.get("EnvironmentVariablesOverride", [])
        names = {o.get("Name"): o.get("Value") for o in overrides if isinstance(o, dict)}
        return (
            names.get("TARGET_ENV") == env
            and "TARGET_ROLE_ARN" in names
            and "EXTERNAL_ID" not in names
        )

    return [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- cfn-lint E1003: Description within the 1024-byte CFN limit ---
        (f"template Description within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit (cfn-lint E1003)",
         0 < _description_bytes(full) <= CFN_DESCRIPTION_MAX_BYTES),
        # --- The state machine exists and is STANDARD (approval pauses can outlast EXPRESS) ---
        ("declares two state machines: the production pipeline + the Story 2.3 gate probe",
         raw.count("Type: AWS::StepFunctions::StateMachine") == 2
         and "PromotionStateMachine:" in raw and "GateProbeStateMachine:" in raw),
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
        ("DeployDev overrides TARGET_ENV=dev + TARGET_ROLE_ARN, NO plaintext ExternalId",
         _deploy_env("DeployDev", "dev")),
        ("DeploySandbox overrides TARGET_ENV=sandbox + TARGET_ROLE_ARN, NO plaintext ExternalId",
         _deploy_env("DeploySandbox", "sandbox")),
        ("DeployProd overrides TARGET_ENV=prod + TARGET_ROLE_ARN, NO plaintext ExternalId",
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
        ("the production pipeline has exactly two waitForTaskToken approval pauses",
         _promotion_definition(full).count("sns:publish.waitForTaskToken") == 2),
        ("the production approval pauses carry the Step Functions task token ($$.Task.Token)",
         _promotion_definition(full).count('"taskToken.$": "$$.Task.Token"') == 2),
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
        ("every taggable resource is Project=PDE-tagged (pipeline: topic+log group+role+SM = 4; probe: log group+role+SM = 3; total 7; managed policies have no Tags)",
         raw.count("Key: Project, Value: PDE") == 7),
        # --- checkov CKV_AWS_26: SNS at-rest encryption on the approval topic ---
        #     (REAL SSE, not a skip — the topic carries the task token + decision).
        ("approval SNS topic has at-rest encryption (checkov CKV_AWS_26)",
         "KmsMasterKeyId:" in raw),
        # --- checkov CKV_AWS_158: Log Group KMS — satisfied by a justified skip ---
        ("both Log Groups (state machine + gate probe) carry a justified CKV_AWS_158 KMS suppression (checkov)",
         full.count("checkov:skip=CKV_AWS_158:") == 2),
        # --- checkov CKV_AWS_111: the AWS-mandated events-rule-management Resource "*"
        #     on SyncEventsPolicy carries a justified skip (the "*" is required by the
        #     codebuild:startBuild.sync managed-rule authz check; still bounded to the
        #     three named events: actions + no events:* — see the named-actions invariant
        #     below). Exactly ONE such suppression, on SyncEventsPolicy.
        ("SyncEventsPolicy carries a justified CKV_AWS_111 suppression for the AWS-mandated events rule-management Resource \"*\" (checkov)",
         full.count("checkov:skip=CKV_AWS_111:") == 1),
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
        #     at CreateStateMachine time Step Functions calls events:PutRule/PutTargets/
        #     DescribeRule to provision + validate the managed rule for the
        #     codebuild:startBuild.sync integration. CORRECTED THROUGH 3 LIVE ATTEMPTS
        #     (attempts 1, 5, 6): the authorization check does NOT accept a
        #     resource-SCOPED grant (a literal rule ARN OR the StepFunctionsGetEventsFor*
        #     family both got AccessDenied, SDK Attempt Count 11), and it is NOT an
        #     ordering race (an explicit DependsOn did not help). AWS's OWN published IAM
        #     template for this integration grants exactly these three actions on
        #     Resource: "*". So the correct, documented grant is the three managed-rule
        #     actions on "*", bounded to events: rule-management actions only. ---
        ("SFN role grants the three AWS-documented .sync managed-rule actions (PutRule/PutTargets/DescribeRule)",
         all(a in raw for a in ("events:PutRule", "events:PutTargets", "events:DescribeRule"))),
        ("the .sync managed-rule actions are on Resource \"*\" (AWS-documented; a scoped rule ARN gets AccessDenied at CreateStateMachine — attempts 1/5/6)",
         bool(re.search(
             # Within the CodeBuildSyncManagedRule statement ONLY (stop at the next
             # `- Sid:` so we never read a later statement's Resource), the Resource is "*".
             r"Sid:\s*CodeBuildSyncManagedRule\b"
             r"(?:(?!-\s*Sid:).)*?"
             r"Resource:\s*[\"']\*[\"']",
             raw, re.DOTALL))),
        ("still least-privilege on the events grant: no events:* wildcard (only the named rule-management actions)",
         "events:*" not in raw),
        # --- Step Functions CloudWatch Logs DELIVERY permissions (live-sealed FAIL
        #     class, Story 2.3 attempt 7, 2026-10-02): CreateStateMachine attaches a log
        #     DESTINATION, which needs the account-level log-delivery actions + especially
        #     logs:PutResourcePolicy on Resource "*". PutResourcePolicy scoped to a
        #     log-group ARN gets "not authorized to access the Log Destination" and rolls
        #     back. Only the log-WRITE actions (CreateLogStream/PutLogEvents) may be
        #     scoped to the own log-group ARN. ---
        ("logs:PutResourcePolicy is in a LogDeliverySetup \"*\" statement and NEVER in a scoped Own*LogGroupOnly statement (account-level; a scoped ARN gets 'not authorized to access the Log Destination' — attempt 7)",
         "logs:PutResourcePolicy" in raw
         # it must appear in every LogDeliverySetup "*" block that exists...
         and all(
             "logs:PutResourcePolicy" in blk
             for blk in re.findall(r"Sid:\s*LogDeliverySetup\b((?:(?!-\s*Sid:).)*?)Resource:\s*[\"']\*[\"']", raw, re.DOTALL)
         )
         # ...and NEVER inside a scoped Own*LogGroupOnly statement.
         and not re.search(
             r"Sid:\s*Own\w*LogGroupOnly\b(?:(?!-\s*Sid:).)*?logs:PutResourcePolicy",
             raw, re.DOTALL)),
        ("the account-level log-delivery actions are on Resource \"*\" (CreateLogDelivery present in the \"*\" statement)",
         bool(re.search(
             r"Sid:\s*LogDeliverySetup\b"
             r"(?:(?!-\s*Sid:).)*?logs:CreateLogDelivery"
             r"(?:(?!-\s*Sid:).)*?Resource:\s*[\"']\*[\"']",
             raw, re.DOTALL))),
        # --- PHASE 2 GATE PROBE (Story 2.3): a SEPARATE, structurally non-promoting
        #     state machine proves the approval pause is reachable WITHOUT a real deploy.
        #     Security guarantees enforced here so the probe can NEVER become a deploy/
        #     promotion path, and the PRODUCTION pipeline stays bypass-free. ---
        ("a separate gate-probe state machine exists (Story 2.3 — proves the pause without a deploy)",
         "GateProbeStateMachine:" in raw and '!Sub "${NamePrefix}gate-probe"' in raw),
        ("the gate probe references NO codebuild / startBuild anywhere (cannot deploy or promote)",
         _probe_definition(full) != ""
         and "codebuild" not in _probe_definition(full)
         and "startBuild" not in _probe_definition(full)),
        ("the gate probe terminates in a Fail state, never Succeed (an approved probe can't read as a promotion)",
         '"GateProbeReachedPause"' in _probe_definition(full)
         and '"Type": "Fail"' in _probe_definition(full)
         and '"Type": "Succeed"' not in _probe_definition(full)),
        ("the gate-probe role has ONLY publish + logs (no codebuild, no events managed-rule, no sts:AssumeRole into a member)",
         "!Ref GateProbePublishPolicy" in raw and "!Ref GateProbeLogsPolicy" in raw
         and not re.search(r"GateProbe\w*Policy:(?:(?!Type: AWS::IAM).)*?(codebuild:|events:PutRule|events:PutTargets|sts:AssumeRole)", raw, re.DOTALL)),
        # --- PRODUCTION pipeline stays BYPASS-FREE: no input-driven skip. The real
        #     promotion path must keep all three deploys + both approvals in strict
        #     order (already checked above) and introduce NO Choice/gateMode branch. ---
        ("the PRODUCTION promotion pipeline has NO gateMode / input-driven bypass branch",
         "gateMode" not in _promotion_definition(full)
         and '"Type": "Choice"' not in _promotion_definition(full)),
        # --- IAM Description ASCII constraint (live-sealed FAIL class, Story 2.3
        #     attempt 9): an IAM Role/ManagedPolicy Description with a non-ASCII char
        #     (em-dash, smart quote) fails AWS's regex at CreateRole and rolls the stack
        #     back. Every IAM resource Description must be plain ASCII in AWS's allowed
        #     range. ---
        ("every IAM Role/ManagedPolicy Description is within AWS's allowed character set (no em-dash/smart-quote — attempt 9)",
         all(_IAM_DESCRIPTION_RE.search(d) is None for d in _iam_description_values(full))),
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
        # --- Story 3.2: the ExternalId is a control-plane secret that must NOT
        #     traverse the orchestration layer. It is resolved at the CodeBuild edge
        #     from a Hub SSM SecureString, so the state machine must carry NEITHER an
        #     ExternalId parameter NOR an EXTERNAL_ID override anywhere in the ASL. ---
        ("no ExternalId parameter on the state machine (secret resolved at the edge)",
         "ExternalId:" not in raw),
        ("no EXTERNAL_ID anywhere in the ASL (never in the execution history)",
         "EXTERNAL_ID" not in raw and "ExternalId" not in raw),
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
        ("dropped CKV_AWS_111 suppression on SyncEventsPolicy",
         good.replace("checkov:skip=CKV_AWS_111:", "nope:", 1),
         "CKV_AWS_111 suppression"),
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
        # The live-sealed FAIL class (attempts 1/5/6): scoping the .sync managed-rule
        # grant to a rule ARN instead of "*" gets AccessDenied at CreateStateMachine.
        # Re-introduce a scoped resource on that statement — must re-fail the "on
        # Resource *" invariant.
        ("SFN managed-rule grant re-scoped to a rule ARN (the attempts-1/5/6 FAIL)",
         # Flip ONLY the managed-rule statement's Resource "*" to a scoped ARN. The
         # events statement is the only `Resource: "*"` on its own line (the logs policy
         # uses `Resource: "*"` too but on a differently-indented line); target the
         # events one by its unique 12-space indent + exact value.
         good.replace(
             '            Resource: "*"',
             '            Resource:\n              - !Sub "arn:${AWS::Partition}:events:${AWS::Region}:${AWS::AccountId}:rule/StepFunctionsGetEventsForCodeBuildStartBuildRule"',
             1),
         "sync managed-rule actions are on Resource"),
        # Over-broad fix regression: events:* must still be rejected.
        ("events:* broadening injected",
         good.replace("events:PutTargets", "events:*", 1),
         "no events:* wildcard"),
        # The attempt-5 FAIL class: drop the state machine's DependsOn on its policies
        # (the CreateStateMachine-before-policy-attached ordering race) — must re-fail.
        ("state machine DependsOn on managed policies removed (the attempt-5 ordering race)",
         re.sub(r"\n    DependsOn:\n(?:      - \w+\n)+", "\n", good, count=1),
         "DependsOn its managed policies"),
        # The attempt-7 FAIL class: remove logs:PutResourcePolicy from the "*" delivery
        # statement (it would have to be scoped, which gets the Log Destination denial).
        ("logs:PutResourcePolicy removed from the \"*\" delivery statement (the attempt-7 FAIL)",
         good.replace("              - logs:PutResourcePolicy\n", ""),  # remove from ALL delivery blocks
         "logs:PutResourcePolicy is in a LogDeliverySetup"),
        # Gate-probe security: the probe must never gain a deploy/promote path.
        ("gate probe given a codebuild/startBuild path (probe must be non-promoting)",
         good.replace(
             '"GateProbeReachedPause"',
             '"DeployViaProbe"', 1).replace(
             '"GateProbeReachedPause": {\n              "Type": "Fail",',
             '"DeployViaProbe": {\n              "Type": "Task",\n              "Resource": "arn:aws:states:::codebuild:startBuild.sync",',
             1),
         "references NO codebuild / startBuild"),
        ("gate probe terminal flipped Fail -> Succeed (an approved probe would read as a promotion)",
         good.replace(
             '"GateProbeReachedPause": {\n              "Type": "Fail",',
             '"GateProbeReachedPause": {\n              "Type": "Succeed",', 1),
         "terminates in a Fail state, never Succeed"),
        # Production bypass: injecting a gateMode skip into the real pipeline must fail.
        ("gateMode bypass injected into the PRODUCTION pipeline",
         good.replace('"StartAt": "DeployDev"', '"StartAt": "DeployDev", "gateMode": true', 1),
         "PRODUCTION promotion pipeline has NO gateMode"),
        # The attempt-9 FAIL class: a non-ASCII em-dash in an IAM role Description.
        ("non-ASCII em-dash injected into an IAM role Description (the attempt-9 FAIL)",
         good.replace("writes its own logs - nothing else",
                      "writes its own logs \u2014 nothing else", 1),
         "within AWS's allowed character set"),
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
