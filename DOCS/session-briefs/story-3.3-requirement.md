# Requirement — the Planner's story output

> Authored by the **Planner / Validator seat (Gemini)** acting *as Planner*
> (`../../governance/AGENTS.md` §2.1 / §3). States *what* and *why* — it is **NOT** a
> Definition of Done or a pass/fail rubric (§4.1 barrier); the independent Validator
> authors the DoD blind from this + the raw change. First Story authored on the
> Troikauge split requirement/operations architecture (G-4), replacing the monolithic
> PROMPT.

---

## Story 3.3 — Validate the Dev deployment, approve the gate, promote to `Pipeline-Sandbox`

### Objective

With Story 3.2 proven (the Golden-Path artifact deployed cross-account into Pipeline-Dev
`946509368326` and the `pdlv-promotion-pipeline` execution holding at `AwaitSandboxApproval`),
Story 3.3 exercises the **human approval + promotion** leg of the pipeline: approve the
waiting Sandbox gate so the pipeline resumes, orchestrates the same two-hop deploy into
**Pipeline-Sandbox `586917955591`**, and stands the artifact up there. This proves the
promotion path (approve → resume → cross-account deploy to the next environment) works
end-to-end, not just the first hop — the capability the Golden Path exists to demonstrate.

### Acceptance Criteria

> Objective, binary facts a skeptic can confirm from the real system — inputs the
> Validator derives its DoD from, not the DoD itself.

- The waiting execution's `AwaitSandboxApproval` task is resolved by a **human approval**
  action (the SNS task-token callback succeeds; the execution leaves the pause state).
- After approval, the execution runs the Sandbox deploy and reaches `CREATE_COMPLETE`
  for stack `pdlv-golden-path-artifact` in **Pipeline-Sandbox `586917955591`**.
- The live `pdlv-golden-path-artifact` DynamoDB table exists in Sandbox, is `ACTIVE`,
  `PAY_PER_REQUEST`, and `Project=PDE`-tagged.
- The execution then holds at the **next** pause (`AwaitProdApproval`) via its SNS task
  token — Prod is NOT deployed (that is Story 3.4).
- No `pde-*` (ZTIE) resource, the management account `467866449172`, or Forensics
  `360999005254` is touched (strictly additive, ZTIE-safe).

### Scope

- **In:** approve the Sandbox gate on the live Story-3.2 execution (or a fresh execution);
  the two-hop promotion deploy into Pipeline-Sandbox; verify the live Sandbox artifact.
- **Out:** the Prod approval + deploy (Story 3.4); any change to the artifact template
  (frozen from 3.1) or the deploy engine (frozen from 3.2) unless a real defect forces
  fix-then-validate-once; the management account (zero-touch).

### Dependencies & Validation Rationale

- **Depends on:** Story 3.2 ✅ (sealed PASS Attempt 11, `story-3.2-validated` @ `30e72f3`).
- **Unblocks:** Story 3.4 (Prod approval + deploy; closes Phase 3).
- **Validation rationale:** a live `describe-stacks`/`describe-table` in Sandbox after a
  real human approval is the skeptical proof the promotion leg works — not a green
  execution line. It also re-exercises the two-hop cross-account assume into a *second*
  member account, confirming the trust fabric generalizes beyond Dev.
- **Compliance mapping (candidate — pending ratification):** none new (reuses the RD-006
  orchestrate-and-pull + RD-011 two-hop decisions already recorded).
