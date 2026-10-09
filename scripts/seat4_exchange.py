"""OFFLINE-only Seat 4 packet checker. Does not send or certify Human identity."""
import hashlib
import json
import re

class BoundaryError(ValueError):
    pass

REQUIRED = {"packet_id","purpose","recipient","context","classification","source_ref",
            "source_hash","payload","payload_hash","approval_ref"}
ROLES = {"gemini-planner","gemini-validator-live","gemini-validator-retro","kiro-builder","copilot-moderator"}
PRIVATE = {"raw-assessment","private-provenance","engagement-response","private-synthesis"}

def check(packet, sources, approvals, target, *, production=True):
    if not isinstance(packet,dict) or set(packet) != REQUIRED:
        raise BoundaryError("incorrect packet fields")
    if packet["recipient"] != target or target not in ROLES:
        raise BoundaryError("recipient mismatch")
    if packet["classification"] not in ("operating","role-bound"):
        raise BoundaryError("private or unknown classification")
    if packet["context"] not in ("production","retrospective"):
        raise BoundaryError("unrecognized context")
    if target == "gemini-validator-live" and packet["context"] != "production":
        raise BoundaryError("live validator context separation")
    if packet["purpose"] == "cross-evaluation" and packet["context"] != "retrospective":
        raise BoundaryError("cross-evaluation cannot enter production")
    for field in ("packet_id","purpose","source_ref","approval_ref"):
        if not isinstance(packet[field],str) or not packet[field]:
            raise BoundaryError("missing required identifier")
    if not isinstance(packet["payload"],str):
        raise BoundaryError("invalid payload")
    for field in ("source_hash","payload_hash"):
        if not isinstance(packet[field],str) or not re.fullmatch(r"[0-9a-f]{64}",packet[field]):
            raise BoundaryError("invalid digest")
    if hashlib.sha256(packet["payload"].encode()).hexdigest() != packet["payload_hash"]:
        raise BoundaryError("tampered packet")
    source=sources.get(packet["source_ref"])
    if not isinstance(source,dict) or source.get("hash") != packet["source_hash"]:
        raise BoundaryError("unverified source")
    if source.get("kind") in PRIVATE or target not in source.get("recipients",[]):
        raise BoundaryError("protected source or unauthorized recipient")
    if source.get("classification") != packet["classification"] or source.get("purpose") != packet["purpose"]:
        raise BoundaryError("inconsistent source metadata")
    approval=approvals.get(packet["approval_ref"])
    if not isinstance(approval,dict) or approval.get("verified_human") is not True:
        raise BoundaryError("no externally verified Human approval")
    for key in ("packet_id","recipient","source_ref","payload_hash"):
        if approval.get(key) != packet[key]:
            raise BoundaryError("approval mismatch")
    if production:
        raise BoundaryError("PRODUCTION_RELEASE_DISABLED")
    return "OFFLINE_VALID_ONLY"

def main():
    import argparse
    parser=argparse.ArgumentParser(description="Offline Seat 4 packet lint only; never transmits")
    parser.add_argument("packet")
    parser.add_argument("--sources",required=True)
    parser.add_argument("--approvals",required=True)
    parser.add_argument("--recipient",required=True)
    args=parser.parse_args()
    try:
        def load(p):
            with open(p,encoding="utf-8") as f: return json.load(f)
        print(check(load(args.packet),load(args.sources),load(args.approvals),args.recipient,production=False))
    except (BoundaryError,ValueError,TypeError,OSError) as e:
        print("DENY:",e)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
