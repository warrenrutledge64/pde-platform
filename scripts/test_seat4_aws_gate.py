"""Negative contract tests for offline, non-deployable AWS gate."""
import copy
import hashlib
import json
import unittest
from seat4_aws_gate import InvalidRequest, lambda_handler, validate_request

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

class GateTest(unittest.TestCase):
    def setUp(self):
        self.req = {
            "schema_version": "seat4.request.v0",
            "request_id": "request-001", "operation": "verify-private-repo-read",
            "repository": "warrenrutledge64/troikauge-seat4-private",
            "target_sha": "a"*40, "purpose": "identity-boundary-check",
            "recipient": "seat4-internal", "context": "seat4-internal",
            "source_ref": "fixture:readme", "source_sha256": digest("source"),
            "payload_sha256": digest("payload"), "nonce": "unique-001",
            "expires_at": "2027-01-01T00:00:00Z"
        }
    def assert_invalid(self, **changes):
        with self.assertRaises(InvalidRequest):
            validate_request(dict(self.req, **changes))
    def test_schema_valid_but_denied(self):
        result = lambda_handler({"body":json.dumps(self.req)}, None)
        self.assertEqual(result["statusCode"], 403)
        self.assertEqual(json.loads(result["body"])["reason"], "PROTOTYPE_DISABLED")
    def test_no_write_operation(self):
        self.assert_invalid(operation="write-file")
    def test_no_production_repo(self):
        self.assert_invalid(repository="warrenrutledge64/pde-platform")
    def test_no_builder_recipient(self):
        self.assert_invalid(recipient="kiro-builder")
    def test_no_validator_context(self):
        self.assert_invalid(context="gemini-validator-live")
    def test_no_cross_eval_transfer(self):
        self.assert_invalid(purpose="cross-evaluation")
    def test_no_extra_fields(self):
        self.assert_invalid(admin_override=True)
    def test_no_missing_fields(self):
        data=copy.deepcopy(self.req); del data["nonce"]
        with self.assertRaises(InvalidRequest):
            validate_request(data)
    def test_bad_sha(self):
        self.assert_invalid(target_sha="main")
    def test_bad_hash(self):
        self.assert_invalid(payload_sha256="not-hash")
    def test_bad_nonce(self):
        self.assert_invalid(nonce="")
    def test_bad_expiry_format(self):
        self.assert_invalid(expires_at="tomorrow")
    def test_bad_json_denied(self):
        self.assertEqual(lambda_handler({"body":"{"},None)["statusCode"],400)
    def test_no_body_denied(self):
        self.assertEqual(lambda_handler({},None)["statusCode"],400)
    def test_deterministic_request_digest(self):
        self.assertEqual(validate_request(self.req), validate_request(dict(reversed(list(self.req.items())))))

if __name__=="__main__":
    unittest.main()
