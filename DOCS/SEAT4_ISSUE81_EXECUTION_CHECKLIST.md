# Issue #81 — Human / Assistant implementation checklist
Status: DRAFT PLAN; no claims of completed security controls.

## A. Human-controlled setup
- [ ] Create a **private** GitHub repository, suggested name `troikauge-seat4-private`, with no template containing production secrets.
- [ ] Confirm initial collaborators and installed GitHub Apps; explicitly remove or avoid production-seat principals.
- [ ] Create dedicated Seat 4 GitHub App in GitHub developer settings; configure repository selection to explicit allowlist.
- [ ] Grant minimum possible read/write scopes only after enumerating required operations, and verify no admin/secret-management privileges.
- [ ] Install App on private repository and only approved public/work repositories as needed.
- [ ] Define branch/ruleset requiring an independently authenticated Human approval for reserved actions.
- [ ] Select an audit log retention destination outside the App's ability to rewrite.

## B. Seat 4 assistant preparation
- [ ] Verify private repo access with the configured App and inspect grants using permitted APIs.
- [ ] Prepare private directories/files (not in PDE) and encrypted-at-rest / GitHub access assumptions.
- [ ] Implement approval receipt validation against authenticated GitHub review/check event, pinned commit and approved scope.
- [ ] Add packet nonces, expiry, idempotency/replay prevention, and append-only release register.
- [ ] Integrate Issue #80 contract only after source/approval registries are independently protected.
- [ ] Perform negative read/write access tests from each production seat and a positive scoped App operation.
- [ ] Present proof to Human, then request distinct authorization to activate (not implicit from PR review).

## C. Cutover gate
DO NOT merge #87 merely because this design is reviewed. It remains draft pending verified tests/dependencies. Do not move raw records into a production-seat-readable shared repo. Do not merge or change operating authority until explicit Human ratification.

## Decision record
- Private storage: separate private GitHub repository — Human selected.
- Identity: dedicated GitHub App / automation identity — Human selected.
- Approval evidence: protected GitHub approval/review record — Human selected.
- Repository name, App installation ID, permissions, ruleset IDs and proof URLs: **not yet supplied or verified**.
