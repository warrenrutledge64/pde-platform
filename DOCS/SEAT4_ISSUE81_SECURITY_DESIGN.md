# Troikauge 3.0 — Issue #81: Seat 4 Identity and Private Storage
Status: DESIGN PROPOSAL — NOT IMPLEMENTED / NOT RATIFIED
Human selections: separate PRIVATE GitHub repository; dedicated GitHub App / automation identity; protected GitHub approval/review records.
Applies to: future Seat 4 workflow, with PDE as pilot. Draft PR #87 remains draft.

## Required isolation model
Seat 4 private materials must be in a separate private repository (proposed name: troikauge-seat4-private). It must be inaccessible to Gemini, Kiro, Copilot, and their credentials/tool connections. IMPORTANT: a GitHub repository being 'private' does not imply isolation from collaborators or installed Apps; inspect effective grants. Do not place private records in pde-platform, SDD-repo-kit, BOM, or ZTIE-Issues.

Human owns repository administration and grants. ChatGPT performs authorized actions only through an explicitly approved GitHub App identity and audited workflows. The App's identity must remain visible in Git logs; communications to production seats may remain Stakeholder-channel messages but cannot falsely assert personal Human authorship or approval.

## Private repo suggested structure
- policy/seat4-charter.md — governance and permitted authority
- approvals/ — **references and receipts only**, not unverified self-entered approval flags
- cross-eval/<cycle>/raw/ — separate original Gemini-P, Gemini-V, Kiro and Copilot assessments
- cross-eval/<cycle>/provenance/ — source mapping, hashes, evidence register
- cross-eval/<cycle>/internal/ — protected analysis and unified drafts
- releases/<cycle>/ — sanitized packet manifests and Human-approved release records
- audit/ — append-only event export or references to independently retained audit logs
Do not store credentials, tokens, live secrets, or irrelevant personal information in the repository. Git history alone is not immutable against privileged history changes; retention and independent export are required.

## Credential model
Create/install a dedicated GitHub App limited to exact repositories and minimum Contents / Pull requests / Issues permissions needed for Seat 4. Avoid broad repository administration or workflow write permissions for normal operation. Separate identities for production seats; deny those principals access to private Seat 4 repository. Use short-lived installation tokens. Never put credentials in prompts, committed JSON, issue bodies, or PRs.
For approval records, require authenticated Human action on a protected PR or a protected approval workflow. A ChatGPT-authored file, 'verified_human': true boolean, comment, or RATIFIED marker alone is NOT an authentic approval. Preserve actor ID, GitHub event ID/URL, target commit hash, scope and timestamp.

## Separation of duties
- Human: repo creation, GitHub App grants, approval, ratification, merge.
- Seat 4 assistant: packet drafting, source-bound administrative files, controlled PR preparation, retrospective processing in private repository.
- Kiro: design and build only.
- Gemini: Planner/Validator authoring authority in strictly separate contexts.
- Copilot: official Moderator precondition attestations.
No production seat gets private raw cross-eval information. No retrospective material enters an active Validator context.

## Exchange transport
No direct raw reads by production seats. Seat 4 prepares role-specific packets, validates source/provenance and destination, and obtains independent Human approval when required. The GitHub App publishes only the minimal approved packet to the authorized channel. All releases must have unique IDs, content hash, source reference/hash, intended recipient, context, purpose, expiry, nonce/replay tracking, identity, and authorization reference.
If any check cannot complete: BLOCK RELEASE, log reason, request Human review. The Issue #80 checker is an offline prototype and must remain incapable of release until this control plane exists.

## Historical exposure
PDE currently contains DOCS/cross-eval/2026-10-09-dryrun/ raw assessments and synthesis/provenance. Treat historical access as potentially exposed wherever seat credentials could access PDE. Do not claim confidentiality has been restored simply by moving files. Preserve and assess the historical records, identify affected accessors, and create a Human-approved retention/remediation plan without silent deletions.

## Required evidence before completion
1. Private repo exists and visibility is confirmed via GitHub metadata.
2. Authorized Human and Seat 4 App access demonstrated; effective access for each production-seat principal reviewed and DENIED.
3. Dedicated App permissions explicitly enumerated, least privilege verified, token lifecycle and rotation documented.
4. Branch protection/rulesets and required Human approval verified (including protection from automation self-approval).
5. Separate, independently retained audit log design verified.
6. Negative tests: denied read, write, issue/comment, PR, checkout and clone where applicable; attempted forged approval; release replay; wrong audience; raw information leak; Validator context contamination.
7. Recorded Human sign-off at pinned revision. No close-out on screenshots or prompt claims alone.

## Dependency
Blocked on the Human actually creating/authorizing private repo and GitHub App. Existing connector access cannot establish that a new App is installed or that credential separation is enforced. No automatic cutover of Kiro responsibilities before #81 and #85 controls pass.
