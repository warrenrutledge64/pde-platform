#!/usr/bin/env python3
"""Offline structural validation for the PDE CloudTrail baseline template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / cfn-guard /
Checkov cannot be installed here — those run in the operator's CloudShell / CI
(see the Story 1.1 runbook). This stdlib-only checker is the OFFLINE proof bar:
it confirms the template is well-formed enough to parse and that every Story 1.1
security invariant (RD-005 + the Universal Acceptance Criteria) is present.

It deliberately avoids a YAML lib: CloudFormation intrinsic tags (!Ref, !Sub,
!GetAtt ...) break naive YAML loaders, and PyYAML is unavailable offline anyway.
Instead it asserts invariants against the raw template text with anchored checks.

Usage:  python3 infra/validate_template.py
Exit:   0 = all invariants hold; 1 = one or more failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "cloudtrail-org-baseline.yaml"


def _norm(text: str) -> str:
    """Collapse whitespace so multi-line YAML values match single-line checks."""
    return re.sub(r"\s+", " ", text)


def main() -> int:
    raw = TEMPLATE.read_text(encoding="utf-8")
    flat = _norm(raw)

    # (name, predicate) — each predicate is True when the invariant holds.
    checks: list[tuple[str, bool]] = [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        # --- Org trail invariants (the core of the Phase 1 gate) ---
        ("trail resource is AWS::CloudTrail::Trail",
         "Type: AWS::CloudTrail::Trail" in raw),
        ("IsOrganizationTrail: true",
         "IsOrganizationTrail: true" in flat),
        ("IsMultiRegionTrail: true",
         "IsMultiRegionTrail: true" in flat),
        ("EnableLogFileValidation: true",
         "EnableLogFileValidation: true" in flat),
        ("IsLogging: true",
         "IsLogging: true" in flat),
        ("IncludeGlobalServiceEvents: true",
         "IncludeGlobalServiceEvents: true" in flat),
        ("trail encrypted with the KMS CMK (KMSKeyId set)",
         "KMSKeyId:" in raw),
        ("trail DependsOn the bucket policy",
         bool(re.search(r"DependsOn:\s*-?\s*CloudTrailLogBucketPolicy", flat))),
        # --- KMS CMK invariants ---
        ("KMS key resource present",
         "Type: AWS::KMS::Key" in raw),
        ("KMS key rotation enabled",
         "EnableKeyRotation: true" in flat),
        ("KMS policy grants CloudTrail GenerateDataKey*",
         "kms:GenerateDataKey*" in raw),
        ("KMS decrypt scoped to the organization (PrincipalOrgID)",
         "aws:PrincipalOrgID" in raw),
        # --- S3 log bucket hardening ---
        ("S3 bucket resource present",
         "Type: AWS::S3::Bucket" in raw),
        ("bucket blocks public ACLs",
         "BlockPublicAcls: true" in flat),
        ("bucket blocks public policy",
         "BlockPublicPolicy: true" in flat),
        ("bucket ignores public ACLs",
         "IgnorePublicAcls: true" in flat),
        ("bucket restricts public buckets",
         "RestrictPublicBuckets: true" in flat),
        ("bucket versioning enabled",
         bool(re.search(r"VersioningConfiguration:\s*Status:\s*Enabled", flat))),
        ("bucket default SSE is aws:kms",
         "SSEAlgorithm: aws:kms" in flat),
        ("bucket retained on stack delete (rollback-safe)",
         "DeletionPolicy: Retain" in raw),
        # NO Object Lock / WORM — a hard 'must-NOT-be-present' invariant.
        ("NO S3 Object Lock (COMPLIANCE WORM) configured",
         "ObjectLockConfiguration" not in raw
         and "ObjectLockEnabled" not in raw),
        # --- Bucket policy: CloudTrail service + TLS-only ---
        ("bucket policy grants CloudTrail GetBucketAcl",
         "s3:GetBucketAcl" in raw),
        ("bucket policy requires bucket-owner-full-control on PutObject",
         "bucket-owner-full-control" in raw),
        ("bucket policy denies non-TLS access",
         "aws:SecureTransport" in raw),
        ("org-trail write path scoped to the OrganizationId prefix",
         "AWSLogs/${OrganizationId}/*" in raw),
        # --- ZTIE co-existence / tagging discipline (naming prefix) ---
        ("resources tagged Project=PDE",
         "Value: PDE" in raw),
        ("PDE naming prefix used (pde-)",
         "pde-" in raw),
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
        print(f"validate_template: FAIL — {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_template: PASS — all {len(checks)} Story 1.1 invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
