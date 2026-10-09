import copy
import hashlib
import unittest
from seat4_exchange import BoundaryError, check

def digest(s): return hashlib.sha256(s.encode()).hexdigest()

class TestExchange(unittest.TestCase):
    def setUp(self):
        self.p={"packet_id":"p1","purpose":"cross-evaluation","recipient":"kiro-builder",
                "context":"retrospective","classification":"operating","source_ref":"approved-neutral",
                "source_hash":digest("source"),"payload":"A neutral finding.","payload_hash":digest("A neutral finding."),
                "approval_ref":"approved1"}
        self.sources={"approved-neutral":{"hash":digest("source"),"kind":"approved-finding",
                       "classification":"operating","purpose":"cross-evaluation","recipients":["kiro-builder"]}}
        self.approvals={"approved1":{"verified_human":True,"packet_id":"p1","recipient":"kiro-builder",
                       "source_ref":"approved-neutral","payload_hash":digest("A neutral finding.")}}
    def validate(self,p=None,s=None,a=None,production=False):
        return check(p if p is not None else self.p,s if s is not None else self.sources,
                     a if a is not None else self.approvals,"kiro-builder",production=production)
    def deny(self,**changes):
        with self.assertRaises(BoundaryError): self.validate(p=dict(self.p,**changes))
    def test_valid_offline(self): self.assertEqual(self.validate(),"OFFLINE_VALID_ONLY")
    def test_production_locked(self):
        with self.assertRaisesRegex(BoundaryError,"PRODUCTION_RELEASE_DISABLED"):
            self.validate(production=True)
    def test_recipient(self): self.deny(recipient="copilot-moderator")
    def test_private_class(self): self.deny(classification="seat4-private")
    def test_tamper(self): self.deny(payload="altered")
    def test_source_hash(self): self.deny(source_hash=digest("other"))
    def test_missing_approval(self): self.deny(approval_ref="none")
    def test_false_approval(self):
        a=copy.deepcopy(self.approvals); a["approved1"]["verified_human"]=False
        with self.assertRaises(BoundaryError): self.validate(a=a)
    def test_raw_assessment(self):
        s=copy.deepcopy(self.sources);s["approved-neutral"]["kind"]="raw-assessment"
        with self.assertRaises(BoundaryError): self.validate(s=s)
    def test_context(self): self.deny(context="production")
    def test_extra_field(self):
        with self.assertRaises(BoundaryError): self.validate(p=dict(self.p,override=True))
    def test_missing_field(self):
        p=dict(self.p);p.pop("source_ref")
        with self.assertRaises(BoundaryError):self.validate(p=p)
if __name__=="__main__":unittest.main()
