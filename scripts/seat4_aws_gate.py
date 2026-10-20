"""Troikauge Seat 4 AWS Lambda CONTRACT PROTOTYPE — no credentials or release capability.

Every call denies authorization even if the request schema is valid. This file
contains no boto3 calls, AWS resource creation, GitHub token exchange or writes.
"""
import hashlib
import json
import re

FIELDS = frozenset({
    "schema_version", "request_id", "operation", "repository", "target_sha",
    "purpose", "recipient", "context", "source_ref", "source_sha256",
    "payload_sha256", "nonce", "expires_at"
})
ALLOWED_OPERATIONS = frozenset({"verify-private-repo-read"})
ALLOWED_REPO = "warrenrutledge64/troikauge-seat4-private"
ALLOWED_RECIPIENTS = frozenset({"seat4-internal"})
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

class InvalidRequest(ValueError):
    pass

def validate_request(body):
    if not isinstance(body, dict) or frozenset(body) != FIELDS:
        raise InvalidRequest("unexpected or missing fields")
    if body["schema_version"] != "seat4.request.v0":
        raise InvalidRequest("unsupported schema")
    if body["operation"] not in ALLOWED_OPERATIONS or body["repository"] != ALLOWED_REPO:
        raise InvalidRequest("operation/repository not permitted")
    if body["recipient"] not in ALLOWED_RECIPIENTS or body["context"] != "seat4-internal":
        raise InvalidRequest("invalid audience/context")
    if body["purpose"] != "identity-boundary-check":
        raise InvalidRequest("unapproved purpose")
    if not isinstance(body["target_sha"], str) or not SHA40.fullmatch(body["target_sha"]):
        raise InvalidRequest("target must be pinned SHA")
    for k in ("source_sha256", "payload_sha256"):
        if not isinstance(body[k], str) or not HEX64.fullmatch(body[k]):
            raise InvalidRequest("invalid digest")
    for k in ("request_id", "source_ref", "nonce"):
        if not isinstance(body[k], str) or not ID.fullmatch(body[k]):
            raise InvalidRequest("invalid identifier")
    # Caller-controlled timestamps must be authenticated and checked by the
    # eventual gate; do NOT treat a syntactically valid date as authorized.
    if not isinstance(body["expires_at"], str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", body["expires_at"]
    ):
        raise InvalidRequest("invalid expiry format")
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def lambda_handler(event, context):
    """Prototype API handler: schema lint; NEVER authorizes or executes."""
    try:
        payload = event.get("body") if isinstance(event, dict) else None
        body = json.loads(payload) if isinstance(payload, str) else payload
        request_hash = validate_request(body)
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
            "body": json.dumps({"status": "DENIED", "reason": "PROTOTYPE_DISABLED",
                                "request_sha256": request_hash})
        }
    except (InvalidRequest, ValueError, TypeError):
        return {"statusCode": 400, "headers": {"Content-Type": "application/json",
                                               "Cache-Control": "no-store"},
                "body": json.dumps({"status": "DENIED", "reason": "INVALID_REQUEST"})}
