#!/usr/bin/env python3
"""Offline structural validation for the PDE Golden-Path artifact template.

The build sandbox is network-restricted (no PyPI), so cfn-lint / Checkov run
operator-side / in CI (see .github/workflows/static-bar.yml + CONTRIBUTING.md).
This stdlib-only checker is the OFFLINE proof bar for the Story 3.1 Golden-Path
payload (RD-003/RD-004/RD-009): it confirms the template is well-formed and that
every "trivial, zero-cost, ZTIE-safe single resource" invariant holds.

Story 3.1 is AUTHOR + OFFLINE-PROOF ONLY. Nothing is deployed here; the first
live deploy is Story 3.2, THROUGH the pipeline. So this checker never touches
AWS - it is pure static analysis of the committed template text.

It also mirrors the Phase-2 lessons so that class of defect is caught OFFLINE:
the CloudFormation top-level Description byte limit (cfn-lint E1003) and plain
ASCII in any pasted text (an em-dash broke CreateRole in Phase 2).

Usage:
    python3 infra/validate_golden_path_artifact.py      # validate the real template
    python3 infra/validate_golden_path_artifact.py --self-test
        # prove the guard actually FAILS on broken input, in memory, no disk write.
Exit:   0 = all invariants hold (or self-test passed); 1 = one or more failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "golden-path-artifact.yaml"

# CloudFormation hard limit on the top-level template Description (cfn-lint E1003).
CFN_DESCRIPTION_MAX_BYTES = 1024


def _strip_comments(text: str) -> str:
    """Drop YAML comment content so structural invariants test the TEMPLATE, not
    the prose (an explanatory 'no CMK' comment must not be mistaken for the
    property). Invariants that must inspect a COMMENT (the checkov:skip
    suppressions) test the RAW un-stripped text instead.
    """
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _description_bytes(raw_text: str) -> int:
    """Rendered byte length of the top-level folded ('>-') Description block,
    matching what CloudFormation stores / what cfn-lint E1003 counts.
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


def _description_prose_lines(text: str) -> set[str]:
    """Return the set of lines that are explanatory Description prose.

    A `pde-` token is permitted in prose that CITES the RD-009 rule, but never in
    a value that names/exports a resource. A line is prose if it is the
    `Description:` key line itself (folded or inline) OR a continuation line of a
    folded ('>-') Description block (more-indented than the `Description:` key,
    until the indentation returns to the key's level or less).
    """
    prose: set[str] = set()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"(\s*)Description:\s*(>-|>|\|)?\s*$|(\s*)Description:\s*\S", line)
        key = re.match(r"(\s*)Description:", line)
        if key:
            prose.add(line)
            indent = len(key.group(1))
            folded = bool(re.search(r"Description:\s*(>-|>|\|)\s*$", line))
            if folded:
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.strip() == "":
                        prose.add(nxt)
                        j += 1
                        continue
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent > indent:
                        prose.add(nxt)
                        j += 1
                    else:
                        break
                i = j
                continue
        i += 1
    return prose


def run_checks(template_text: str) -> list[tuple[str, bool]]:
    """Return the (name, ok) invariant list for a template's TEXT.

    Pure function of the text, so --self-test can feed it a deliberately broken
    template in memory (no file, no disk write).
    """
    raw = _strip_comments(template_text)  # structure invariants
    full = template_text                  # comment-aware invariants (suppressions)
    prose_lines = _description_prose_lines(raw)  # lines allowed to cite "pde-"

    # Count only RESOURCE declarations (indented "Type:" under Resources), not the
    # AttributeType: S inside the resource properties.
    resource_type_lines = re.findall(r"\n    Type:\s*AWS::", template_text)

    return [
        ("template format version present",
         "AWSTemplateFormatVersion:" in raw),
        ("template is plain ASCII (no em-dash / smart quotes - Phase 2 CreateRole trap)",
         all(ord(c) <= 127 for c in template_text)),
        # --- cfn-lint E1003: Description within the 1024-byte CFN limit ---
        (f"template Description within the CFN {CFN_DESCRIPTION_MAX_BYTES}-byte limit (cfn-lint E1003)",
         0 < _description_bytes(full) <= CFN_DESCRIPTION_MAX_BYTES),
        # --- EXACTLY ONE trivial resource (the whole point of Story 3.1) ---
        ("declares EXACTLY ONE resource (a trivial single-resource payload)",
         len(resource_type_lines) == 1),
        ("the single resource is an on-demand DynamoDB table",
         raw.count("Type: AWS::DynamoDB::Table") == 1),
        ("GoldenPathTable resource present",
         "GoldenPathTable:" in raw),
        # --- Zero-cost: on-demand, no provisioned capacity, no streams/GSI/CMK/PITR ---
        ("billing is PAY_PER_REQUEST (on-demand - no provisioned capacity)",
         "BillingMode: PAY_PER_REQUEST" in raw),
        ("no provisioned ProvisionedThroughput block (would add standing cost)",
         "ProvisionedThroughput" not in raw),
        ("no DynamoDB stream (StreamSpecification absent - keep it trivial/free)",
         "StreamSpecification" not in raw),
        ("no secondary indexes (GlobalSecondaryIndexes/LocalSecondaryIndexes absent)",
         "SecondaryIndexes" not in raw),
        ("no customer-managed KMS key (SSESpecification absent -> free AWS-owned key)",
         "SSESpecification" not in raw and "KMSMasterKeyId" not in raw
         and "KmsMasterKeyId" not in raw),
        ("point-in-time recovery not enabled (adds cost; nothing durable to recover)",
         "PointInTimeRecoveryEnabled: true" not in raw),
        ("a minimal single-attribute HASH key schema",
         "KeyType: HASH" in raw and "AttributeType: S" in raw
         and "RANGE" not in raw),
        # --- Justified security-scanner skips (checkov), repo-standard pattern ---
        ("CKV_AWS_119 (DynamoDB CMK) carries a justified checkov:skip",
         full.count("checkov:skip=CKV_AWS_119:") == 1),
        ("CKV_AWS_28 (DynamoDB PITR) carries a justified checkov:skip",
         full.count("checkov:skip=CKV_AWS_28:") == 1),
        # --- ZTIE-safe naming (RD-009): pdlv-, never pde- ---
        ("name prefix parameter is exactly pdlv- (RD-009)",
         bool(re.search(r'AllowedPattern:\s*"\^pdlv-\$"', raw))),
        ("prefix default is pdlv-",
         bool(re.search(r"Default:\s*pdlv-", raw))),
        ("table name uses the ${NamePrefix} prefix",
         '!Sub "${NamePrefix}${ArtifactName}"' in raw),
        ("no bare pde- resource name (ZTIE's namespace)",
         not re.search(r'(TableName|Name):\s*[!"\s]*[^\n]*"?pde-', raw)),
        ("exports use the pdlv- prefix (via ${NamePrefix})",
         "${NamePrefix}golden-path-artifact-table-name" in raw
         and "${NamePrefix}golden-path-artifact-table-arn" in raw),
        # Any `pde-` MUST only appear in explanatory Description prose (which cites
        # the RD-009 rule), NEVER in a value that names/defaults/exports a resource
        # (TableName / Name / Default / AllowedPattern / Export Name / !Sub value).
        ("no pde- in any naming/default/export value (only in Description prose)",
         not any(
             "pde-" in line and line not in prose_lines
             for line in raw.splitlines()
         )),
        # --- Project=PDE tagging on the taggable resource ---
        ("resource tagged Project=PDE",
         "Key: Project, Value: PDE" in raw),
        ("the single taggable resource carries Project=PDE exactly once",
         raw.count("Key: Project, Value: PDE") == 1),
        # --- Least privilege / blast radius: no IAM, no wildcards (author-only) ---
        ("no IAM resource (the payload is a bare data resource, not a role/policy)",
         "AWS::IAM::" not in raw),
        ("no full wildcard action",
         not re.search(r"Action:\s*['\"]\*['\"]", raw)),
        # --- ZTIE-safe / zero-touch-root / Hub-only account hygiene ---
        ("no reference to the management/root account 467866449172 (zero-touch)",
         "467866449172" not in raw),
        ("no reference to the Pipeline-Forensics (ZTIE) account 360999005254",
         "360999005254" not in raw),
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
        print(f"validate_golden_path_artifact: FAIL - {failed} invariant(s) not satisfied")
        return 1
    print(f"validate_golden_path_artifact: PASS - all {len(checks)} artifact invariants hold")
    return 0


def self_test() -> int:
    """Prove the guard GUARDS - in memory, no disk write.

    Takes the real template, applies sabotages that mirror the ways a "trivial
    zero-cost ZTIE-safe single resource" could silently break, and asserts the
    relevant invariant flips to FAIL. Then confirms the pristine template passes.
    """
    good = TEMPLATE.read_text(encoding="utf-8")

    sabotages: list[tuple[str, str, str]] = [
        # (label, broken_text, the invariant-name substring that must now FAIL)
        ("pde- namespace regression",
         good.replace("pdlv-", "pde-"),
         "no pde- in any naming/default/export value"),
        ("provisioned capacity injected (not zero-cost)",
         good.replace(
             "BillingMode: PAY_PER_REQUEST",
             "BillingMode: PROVISIONED\n      ProvisionedThroughput:\n"
             "        ReadCapacityUnits: 5\n        WriteCapacityUnits: 5"),
         "no provisioned ProvisionedThroughput block"),
        ("a second resource added (no longer a single trivial payload)",
         good.replace(
             "# ---------------------------------------------------------------------------\n"
             "# OUTPUTS",
             "  SecondQueue:\n    Type: AWS::SQS::Queue\n"
             "    Properties:\n      QueueName: !Sub \"${NamePrefix}extra\"\n\n"
             "# ---------------------------------------------------------------------------\n"
             "# OUTPUTS"),
         "declares EXACTLY ONE resource"),
        ("DynamoDB stream enabled (not trivial)",
         good.replace(
             "      BillingMode: PAY_PER_REQUEST",
             "      BillingMode: PAY_PER_REQUEST\n"
             "      StreamSpecification:\n        StreamViewType: NEW_IMAGE"),
         "StreamSpecification absent"),
        ("dropped Project=PDE tag",
         good.replace("- { Key: Project, Value: PDE }\n", "", 1),
         "carries Project=PDE exactly once"),
        ("dropped CKV_AWS_119 skip justification",
         good.replace("checkov:skip=CKV_AWS_119:", "nope:", 1),
         "CKV_AWS_119 (DynamoDB CMK) carries a justified checkov:skip"),
        ("non-ASCII em-dash injected (Phase 2 CreateRole trap)",
         good.replace("zero-cost", "zero\u2014cost", 1),
         "plain ASCII"),
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
        print("validate_golden_path_artifact --self-test: FAIL - a sabotage was NOT caught")
        return 1
    clean_fail = sum(1 for _, ok in run_checks(good) if not ok)
    if clean_fail:
        print(f"validate_golden_path_artifact --self-test: FAIL - clean template has {clean_fail} failing invariant(s)")
        return 1
    print("validate_golden_path_artifact --self-test: PASS - guard flips to FAIL on every sabotage; clean template passes")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    return _report(run_checks(TEMPLATE.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
