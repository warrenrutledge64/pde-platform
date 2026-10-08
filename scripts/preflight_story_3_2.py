#!/usr/bin/env python3
"""Story 3.2 LIVE preflight — refuse to validate against un-redeployed infra.

WHY THIS EXISTS (VD-9 attempts 1 + 2, 2026-10-04)
-------------------------------------------------
Both failed live runs validated STALE infrastructure that was never redeployed
from `feature/story-3.2`: a legacy `pde-hub-orchestrator` dated 2026-06-10 (trusts
Step Functions, holds S3/events power, targets `pde-cross-account-deployer`), the
pre-3.2 state machine (plaintext `EXTERNAL_ID` override), and the `Story=1.1` Dev
member role with a `<paste-the-new-value>` ExternalId. In attempt 2 the operator was
not even inside the clone (`git rev-parse HEAD` -> "fatal: not a git repository"), so
the `cloudformation deploy` of the branch templates never ran. The branch deliverable
was never under test — an execution failure, not a deliverable defect.

Prose gates ("deploy first, please") kept being skipped. Per the standing discipline
(a repeatedly-skipped step gets a MECHANICAL check, not more prose), this script reads
the ACTUAL LIVE resources and HARD-FAILS unless they match the Story-3.2 baseline — so
a validation run against un-redeployed infra is impossible to start. The independent
validator / operator runs this BEFORE triggering the pipeline; a non-zero exit means
"the branch is not deployed yet — deploy STEP 2a-2d, then re-run this."

WHAT IT PROVES (reads live AWS; needs Hub + Dev read creds)
-----------------------------------------------------------
Hub (641628980935):
  * `pdlv-hub-orchestrator` (the RD-009 rename of the legacy pde-hub-orchestrator)
    trust names ONLY `pdlv-codebuild-service-role` (NOT any `*.amazonaws.com`
    service, NOT `:root`);
  * it carries a PermissionsBoundary;
  * it has NO local Hub power (no s3:/events:/logs: inline or attached statements) and
    its only action is `sts:AssumeRole` to the three `pde-member-execution-<env>` ARNs
    (NOT `pde-cross-account-deployer`);
  * the `pdlv-promotion-pipeline` state-machine definition contains NO `EXTERNAL_ID`.
Dev (946509368326):
  * `pde-member-execution-dev` carries the `Story=3.2` tag (NOT `1.1`);
  * its execution policy scopes CloudFormation to `stack/pdlv-*` (NOT `pde-*`) and
    grants the concrete DynamoDB table-lifecycle actions on `table/pdlv-*`;
  * its trust `sts:ExternalId` is a real value (NOT a `<...>` placeholder).

Usage (run in Hub CloudShell with Dev read access, or pass a Dev profile):
    python3 scripts/preflight_story_3_2.py --hub-profile <hub> --dev-profile <dev>
    # or rely on the default credential chain for each if already scoped:
    python3 scripts/preflight_story_3_2.py
    python3 scripts/preflight_story_3_2.py --self-test   # offline logic proof (no AWS)

Exit: 0 = live infra matches the Story-3.2 baseline (safe to validate);
      1 = a mismatch (STALE/undeployed infra — deploy the branch, do NOT validate);
      2 = could not read a required live resource (environment/credentials issue).
"""

from __future__ import annotations

import argparse
import json
import sys

HUB_ACCOUNT = "641628980935"
DEV_ACCOUNT = "946509368326"
# The Story-3.2 Hub orchestrator is pdlv--named (RD-009; renamed from the legacy
# pde-hub-orchestrator to be collision-proof vs. the pre-existing June-2026 Hub role).
ORCHESTRATOR_ROLE = "pdlv-hub-orchestrator"
MEMBER_ROLE_DEV = "pde-member-execution-dev"
CODEBUILD_SERVICE_ROLE = "pdlv-codebuild-service-role"
STATE_MACHINE_NAME = "pdlv-promotion-pipeline"


# --------------------------------------------------------------------------- #
# Pure evaluation logic (unit-testable offline; --self-test drives this).      #
# --------------------------------------------------------------------------- #
def evaluate(orchestrator_role: dict, orchestrator_statements: list[dict],
             member_role: dict, member_statements: list[dict],
             state_machine_definition: str) -> list[tuple[str, bool, str]]:
    """Return [(check, ok, detail)] for the FULL baseline (Hub + Dev), as plain data.

    Each argument is already-parsed JSON (so the collector and the self-test feed
    the SAME logic). `*_statements` are the flattened IAM policy statements
    (inline + attached managed) for that role. This is the composition of the two
    per-account check sets (evaluate_hub + evaluate_dev) and is unchanged in output,
    so the offline self-test and the default (both-accounts) run are identical.
    """
    return (
        evaluate_hub(orchestrator_role, orchestrator_statements, state_machine_definition)
        + evaluate_dev(member_role, member_statements)
    )


def evaluate_hub(orchestrator_role: dict, orchestrator_statements: list[dict],
                 state_machine_definition: str) -> list[tuple[str, bool, str]]:
    """Hub-account (641628980935) baseline checks: orchestrator role + state machine.

    Split out so an operator who works in per-account shells (no cross-account
    profile) can prove the Hub side from the Hub shell alone (--scope hub). The
    returned checks are a strict subset of evaluate()'s, in the same order.
    """
    checks: list[tuple[str, bool, str]] = []

    # --- Orchestrator trust: ONLY the CodeBuild service role --------------------
    trust = orchestrator_role.get("AssumeRolePolicyDocument", {})
    principals = _collect_principals(trust)
    trusts_codebuild = any(
        p.endswith(f":role/{CODEBUILD_SERVICE_ROLE}") for p in principals
    )
    trusts_service_or_root = any(
        (".amazonaws.com" in p) or p.endswith(":root") for p in principals
    )
    checks.append((
        "orchestrator trust names ONLY pdlv-codebuild-service-role",
        trusts_codebuild and not trusts_service_or_root,
        f"principals={sorted(principals)}",
    ))

    # --- Orchestrator carries a PermissionsBoundary -----------------------------
    checks.append((
        "orchestrator has a PermissionsBoundary",
        bool(orchestrator_role.get("PermissionsBoundary")),
        f"boundary={orchestrator_role.get('PermissionsBoundary') or 'NONE'}",
    ))

    # --- Orchestrator is pure pass-through: only sts:AssumeRole -----------------
    orch_actions = _collect_actions(orchestrator_statements)
    non_assume = sorted(a for a in orch_actions if a != "sts:AssumeRole")
    checks.append((
        "orchestrator holds ONLY sts:AssumeRole (no local Hub power)",
        orch_actions == {"sts:AssumeRole"},
        f"unexpected_actions={non_assume}",
    ))

    # --- Orchestrator targets the member roles, NOT pde-cross-account-deployer --
    orch_resources = _collect_resources(orchestrator_statements)
    targets_members = all(
        any(r.endswith(f":role/{MEMBER_ROLE_DEV.rsplit('-', 1)[0]}-{env}") for r in orch_resources)
        for env in ("dev", "sandbox", "prod")
    )
    targets_legacy = any("pde-cross-account-deployer" in r for r in orch_resources)
    checks.append((
        "orchestrator assume targets pde-member-execution-<env> (not pde-cross-account-deployer)",
        targets_members and not targets_legacy,
        f"resources={sorted(orch_resources)}",
    ))

    # --- State machine does NOT carry EXTERNAL_ID (edge-resolved) ---------------
    checks.append((
        "state-machine definition has NO EXTERNAL_ID (resolved at the edge)",
        "EXTERNAL_ID" not in state_machine_definition
        and "ExternalId" not in state_machine_definition,
        "EXTERNAL_ID present in ASL" if "EXTERNAL_ID" in state_machine_definition else "absent",
    ))

    return checks


def evaluate_dev(member_role: dict, member_statements: list[dict]) -> list[tuple[str, bool, str]]:
    """Dev-account (946509368326) baseline checks: the member execution role.

    Split out so an operator who works in per-account shells can prove the Dev side
    from the Dev shell alone (--scope dev). The returned checks are a strict subset
    of evaluate()'s, in the same order.
    """
    checks: list[tuple[str, bool, str]] = []

    # --- Dev member role carries Story=3.2 (not 1.1) ----------------------------
    tags = {t.get("Key"): t.get("Value") for t in member_role.get("Tags", [])}
    checks.append((
        "Dev member role tagged Story=3.2 (branch deployed, not the Story=1.1 role)",
        tags.get("Story") == "3.2",
        f"Story tag={tags.get('Story')!r}",
    ))

    # --- Dev member policy: pdlv- scoped CFN + concrete DynamoDB ----------------
    member_text = json.dumps(member_statements)
    cfn_pdlv = "stack/pdlv-" in member_text
    cfn_pde = "stack/pde-" in member_text
    has_dynamo = "dynamodb:CreateTable" in member_text and "table/pdlv-" in member_text
    checks.append((
        "Dev member CFN scoped to stack/pdlv-* (not pde-*)",
        cfn_pdlv and not cfn_pde,
        f"pdlv={cfn_pdlv} pde={cfn_pde}",
    ))
    checks.append((
        "Dev member grants concrete DynamoDB table-lifecycle on table/pdlv-*",
        has_dynamo,
        f"dynamodb+pdlv table grant={has_dynamo}",
    ))

    # --- Dev member trust ExternalId is a real value, not a placeholder ---------
    member_trust = json.dumps(member_role.get("AssumeRolePolicyDocument", {}))
    placeholder = "<" in member_trust and ">" in member_trust
    checks.append((
        "Dev member trust ExternalId is a real value (not a <placeholder>)",
        not placeholder,
        "placeholder present" if placeholder else "real value",
    ))

    return checks


def _collect_principals(trust: dict) -> set[str]:
    out: set[str] = set()
    for stmt in trust.get("Statement", []):
        pr = stmt.get("Principal", {})
        if isinstance(pr, dict):
            for v in pr.values():
                out.update([v] if isinstance(v, str) else v)
        elif isinstance(pr, str):
            out.add(pr)
    return out


def _collect_actions(statements: list[dict]) -> set[str]:
    out: set[str] = set()
    for stmt in statements:
        if stmt.get("Effect") != "Allow":
            continue
        a = stmt.get("Action", [])
        out.update([a] if isinstance(a, str) else a)
    return out


def _collect_resources(statements: list[dict]) -> set[str]:
    out: set[str] = set()
    for stmt in statements:
        if stmt.get("Effect") != "Allow" or "sts:AssumeRole" not in (
            [stmt.get("Action")] if isinstance(stmt.get("Action"), str) else stmt.get("Action", [])
        ):
            continue
        r = stmt.get("Resource", [])
        out.update([r] if isinstance(r, str) else r)
    return out


# --------------------------------------------------------------------------- #
# Live collectors (boto3; only imported when actually hitting AWS).            #
# --------------------------------------------------------------------------- #
def _session(profile: str | None):
    import boto3  # local import so --self-test / --help need no boto3
    return boto3.Session(profile_name=profile) if profile else boto3.Session()


def _flatten_role_policies(iam, role_name: str) -> list[dict]:
    """Inline + attached-managed statements for a role, flattened."""
    statements: list[dict] = []
    for name in iam.list_role_policies(RoleName=role_name).get("PolicyNames", []):
        doc = iam.get_role_policy(RoleName=role_name, PolicyName=name)["PolicyDocument"]
        statements.extend(doc.get("Statement", []))
    for att in iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", []):
        pol = iam.get_policy(PolicyArn=att["PolicyArn"])["Policy"]
        ver = iam.get_policy_version(PolicyArn=att["PolicyArn"],
                                     VersionId=pol["DefaultVersionId"])
        statements.extend(ver["PolicyVersion"]["Document"].get("Statement", []))
    return statements


def _collect_hub(hub_profile: str | None) -> list[tuple[str, bool, str]]:
    """Read the Hub account live and return the Hub baseline checks."""
    hub = _session(hub_profile)
    hub_iam, hub_sfn = hub.client("iam"), hub.client("stepfunctions")
    hub_acct = hub.client("sts").get_caller_identity()["Account"]
    if hub_acct != HUB_ACCOUNT:
        raise _WrongAccount(f"hub creds are account {hub_acct}, expected {HUB_ACCOUNT}")
    orch = hub_iam.get_role(RoleName=ORCHESTRATOR_ROLE)["Role"]
    orch_statements = _flatten_role_policies(hub_iam, ORCHESTRATOR_ROLE)
    sm_arn = f"arn:aws:states:us-east-1:{HUB_ACCOUNT}:stateMachine:{STATE_MACHINE_NAME}"
    sm_def = hub_sfn.describe_state_machine(stateMachineArn=sm_arn)["definition"]
    return evaluate_hub(orch, orch_statements, sm_def)


def _collect_dev(dev_profile: str | None) -> list[tuple[str, bool, str]]:
    """Read the Dev account live and return the Dev baseline checks."""
    dev = _session(dev_profile)
    dev_iam = dev.client("iam")
    dev_acct = dev.client("sts").get_caller_identity()["Account"]
    if dev_acct != DEV_ACCOUNT:
        raise _WrongAccount(f"dev creds are account {dev_acct}, expected {DEV_ACCOUNT}")
    member = dev_iam.get_role(RoleName=MEMBER_ROLE_DEV)["Role"]
    member_statements = _flatten_role_policies(dev_iam, MEMBER_ROLE_DEV)
    return evaluate_dev(member, member_statements)


class _WrongAccount(Exception):
    """Raised when a live read lands in the wrong account (an ENV failure, exit 2)."""


def collect_and_check(hub_profile: str | None, dev_profile: str | None,
                      scope: str = "both") -> int:
    """Read the live account(s) for `scope` and report.

    scope="both" (default) reads Hub + Dev in one process — unchanged behaviour for
    profile-based operators and CI. scope="hub"/"dev" reads only that account, so an
    operator working in per-account CloudShell sessions (no cross-account profile) can
    prove each side from its own shell. A per-account run prints a SCOPED PASS/FAIL;
    the two scoped PASSes together are the full baseline the validator reads.
    """
    try:
        checks: list[tuple[str, bool, str]] = []
        if scope in ("both", "hub"):
            checks += _collect_hub(hub_profile)
        if scope in ("both", "dev"):
            checks += _collect_dev(dev_profile)
    except _WrongAccount as exc:
        print(f"preflight: [ENV] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any read failure is an ENV/credentials issue
        print(f"preflight: [ENV] could not read a required live resource — {exc}", file=sys.stderr)
        print("preflight: this is an environment/credentials issue (exit 2), NOT a baseline mismatch.", file=sys.stderr)
        return 2

    return _report(checks, scope)


def _report(checks: list[tuple[str, bool, str]], scope: str = "both") -> int:
    failed = 0
    for name, ok, detail in checks:
        mark = "ok  " if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{mark}] {name}" + (f"   ({detail})" if not ok else ""))
    print()
    # The scoped label makes a per-account PASS self-describing in the evidence the
    # validator reads (e.g. "preflight_story_3_2 [hub]: PASS").
    label = "preflight_story_3_2" if scope == "both" else f"preflight_story_3_2 [{scope}]"
    span = {"both": "Hub + Dev", "hub": "Hub", "dev": "Dev"}[scope]
    if failed:
        print(f"{label}: FAIL — {failed} live resource(s) do NOT match the "
              f"Story-3.2 baseline ({span}). The branch is NOT deployed; deploy STEP 2a-2d "
              f"from feature/story-3.2, then re-run this. DO NOT validate against this infra.")
        return 1
    print(f"{label}: PASS — live {span} infra matches the Story-3.2 "
          "baseline; safe to trigger the pipeline + validate.")
    return 0


# --------------------------------------------------------------------------- #
# Offline self-test: prove the logic flags the exact attempt-1/2 stale infra.  #
# --------------------------------------------------------------------------- #
def self_test() -> int:
    good_orch_role = {
        "AssumeRolePolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": "sts:AssumeRole",
             "Principal": {"AWS": f"arn:aws:iam::{HUB_ACCOUNT}:role/{CODEBUILD_SERVICE_ROLE}"}}]},
        "PermissionsBoundary": {"PermissionsBoundaryArn": "arn:aws:iam::...:policy/pdlv-hub-orchestrator-boundary"},
    }
    good_orch_stmts = [{"Effect": "Allow", "Action": "sts:AssumeRole", "Resource": [
        f"arn:aws:iam::{DEV_ACCOUNT}:role/pde-member-execution-dev",
        "arn:aws:iam::586917955591:role/pde-member-execution-sandbox",
        "arn:aws:iam::466494951534:role/pde-member-execution-prod",
    ]}]
    good_member_role = {
        "Tags": [{"Key": "Story", "Value": "3.2"}],
        "AssumeRolePolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": "sts:AssumeRole",
             "Condition": {"StringEquals": {"sts:ExternalId": "a-real-secret-value"}}}]},
    }
    good_member_stmts = [
        {"Effect": "Allow", "Action": ["cloudformation:CreateStack"],
         "Resource": f"arn:aws:cloudformation:*:{DEV_ACCOUNT}:stack/pdlv-*/*"},
        {"Effect": "Allow", "Action": ["dynamodb:CreateTable", "dynamodb:DeleteTable"],
         "Resource": f"arn:aws:dynamodb:*:{DEV_ACCOUNT}:table/pdlv-*"},
    ]
    good_sm = '{"States":{"DeployDev":{"Parameters":{"EnvironmentVariablesOverride":[{"Name":"TARGET_ENV"}]}}}}'

    # Clean baseline must PASS.
    clean = evaluate(good_orch_role, good_orch_stmts, good_member_role, good_member_stmts, good_sm)
    if any(not ok for _, ok, _ in clean):
        print("preflight --self-test: FAIL — clean baseline should pass:")
        _report(clean)
        return 1

    # Scope split integrity: evaluate() MUST equal evaluate_hub() + evaluate_dev()
    # in content and order, and each scoped set must be a non-empty strict subset.
    # This guards the per-account (--scope hub|dev) runs: if a future edit moves a
    # check across the Hub/Dev boundary, the scoped PASSes would silently diverge
    # from the full baseline — this catches that offline.
    hub_only = evaluate_hub(good_orch_role, good_orch_stmts, good_sm)
    dev_only = evaluate_dev(good_member_role, good_member_stmts)
    if hub_only + dev_only != clean:
        print("preflight --self-test: FAIL — evaluate_hub()+evaluate_dev() != evaluate() "
              "(scope split drifted from the full baseline).")
        return 1
    if not hub_only or not dev_only:
        print("preflight --self-test: FAIL — a scoped check set is empty (hub or dev).")
        return 1
    hub_names = {n for n, _, _ in hub_only}
    dev_names = {n for n, _, _ in dev_only}
    if hub_names & dev_names:
        print("preflight --self-test: FAIL — a check appears in BOTH hub and dev scopes.")
        return 1

    # The EXACT attempt-1/2 stale live infra must be caught on every axis.
    stale_orch_role = {
        "AssumeRolePolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": "sts:AssumeRole",
             "Principal": {"Service": ["states.amazonaws.com"]}}]},
        # no PermissionsBoundary
    }
    stale_orch_stmts = [
        {"Effect": "Allow", "Action": "sts:AssumeRole",
         "Resource": "arn:aws:iam::*:role/pde-cross-account-deployer"},
        {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"],
         "Resource": "arn:aws:s3:::pde-blueprint-store-641628980935/*"},
        {"Effect": "Allow", "Action": ["events:PutRule"], "Resource": "*"},
    ]
    stale_member_role = {
        "Tags": [{"Key": "Story", "Value": "1.1"}],
        "AssumeRolePolicyDocument": {"Statement": [
            {"Effect": "Allow", "Action": "sts:AssumeRole",
             "Condition": {"StringEquals": {"sts:ExternalId": "<paste-the-new-value>"}}}]},
    }
    stale_member_stmts = [
        {"Effect": "Allow", "Action": ["cloudformation:CreateStack"],
         "Resource": f"arn:aws:cloudformation:*:{DEV_ACCOUNT}:stack/pde-*/*"},
    ]
    stale_sm = ('{"States":{"DeployDev":{"Parameters":{"EnvironmentVariablesOverride":'
                '[{"Name":"EXTERNAL_ID","Type":"PLAINTEXT","Value":"set-this-at-deploy-time"}]}}}}')

    stale = evaluate(stale_orch_role, stale_orch_stmts, stale_member_role, stale_member_stmts, stale_sm)
    # EVERY check must flip to FAIL on the stale infra (that is the whole point).
    passed_on_stale = [name for name, ok, _ in stale if ok]
    if passed_on_stale:
        print("preflight --self-test: FAIL — these checks did NOT catch the stale infra:")
        for n in passed_on_stale:
            print(f"    - {n}")
        return 1

    print("preflight_story_3_2 --self-test: PASS — clean baseline passes; the exact "
          "attempt-1/2 stale infra (June-10 orchestrator trusting Step Functions, S3/events "
          "power, pde-cross-account-deployer target, no boundary, Story=1.1 member role, "
          "pde-* CFN scope, no DynamoDB, placeholder ExternalId, EXTERNAL_ID in the ASL) is "
          "caught on every axis.")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Story 3.2 live preflight — refuse to validate un-redeployed infra.")
    p.add_argument("--hub-profile", default=None, help="AWS profile with Hub 641628980935 read access.")
    p.add_argument("--dev-profile", default=None, help="AWS profile with Dev 946509368326 read access.")
    p.add_argument("--scope", choices=["both", "hub", "dev"], default="both",
                   help="Which account(s) to read. 'both' (default) reads Hub+Dev in one "
                        "process (profile-based / CI). 'hub' or 'dev' reads only that account "
                        "— for operators in per-account CloudShell sessions with no "
                        "cross-account profile: run --scope hub in the Hub shell and "
                        "--scope dev in the Dev shell; the two scoped PASSes together are the "
                        "full baseline.")
    p.add_argument("--self-test", action="store_true", help="Offline logic proof (no AWS).")
    args = p.parse_args(argv)
    if args.self_test:
        return self_test()
    return collect_and_check(args.hub_profile, args.dev_profile, args.scope)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
