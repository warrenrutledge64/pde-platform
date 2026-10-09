# PROPOSAL — Kiro Administrative Transfer to Seat 4
Status: PROPOSED — NOT RATIFIED
Date: 2026-10-09

## Responsibility map
| Activity | Authoritative owner | Seat 4 operation |
|---|---|---|
| Story selection and strategic brief | Gemini Planner + Human direction | Source-bound filing and scaffolding |
| Requirement and acceptance intent | Gemini Planner | Copy approved artifact unchanged |
| Build design, implementation, implementation tests, feature branch, build PR | Kiro Builder | No substantive involvement |
| Operator implementation notes and deployment instructions | Kiro only if not live proof/rubric | Store/link as Builder-authored |
| Validator DoD, live proof procedure and PASS/FAIL/INCONCLUSIVE | Gemini Validator isolated context | Preserve exact sealed output |
| Moderator preconditions and run attestations | Copilot Moderator | Preserve/route, no re-attestation |
| Story creation scaffolds, initial open rows, ledger synchronization | Seat 4 | Deterministic edits from Planner-authorized inputs |
| Validation Result transcription, status flip after checks | Seat 4 | Verbatim, target-bound, evidence-checked |
| Progress summaries, register bookkeeping, restore/BOM document clerical updates | Seat 4 | Only authenticated sources/decisions; no substantive judgment |
| Administrative Git branches, documentation commits and PRs | Seat 4 | No main merge |
| Technical next-story lessons | Kiro as non-authoritative technical facts | Forward only scoped factual notes to Planner; never draft next requirements |
| Next story brief/prompt | Gemini Planner | Package approved version |
| Cross-eval raw collection, compilation, neutralization draft, engagement logistics and draft synthesis | Seat 4 | Protected workspace only; Human approves release/final |
| Cross-eval final findings and governance ratification | Human | ChatGPT advisory only |
| Main merge | Human | No merge |

## Containment rule
The Builder ends at an implementation handoff with pinned target and implementation facts. It does not resume in a 'Scribe mode.' Repository permissions must enforce this, not just prompts. Existing checkers G/Q/R/LOCK 4/merge order continue, but should be strengthened for actual provenance and write scope.

## Documentation changes required after ratification
- governance/AGENTS.md: remove Builder verdict recording, status changes, warm Planner brief/prompt, and Moderator gate-definition governance authorship if substantive governance is not explicitly delegated and ratified.
- governance/METHODOLOGY.md: replace 'executor records verdict' with Seat 4 transcription; preserve live Human operation and independent validation.
- DOCS/CROSS_EVAL_SYNTHESIS_PROCESS.md: remove shared-repo raw assessment publication and Builder compilation; use private source store and release-only packets.
- DOCS/TROIKAUGE_CROSS_EVAL_PROMPT.md: change routing and avoid pressuring fabricated weaknesses.
- SDD-repo-kit starter BOOTSTRAP and templates: separately ratified reusable migration after PDE proves it.
- BOM and ZTIE: assess live historical rules and migrate independently; never bulk overwrite.

## Approval
No repository permissions, checker thresholds, requirements, status, validation records, or operating method are changed by this proposal alone. Human ratification must be captured by independently verifiable approval event, not an AI-inserted marker.
