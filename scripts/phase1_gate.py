#!/usr/bin/env python3
"""PDE Phase-1 gate — Hub orchestrate-and-pull reachability check.

Proves the RD-006 **orchestrate-and-pull** trust fabric end to end: run from an
AWS CloudShell session in the Pipeline-Hub account, *as the Hub orchestrator role*
(``pde-hub-orchestrator``), this script performs an STS ``AssumeRole`` into the
**member execution role** (``pde-member-execution-<env>``) in each member account
(Dev → Sandbox → Prod) **sequentially**, presenting the shared ``ExternalId``, and
prints the account id STS returns for each assumed session. A clean run returns
all three member account ids — proving the Hub can direct each member and that the
trust direction (Hub assumes member, member executes locally) is correct.

Why this is the Phase-1 gate artifact
--------------------------------------
This is the exact script the Phase-1 end-of-phase gate runs. Per **Option B**
(stakeholder-chosen 2026-09-30), the Hub orchestrator role ``pde-hub-orchestrator``
is created in **Phase 2**, so the *live cross-account run* of this script is the
deferred **VD-3b** (executed in Phase 2 once that role exists). Story 1.2 authors +
commits this script (targeting the real orchestrator) and proves Hub-CloudShell
reachability + tooling + token-auth repo access live; it does **not** stand up a
throwaway Hub principal just to run this early.

Design discipline (hard-won Story 1.1 lessons)
----------------------------------------------
- **ExternalId is a secret** — it is NEVER hardcoded, printed, or logged. Supply it
  via the ``--external-id`` flag OR the ``PDE_EXTERNAL_ID`` environment variable. It
  must match the ``sts:ExternalId`` condition baked into the member-role trust
  policy (``infra/member-execution-role.yaml``).
- **Derive-the-env-FROM-the-account** — the member mapping is a fixed account→env
  table, never a hand-edited per-account literal (the #1 Story 1.1 failure mode was
  copy-pasting a wrong ``EnvironmentName``). The caller supplies no per-account
  value; the script derives the role name from the mapped account id.
- **Least privilege** — this uses only ``sts:AssumeRole`` through the Story 1.1
  trust fabric and ``sts:GetCallerIdentity``; it adds no new broad permissions and
  mutates nothing.
- **Trust get-caller-identity output, not a label** — the script confirms it is
  actually running in the Hub account before attempting any assume, and refuses to
  proceed from the wrong account (fail-safe).

Usage
-----
    # ExternalId from the environment (preferred — never on the command line):
    export PDE_EXTERNAL_ID='<the-shared-secret>'
    python3 scripts/phase1_gate.py

    # or pass it explicitly (visible in shell history — prefer the env var):
    python3 scripts/phase1_gate.py --external-id '<the-shared-secret>'

    # override the home region / role names if ever needed:
    python3 scripts/phase1_gate.py --region us-east-1

Exit codes
----------
    0  all member account ids returned (gate PASS)
    1  one or more assumes failed, or a precondition was not met (gate FAIL)
    2  usage / configuration error (no ExternalId supplied, etc.)
"""

from __future__ import annotations

import argparse
import os
import sys

# --- PDE account topology (authoritative; see governance/BOM.md & RESTORE.md) -----
# Pipeline-Hub is the orchestrator (where this runs). The three MEMBER accounts are
# the AssumeRole targets. The management/root account is zero-touch and never a
# target. These ids are the single source of truth for the account→env derivation
# (NEVER hand-edit a per-account literal at the call site — Story 1.1 lesson).
HUB_ACCOUNT_ID = "641628980935"          # Pipeline-Hub (orchestrator; run here)
MANAGEMENT_ACCOUNT_ID = "467866449172"   # Org management/root (zero-touch; never a target)

# Ordered Dev → Sandbox → Prod (the gate walks them in this promotion order).
MEMBERS: tuple[tuple[str, str], ...] = (
    ("dev", "946509368326"),       # Pipeline-Dev
    ("sandbox", "586917955591"),   # Pipeline-Sandbox
    ("prod", "466494951534"),      # Pipeline-Prod
)

ROLE_PREFIX = "pde-"                           # ZTIE-safe PDE naming prefix (RD).
HUB_ORCHESTRATOR_ROLE = "pde-hub-orchestrator"  # the Hub principal this runs as.
DEFAULT_REGION = "us-east-1"                    # PDE home region (pinned Story 1.1).
SESSION_PREFIX = "pde-phase1-gate"              # STS session-name prefix (audit).


def member_role_name(env: str) -> str:
    """Member execution role name for an env — the Story 1.1 naming contract.

    Mirrors ``!Sub "${RolePrefix}member-execution-${EnvironmentName}"`` in
    ``infra/member-execution-role.yaml`` so this gate always targets the role that
    template actually creates.
    """
    return f"{ROLE_PREFIX}member-execution-{env}"


def member_role_arn(account_id: str, env: str) -> str:
    return f"arn:aws:iam::{account_id}:role/{member_role_name(env)}"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PDE Phase-1 gate: Hub assumes each member execution role (Dev→Sandbox→Prod).",
    )
    p.add_argument(
        "--external-id",
        default=None,
        help="Shared ExternalId for the assume. PREFER the PDE_EXTERNAL_ID env var "
        "(keeps the secret out of shell history). Never commit the real value.",
    )
    p.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION", DEFAULT_REGION),
        help=f"AWS region for the STS client (default: {DEFAULT_REGION}).",
    )
    p.add_argument(
        "--allow-non-hub",
        action="store_true",
        help="Skip the 'must run in the Hub account' precondition (for testing only).",
    )
    return p.parse_args(argv)


def _resolve_external_id(cli_value: str | None) -> str | None:
    """ExternalId from the CLI flag or PDE_EXTERNAL_ID; never a default literal."""
    return cli_value if cli_value else os.environ.get("PDE_EXTERNAL_ID")


def run_gate(sts, external_id: str, *, require_hub: bool = True) -> int:
    """Walk Dev→Sandbox→Prod, assume each member role, print the returned ids.

    ``sts`` is a boto3 STS client (injected so this is unit-testable offline with a
    stub). Returns a process exit code: 0 = all three assumed, 1 = any failure.
    """
    from botocore.exceptions import ClientError  # local import: offline-import-safe

    # --- Precondition: confirm we are the Hub orchestrator, by OUTPUT not label ---
    try:
        ident = sts.get_caller_identity()
    except ClientError as exc:  # pragma: no cover - network/credential error path
        print(f"  [FAIL] could not call sts:GetCallerIdentity — {exc}", file=sys.stderr)
        return 1
    caller_account = ident.get("Account", "")
    caller_arn = ident.get("Arn", "")
    print(f"Caller account : {caller_account}")
    print(f"Caller ARN     : {caller_arn}")
    if require_hub and caller_account != HUB_ACCOUNT_ID:
        print(
            f"  [FAIL] not running in Pipeline-Hub ({HUB_ACCOUNT_ID}); "
            f"caller account is {caller_account!r}. Refusing to proceed "
            "(run this from the Hub, as pde-hub-orchestrator).",
            file=sys.stderr,
        )
        return 1
    print()

    failures = 0
    returned: list[tuple[str, str]] = []
    for env, account_id in MEMBERS:
        # Guard against ever targeting the Hub or the management account.
        if account_id in (HUB_ACCOUNT_ID, MANAGEMENT_ACCOUNT_ID):
            print(f"  [FAIL] {env}: refusing to target reserved account {account_id}", file=sys.stderr)
            failures += 1
            continue
        role_arn = member_role_arn(account_id, env)
        print(f"→ {env:<8} assume {role_arn}")
        try:
            resp = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"{SESSION_PREFIX}-{env}",
                ExternalId=external_id,
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "ClientError")
            print(f"  [FAIL] {env}: assume denied/failed ({code})", file=sys.stderr)
            failures += 1
            continue

        # Confirm WHICH account we landed in by reading the assumed identity's ARN
        # (arn:aws:sts::<account>:assumed-role/...), not by trusting the request.
        assumed_arn = resp.get("AssumedRoleUser", {}).get("Arn", "")
        landed_account = _account_from_arn(assumed_arn)
        if landed_account != account_id:
            print(
                f"  [FAIL] {env}: assumed into {landed_account!r}, expected {account_id}",
                file=sys.stderr,
            )
            failures += 1
            continue
        print(f"  [PASS] {env}: returned account id {landed_account}")
        returned.append((env, landed_account))

    print()
    if failures:
        print(f"phase1_gate: FAIL — {failures} member assume(s) did not succeed")
        return 1
    pretty = ", ".join(f"{e}={a}" for e, a in returned)
    print(f"phase1_gate: PASS — assumed all {len(returned)} members ({pretty})")
    return 0


def _account_from_arn(arn: str) -> str:
    """Extract the account id from an ARN (the 5th colon-delimited field)."""
    parts = arn.split(":")
    return parts[4] if len(parts) > 4 else ""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    external_id = _resolve_external_id(args.external_id)
    if not external_id:
        print(
            "phase1_gate: no ExternalId supplied — set PDE_EXTERNAL_ID or pass "
            "--external-id. (It must match the member-role trust condition; never "
            "commit the real value.)",
            file=sys.stderr,
        )
        return 2

    try:
        import boto3  # local import so --help works without boto3 installed
    except ImportError:
        print(
            "phase1_gate: boto3 is not installed. In CloudShell it is preinstalled; "
            "otherwise `pip install boto3`.",
            file=sys.stderr,
        )
        return 2

    sts = boto3.client("sts", region_name=args.region)
    return run_gate(sts, external_id, require_hub=not args.allow_non_hub)


if __name__ == "__main__":
    raise SystemExit(main())
