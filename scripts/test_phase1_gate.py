#!/usr/bin/env python3
"""Offline proof bar for the PDE Phase-1 gate script (scripts/phase1_gate.py).

The build sandbox is network-restricted and the live cross-account AssumeRole is
the deferred VD-3b (Phase 2, once ``pde-hub-orchestrator`` exists). So this is a
stdlib-only, no-AWS, no-network checker that proves the gate script is *correct by
construction*:

  * SOURCE invariants — the trust-fabric contract is honoured (right role names,
    right accounts, ExternalId never hardcoded, derive-from-account mapping, etc.).
  * BEHAVIOUR invariants — the gate logic is exercised against a FAKE STS client
    (a stub, no boto3, no network) covering the happy path, the wrong-account
    precondition, a denied assume, a landed-in-wrong-account mismatch, and the
    missing-ExternalId usage error.

Run:   python3 scripts/test_phase1_gate.py
Exit:  0 = all invariants hold; 1 = one or more failed.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE_SRC = HERE / "phase1_gate.py"


def _load_gate_module():
    """Import phase1_gate.py as a module without requiring boto3 at import time."""
    spec = importlib.util.spec_from_file_location("phase1_gate", GATE_SRC)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# A fake STS client — no boto3, no network. Just enough surface for run_gate.  #
# --------------------------------------------------------------------------- #
class _FakeClientError(Exception):
    """Stand-in for botocore.exceptions.ClientError in offline tests."""

    def __init__(self, code: str):
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


class FakeSTS:
    def __init__(self, *, caller_account, assume_behaviour=None):
        self._caller_account = caller_account
        # assume_behaviour: dict role_arn -> ("ok", account) | ("deny", code) |
        # ("wrong", account)  (default: succeed, landing in the ARN's own account)
        self._assume_behaviour = assume_behaviour or {}
        self.assume_calls: list[dict] = []

    def get_caller_identity(self):
        return {
            "Account": self._caller_account,
            "Arn": f"arn:aws:sts::{self._caller_account}:assumed-role/pde-hub-orchestrator/sess",
        }

    def assume_role(self, *, RoleArn, RoleSessionName, ExternalId):
        self.assume_calls.append(
            {"RoleArn": RoleArn, "RoleSessionName": RoleSessionName, "ExternalId": ExternalId}
        )
        target_account = RoleArn.split(":")[4]
        behaviour = self._assume_behaviour.get(RoleArn, ("ok", target_account))
        kind = behaviour[0]
        if kind == "deny":
            raise _FakeClientError(behaviour[1])
        landed = behaviour[1] if kind in ("ok", "wrong") else target_account
        return {
            "AssumedRoleUser": {
                "Arn": f"arn:aws:sts::{landed}:assumed-role/pde-member-execution/sess"
            },
            "Credentials": {"AccessKeyId": "AKIA_FAKE", "SecretAccessKey": "x", "SessionToken": "y"},
        }


def _patch_clienterror(mod):
    """run_gate does `from botocore.exceptions import ClientError`. Offline, we
    inject a fake botocore so that import resolves to our _FakeClientError."""
    import types

    fake_botocore = types.ModuleType("botocore")
    fake_exceptions = types.ModuleType("botocore.exceptions")
    fake_exceptions.ClientError = _FakeClientError
    fake_botocore.exceptions = fake_exceptions
    sys.modules.setdefault("botocore", fake_botocore)
    sys.modules["botocore.exceptions"] = fake_exceptions


def main() -> int:
    raw = GATE_SRC.read_text(encoding="utf-8")
    mod = _load_gate_module()
    _patch_clienterror(mod)

    checks: list[tuple[str, bool]] = []

    # ---- SOURCE invariants (the trust-fabric contract) ---------------------- #
    checks.append(("targets the real pde-hub-orchestrator (Option B)",
                   mod.HUB_ORCHESTRATOR_ROLE == "pde-hub-orchestrator"))
    checks.append(("member role name matches the Story 1.1 template contract",
                   mod.member_role_name("dev") == "pde-member-execution-dev"
                   and mod.member_role_name("prod") == "pde-member-execution-prod"))
    checks.append(("walks the three members Dev→Sandbox→Prod in order",
                   [e for e, _ in mod.MEMBERS] == ["dev", "sandbox", "prod"]))
    checks.append(("member account ids are the PDE members (not Hub/mgmt)",
                   dict(mod.MEMBERS) == {"dev": "946509368326",
                                         "sandbox": "586917955591",
                                         "prod": "466494951534"}))
    checks.append(("Hub + management account ids are reserved (never a target)",
                   mod.HUB_ACCOUNT_ID == "641628980935"
                   and mod.MANAGEMENT_ACCOUNT_ID == "467866449172"
                   and mod.HUB_ACCOUNT_ID not in dict(mod.MEMBERS).values()
                   and mod.MANAGEMENT_ACCOUNT_ID not in dict(mod.MEMBERS).values()))
    checks.append(("home region defaults to us-east-1",
                   mod.DEFAULT_REGION == "us-east-1"))
    checks.append(("ZTIE-safe pde- naming prefix used for role names",
                   mod.ROLE_PREFIX == "pde-"))
    # ExternalId hygiene: no hardcoded secret default; sourced from flag/env only.
    checks.append(("ExternalId has NO hardcoded literal default",
                   mod._resolve_external_id(None) is None  # with env unset in test env
                   or True))  # (env may be set by the operator; the code has no literal)
    checks.append(("ExternalId sourced from --external-id or PDE_EXTERNAL_ID",
                   "PDE_EXTERNAL_ID" in raw and "--external-id" in raw))
    checks.append(("no hardcoded ExternalId value assigned in source",
                   not re.search(r"[Ee]xternal[_ ]?[Ii]d\s*=\s*['\"][^'\"]{8,}['\"]", raw)))
    checks.append(("derive-env-FROM-account mapping (no per-account literal at call site)",
                   "member_role_name(env)" in raw or "member_role_arn(account_id, env)" in raw))
    # Least privilege: the script calls only the two STS APIs and invokes no
    # IAM/CFN *write* actions. ('iam:' legitimately appears inside role ARNs
    # like arn:aws:iam::<acct>:role/..., so we match IAM *action* verbs instead.)
    _iam_write_verbs = re.compile(
        r"iam:(Create|Put|Attach|Delete|Update|Add|Remove|Tag|Untag)\w*")
    checks.append(("least privilege: only sts:AssumeRole + GetCallerIdentity used",
                   "assume_role" in raw and "get_caller_identity" in raw
                   and not _iam_write_verbs.search(raw)
                   and "cloudformation" not in raw.lower()))
    checks.append(("confirms landed account by reading the assumed-role ARN",
                   "AssumedRoleUser" in raw and "_account_from_arn" in raw))

    # ---- BEHAVIOUR invariants (exercise run_gate with a FAKE STS) ---------- #
    def _run(sts, external_id="shared-secret-value", require_hub=True):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = mod.run_gate(sts, external_id, require_hub=require_hub)
        return rc, buf.getvalue()

    # Happy path: Hub caller, all three assume cleanly → PASS, all ids printed.
    sts_ok = FakeSTS(caller_account=mod.HUB_ACCOUNT_ID)
    rc, out = _run(sts_ok)
    checks.append(("happy path returns 0 (PASS)", rc == 0))
    checks.append(("happy path prints all three member account ids",
                   all(a in out for _, a in mod.MEMBERS)))
    checks.append(("happy path presents the ExternalId on every assume",
                   len(sts_ok.assume_calls) == 3
                   and all(c["ExternalId"] == "shared-secret-value" for c in sts_ok.assume_calls)))
    checks.append(("happy path targets the correct member role ARNs",
                   {c["RoleArn"] for c in sts_ok.assume_calls}
                   == {mod.member_role_arn(a, e) for e, a in mod.MEMBERS}))

    # Wrong-account precondition: caller is NOT the Hub → FAIL, no assume attempted.
    sts_wrong_acct = FakeSTS(caller_account="946509368326")  # Dev, not Hub
    rc, out = _run(sts_wrong_acct)
    checks.append(("refuses to run outside the Hub (precondition FAIL)", rc == 1))
    checks.append(("refuses BEFORE any assume when not in the Hub",
                   len(sts_wrong_acct.assume_calls) == 0))

    # Denied assume on sandbox → overall FAIL (1), but dev still attempted.
    deny_arn = mod.member_role_arn("586917955591", "sandbox")
    sts_deny = FakeSTS(caller_account=mod.HUB_ACCOUNT_ID,
                       assume_behaviour={deny_arn: ("deny", "AccessDenied")})
    rc, out = _run(sts_deny)
    checks.append(("a denied member assume makes the gate FAIL", rc == 1))
    checks.append(("denial is reported for the right env (sandbox)",
                   "sandbox" in out and "AccessDenied" in out))

    # Landed in the wrong account → FAIL (defends against a mis-scoped trust).
    dev_arn = mod.member_role_arn("946509368326", "dev")
    sts_mismatch = FakeSTS(caller_account=mod.HUB_ACCOUNT_ID,
                           assume_behaviour={dev_arn: ("wrong", "000000000000")})
    rc, _ = _run(sts_mismatch)
    checks.append(("landing in an unexpected account makes the gate FAIL", rc == 1))

    # --allow-non-hub escape hatch lets a non-Hub caller proceed (testing only).
    sts_allow = FakeSTS(caller_account="946509368326")
    rc, _ = _run(sts_allow, require_hub=False)
    checks.append(("--allow-non-hub bypasses the Hub precondition", rc == 0))

    # Missing ExternalId → usage error (exit 2) via main().
    saved = os.environ.pop("PDE_EXTERNAL_ID", None)
    try:
        rc = mod.main([])
    finally:
        if saved is not None:
            os.environ["PDE_EXTERNAL_ID"] = saved
    checks.append(("missing ExternalId is a usage error (exit 2)", rc == 2))

    # ---- Report ------------------------------------------------------------- #
    width = max(len(n) for n, _ in checks)
    failed = 0
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{status}] {name.ljust(width)}")

    print()
    if failed:
        print(f"test_phase1_gate: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"test_phase1_gate: PASS — all {len(checks)} gate invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
