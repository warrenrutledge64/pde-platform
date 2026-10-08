# Operations — the Builder's operator instructions

> Operator execution surface authored by the **Designer / Builder seat (Kiro)**
> (`../../governance/AGENTS.md` §2.2) — how to *produce raw evidence*, **NOT** the
> acceptance criteria (§4.1). The four **Moderator** gates
> (`../../governance/MODERATOR_PROTOCOL.md`) are wired into the steps; a red gate is a
> hard stop. First Story operations authored on the Troikauge split architecture (G-4),
> replacing the monolithic PROMPT.

---

## Story 3.3 — Approve the Sandbox gate + promote to `Pipeline-Sandbox` · LIVE operations

### Prerequisites & Environment assumptions

- **Target(s):** Pipeline-Hub `641628980935` (orchestrates / approve here); Pipeline-Sandbox
  `586917955591` (the promotion target — verify the live artifact here). Region `us-east-1`.
  Trust `aws sts get-caller-identity`, never a banner label.
- **Zero-touch (never a target):** any `pde-*` (ZTIE) stack; management `467866449172`;
  Forensics `360999005254`; Pipeline-Prod `466494951534` (Story 3.4, not here).
- **Checkout:** a fresh clone of `warrenrutledge64/pde-platform` on `feature/story-3.3`,
  HEAD == `origin/feature/story-3.3` (the deploy/freshness guard enforces this).
- **Secrets/params required (REAL values, not placeholders):** `/pdlv/promotion/external-id`
  and `/pdlv/promotion/repo-token` SecureStrings in the Hub (already set from 3.2); the
  Sandbox member role (`pde-member-execution-sandbox`) must trust `pdlv-hub-orchestrator`
  with the same ExternalId.
- **Tooling:** `aws` CLI, `scripts/deploy_story_3_2.sh`-lineage deploy (extended for the
  `sandbox` phase), `scripts/preflight_story_3_2.py` (`--scope hub` / `--scope sandbox`).

### STEP 0 — Pre-Execution Gate · launch pad + secrets *(Moderator: Pre-Execution)*

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935
cd ~ && rm -rf pde-platform
git clone "https://github.com/warrenrutledge64/pde-platform.git" && cd pde-platform
git fetch origin && git checkout feature/story-3.3 && git reset --hard origin/feature/story-3.3
git rev-parse HEAD   # record; MUST equal origin/feature/story-3.3
# confirm both /pdlv/ SecureStrings still resolve (set in Story 3.2):
aws ssm get-parameter --name /pdlv/promotion/external-id --query Parameter.Type --output text  # SecureString
aws ssm get-parameter --name /pdlv/promotion/repo-token  --query Parameter.Type --output text  # SecureString
```

- **Verify (Pre-Execution Gate):** identity == `641628980935`; HEAD == `origin/feature/story-3.3`;
  both secrets resolve (not placeholders). STOP on any mismatch — fail-closed.

### STEP 1 — Deploy/refresh the Sandbox member trust FROM THE BRANCH *(Moderator: Deployment)*

```bash
# Target: Pipeline-Sandbox 586917955591 (us-east-1)  <-- SWITCH ACCOUNT
aws sts get-caller-identity --query Account --output text   # MUST print 586917955591
# redeploy pde-member-execution-sandbox from the branch (trust -> pdlv-hub-orchestrator + ExternalId)
# then VERIFY the live role carries the branch marker, not a stale version.
```

- **Verify (Deployment Gate):** the live `pde-member-execution-sandbox` role trusts
  `pdlv-hub-orchestrator` (NOT a raw `AROA…`/legacy principal), its `sts:ExternalId` is the
  real shared secret (no `<placeholder>`), and its CFN/DynamoDB grant is `pdlv-*`-scoped —
  read off the live role, never the deploy line. No dead/rolled-back `pdlv-` stack remains.

### STEP 2 — Preflight the Sandbox baseline *(Moderator: Preflight)*

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1), with Sandbox read
python3 scripts/preflight_story_3_2.py --scope hub       # MUST print PASS
# Sandbox-scoped baseline (from a Sandbox shell or --sandbox-profile):
python3 scripts/preflight_story_3_2.py --scope sandbox   # MUST print PASS
```

- **Verify (Preflight Gate):** both scopes print `PASS` (live infra matches the baseline,
  right accounts). A FAIL = branch not deployed → go back to STEP 1. An env error ≠ a result.

### STEP 3 — Approve the gate + promote, then capture *(Moderator: Live Result)*

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
# Approve the waiting AwaitSandboxApproval task (send the SNS task-token success callback),
# let the execution resume + run the two-hop deploy into Sandbox, then capture ALL raw output:
#   aws stepfunctions send-task-success --task-token "$TOKEN" --task-output '{"approved":true}'
#   aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --query status
# Then from Pipeline-Sandbox 586917955591:
aws sts get-caller-identity --query Account --output text   # MUST print 586917955591
aws cloudformation describe-stacks --stack-name pdlv-golden-path-artifact \
  --query "Stacks[0].{Status:StackStatus,Tags:Tags}" --output json   # expect CREATE_COMPLETE + Project=PDE
aws dynamodb describe-table --table-name pdlv-golden-path-artifact \
  --query "Table.{Status:TableStatus,Billing:BillingModeSummary.BillingMode}" --output json  # ACTIVE / PAY_PER_REQUEST
```

- **Verify (Live Result Gate):** the raw output is from the proven target (HEAD-pinned,
  Sandbox `586917955591`), complete, and shows the artifact live in Sandbox + the execution
  now holding at `AwaitProdApproval`. Hand it **raw** to the independent Validator — the
  operator does not judge.

### Backout

- **Revert this run:** `aws cloudformation delete-stack --stack-name pdlv-golden-path-artifact`
  from Pipeline-Sandbox `586917955591` (one empty, free DynamoDB table — minimal blast radius);
  the pipeline execution can be stopped/aborted. The Hub control-plane stacks are additive —
  revert by redeploying the `story-3.2-validated` (@ `30e72f3`) templates if a Hub defect is found.
- **Scope guard:** only `pdlv-` + the Sandbox member role; never a `pde-*`/ZTIE/management/
  Forensics/Prod resource. Last good restore point: `story-3.2-validated` (@ `30e72f3`).
