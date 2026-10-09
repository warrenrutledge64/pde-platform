# Seat 4 Authorized Controlled Exchange — Issue #80
Status: PROTOTYPE ONLY — NOT RATIFIED; never enables production release.

## Purpose
Three production seats receive scoped inputs through the Stakeholder channel. Seat 4 privately stores cross-seat assessment originals, evidence mapping, and Human approval records. Human authority is not inferred from the existence of a message or an AI draft.

## Classification and destination
- operating: approved story task or neutralized retrospective finding to an authorized role.
- role-bound: tightly limited validation or gate inputs, delivered only to that role.
- seat4-private: raw self-assessments, provenance keys, engagement responses, private synthesis. NEVER released.
- human-authorization: private independent approval evidence. NEVER distributed as a raw record.

## Packet
Required: packet_id, purpose, recipient, context, classification, source_ref, source_hash, payload, payload_hash, approval_ref.
The source registry and Human approval registry must be controlled outside Builder-readable or Builder-writable files. A packet cannot approve itself. Git authorship and approval identity must be factual.

## Fail-closed requirements
Reject wrong recipient, private classification, live Validator retrospective content, source revision mismatch, modified payload, protected raw source, missing Human approval, and altered approval scope. Running ordinary code checks does not create Copilot's official Moderator attestation. A green Moderator gate is permission to validate, never PASS.

## Prototype limitations
scripts/seat4_exchange.py is an OFFLINE lint helper only. It accepts supplied JSON registries for testing; it cannot authenticate those registries. Its default production mode always denies and it has no sender. The checks do not detect semantic de-identification failure, prompt-injection embedded in payloads, replay, expiry, or actual context isolation. No claim of full enforcement until Issue #81 provides protected identity/storage, approval authenticity, release logging, and independent permission tests, followed by Human ratification.

## Test
python3 -m unittest discover -s scripts -p test_seat4_exchange.py

## Activation gates
Human ratification; protected independently authenticated registries; replay/expiry rules; role-scoped transport; private-store denial tests; deterministic release log; negative leakage tests; separate Gemini Validator production and retrospective contexts. Until all are independently verified, no packets are authorized for transmission.
