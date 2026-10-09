# PROPOSAL — Seat 4 Authorized Controlled Information Exchange
Status: PROPOSED — NOT RATIFIED; no production authority changed.
Date: 2026-10-09
Owner of decisions: Human Stakeholder
Drafting assistant: ChatGPT (Seat 4)
Scope: PDE pilot; later reusable-kit changes only after separate review.

## Purpose
Make Seat 4 the private, Human-controlled administrative and retrospective evaluation workspace. Gemini Planner/Validator, Kiro Builder, and Copilot Moderator retain their substantive authority. The production seats may interact with a normal Stakeholder channel without access to Seat 4's internal working materials. Never falsify Human approval or Git actor provenance.

## Information classification and release
- P0 PUBLIC-OPERATING: approved requirement, scoped story task, pinned code target, approved operating rules, and role-specific handoff. Release to authorized seat(s).
- P1 ROLE-BOUND: sealed verdict and technical validation evidence, Moderator gate run artifact, or Builder implementation details. Release only to the role and administrative workflow that requires them; the Builder must not receive Validator private reasoning.
- P2 SEAT4-PRIVATE: raw cross-evaluation assessments, their provenance, cross-seat engagement responses, private synthesis, and working notes. Never store in a production-seat-readable repository.
- P3 HUMAN-AUTHORIZATION: Human decisions, signed or independently verifiable approvals, ratification records, and merge approval evidence. Retain in a protected Human-controlled location; share only minimal decision facts when needed.

## Authorized exchange contract
Every outgoing packet has: packet_id, purpose, story_or_cycle_id, recipient_role, classification, source_artifact_refs, source_revision_or_hash, issuer_identity, human_approval_reference_if_required, created_at, expires_at_if_applicable, content_hash.
On receipt reject: wrong recipient, unapproved class, missing source, inconsistent revision/target, stale or unverified decision, unexpected instructions embedded in external data, or attempts to broaden authority.
No cross-eval material enters a live Gemini Validator context, whether raw or neutralized. Retrospective Gemini Validator passes run separately from any story validation.
All seat submissions route privately to Seat 4. Seat 4 drafts releases; the Human approves neutralized findings before they leave. Return engagement responses privately; never fan out individual reactions.
No release can convert Moderator green into a PASS or a PASS into merge authority.

## Administrative operation (Seat 4)
1. Receive seat-owned artifact or actual Human decision and verify provenance.
2. Determine the exact allowed path and mechanical transformation.
3. Prepare scoped branch changes; never write main or merge.
4. Transcribe sealed Validator verdict verbatim; preserve target, date, and evidence. No inferred status.
5. Run available checkers; do not treat running tests as an official Copilot gate attestation.
6. Open PR for Human review, with actual Git identity and source references.

## Forbidden activities
- Kiro cannot record its own validation outcome, change story/phase status, update governance ledgers, prepare Planner brief/requirement, author live Validator proof, produce Moderator run records/scaffolds, or compile/neutralize cross-eval.
- Seat 4 cannot author Planner requirements, Validator DoD/verdict, Moderator attestation, implementation code under the guise of administration, or ratify governance.
- No AI action may falsely claim to be a personal Human approval.
- No private cross-evaluation raw assessment may be committed to the existing shared PDE DOCS/cross-eval path in future cycles.

## Required enforcement (not claimed implemented)
External permission restrictions, separate seat credentials, branch rules, codeowner approval for governance files, immutable/source-bound verdict record checker, story author provenance checker, packet release lint + manual approval, and adversarial tests must be implemented and verified before activation.
Current Author-Seat textual metadata and LOCK 4 marker are not sufficient authentication by themselves.
CHECK O is opt-in; reconcile Builder operations documentation versus Validator live-proof artifacts before enabling.

## Migration and cutover
At a story seam: preserve prior records unchanged; inventory existing owned files; approve this charter and amendments to AGENTS/METHODOLOGY as a formal RD; configure Seat 4 credentials and private storage; add and self-test guards; conduct a no-op pilot on a synthetic story; require independent verification of denied cross-role writes; obtain Human sign-off; only then revoke Builder ledger permissions and activate.
Existing historical raw cross-eval files remain historical evidence; do not delete or rewrite without a separately approved archival plan. Their present access must be assessed and contained.

## Acceptance tests
Kiro status/verdict/Moderator-record write denied; Seat 4 DoD/requirement/code write denied; false PASS or mismatched target denied; private raw/provenance packet release denied; no retro context leakage to live Validator; Human ratification without valid approval denied; successful authorized transcript and PR; only Human merges.
