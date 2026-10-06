# CI OIDC Deploy — one-time setup for the Story 3.2 live-deploy workflow

> **Purpose.** `.github/workflows/deploy-story-3.2.yml` deploys Story 3.2 cross-account via
> **GitHub OIDC** (no long-lived AWS keys). It is MANUAL-ONLY and does NOT validate or flip
> status — the independent validator still authors the DoD and seals the verdict from the raw
> run logs, and the executor records it by hand (the split-brain + write-only-scribe covenant
> is untouched). This note is the one-time stand-up the **stakeholder** performs in AWS +
> GitHub. **Nothing here invents an ARN** — you create the roles and paste their real ARNs
> into the two repo variables; until you do, the workflow self-aborts with a clear message.
>
> **Why this exists.** Seven straight Story-3.2 attempts failed on operator CloudShell paste
> mistakes (wrong directory, wrong account, skipped preflight, input-collision). CI removes the
> human from the mechanical deploy paste — while ADDING a logged, approved human gate on each
> cross-account deploy via protected Environments (below). The human-in-the-loop GOVERNANCE
> guardrail (validator authors the DoD + seals; stakeholder approves) is unchanged.

Region for all of the below: **us-east-1**. Accounts: Hub **641628980935**, Dev **946509368326**.

---

## What the workflow expects (exact names — must match)

| Kind | Name | Where you set it | Value |
|------|------|------------------|-------|
| Repo **variable** | `PDE_HUB_DEPLOY_ROLE_ARN` | GitHub → Settings → Secrets and variables → Actions → **Variables** | ARN of the Hub OIDC deploy role (step 2) |
| Repo **variable** | `PDE_DEV_DEPLOY_ROLE_ARN` | same (Variables) | ARN of the Dev OIDC deploy role (step 2) |
| Repo **secret** | `PDE_EXTERNAL_ID` | GitHub → … → **Secrets** | the shared member-trust ExternalId (the exact value baked into `pde-member-execution-<env>`'s `sts:ExternalId` condition at `restore/phase-1-green`) |
| **Environment** | `pipeline-dev` | GitHub → Settings → **Environments** | protected, required reviewer = you (step 4) |
| **Environment** | `pipeline-hub` | same | protected, required reviewer = you (step 4) |

Also pre-existing (set out-of-band in the Hub, used by the pipeline at runtime, NOT by this
workflow): the Hub SSM SecureStrings `/pdlv/promotion/external-id` and `/pdlv/promotion/repo-token`.

---

## Step 1 — Create the GitHub OIDC identity provider in BOTH accounts

In Hub `641628980935` AND Dev `946509368326`, create an IAM OIDC identity provider (once per
account) if one does not already exist:

- **Provider URL:** `https://token.actions.githubusercontent.com`
- **Audience:** `sts.amazonaws.com`

(Console: IAM → Identity providers → Add provider → OpenID Connect. Or `aws iam
create-open-id-connect-provider`.)

---

## Step 2 — Create the two OIDC deploy roles (one per account)

Each role trusts GitHub's OIDC provider, scoped to THIS repo and the Story-3.2 branch (so a
fork or another branch cannot assume it). Trust policy for BOTH roles (substitute `<ACCOUNT_ID>`
with that role's account):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:warrenrutledge64/pde-platform:ref:refs/heads/feature/story-3.2"
      }
    }
  }]
}
```

> Tighten `:sub` further to an environment if you prefer:
> `repo:warrenrutledge64/pde-platform:environment:pipeline-hub` (and `:pipeline-dev`) — that
> binds each role to its GitHub Environment, so the role can ONLY be assumed by a job running
> in the approved environment. Recommended once the environments (step 4) exist.

### 2a — Dev deploy role (in Dev `946509368326`) → its ARN goes in `PDE_DEV_DEPLOY_ROLE_ARN`
Least-privilege permissions — it only deploys `infra/member-execution-role.yaml` as the
`pde-trust-fabric` stack (which creates the `pde-member-execution-dev` role + its managed
policy) and reads back to verify:
- `cloudformation:CreateStack/UpdateStack/DescribeStacks/DescribeStackEvents/GetTemplate/CreateChangeSet/DescribeChangeSet/ExecuteChangeSet/DeleteChangeSet/TagResource` on `arn:aws:cloudformation:us-east-1:946509368326:stack/pde-trust-fabric/*`
- `iam:CreateRole/DeleteRole/GetRole/TagRole/UntagRole/CreatePolicy/DeletePolicy/GetPolicy/GetPolicyVersion/CreatePolicyVersion/DeletePolicyVersion/AttachRolePolicy/DetachRolePolicy/ListAttachedRolePolicies/ListRoleTags/PutRolePolicy/DeleteRolePolicy` scoped to `role/pde-member-execution-*` and `policy/pde-member-execution-permissions-*`
- `cloudformation:ValidateTemplate`, `sts:GetCallerIdentity` (unscoped reads)
- NO wildcard admin, NO PassRole beyond what CFN needs for the member role.

### 2b — Hub deploy role (in Hub `641628980935`) → its ARN goes in `PDE_HUB_DEPLOY_ROLE_ARN`
It deploys the three Hub stacks (`pdlv-hub-orchestrator`, `pdlv-codebuild`,
`pdlv-promotion-pipeline-stack`), reconciles the `pdlv-` namespace, and the preflight reads
Hub + Dev. Least-privilege:
- `cloudformation:*` (the create/update/delete/describe/changeset/list set, incl.
  `ListStacks`/`DeleteStack`) scoped to `arn:aws:cloudformation:us-east-1:641628980935:stack/pdlv-*/*` — **`pdlv-` only; never `pde-*` (ZTIE's) and never management/Forensics**
- `iam:*` role/policy lifecycle scoped to `role/pdlv-*` + `policy/pdlv-*` (the orchestrator,
  codebuild service role, SFN exec role + their managed policies all `pdlv-`-named), plus
  `iam:PassRole` on those `pdlv-*` roles for the services that use them
- `codebuild:CreateProject/UpdateProject/DeleteProject/BatchGetProjects` on `project/pdlv-*`
- `states:CreateStateMachine/UpdateStateMachine/DeleteStateMachine/DescribeStateMachine/TagResource` on `stateMachine:pdlv-*`
- `sns:CreateTopic/DeleteTopic/GetTopicAttributes/SetTopicAttributes/TagResource` on `pdlv-promotion-approval`
- `logs:CreateLogGroup/DeleteLogGroup/PutRetentionPolicy/TagLogGroup/DescribeLogGroups` on the `pdlv-` vended log groups
- **Preflight Dev-read:** EITHER grant this role `sts:AssumeRole` on a dedicated Dev-read role
  in `946509368326` (recommended — then pass `--dev-profile`/configure the role for the
  preflight), OR give the preflight a separate Dev-read credential. The preflight only needs
  READ on Dev: `iam:GetRole/ListRoleTags/ListAttachedRolePolicies/GetPolicy/GetPolicyVersion`
  on `pde-member-execution-dev`, `cloudformation:DescribeStacks`, `sts:GetCallerIdentity`.
- `ssm:GetParameter` + `kms:Decrypt` (via SSM) on the two `/pdlv/promotion/*` params if the
  preflight/deploy needs them; `sts:GetCallerIdentity` unscoped.

> Keep BOTH roles `pdlv-`/`pde-member-*`-scoped. Neither may touch a `pde-*` ZTIE stack,
> the management account `467866449172`, or Pipeline-Forensics `360999005254`.

---

## Step 3 — Set the repo variables + secret

GitHub → repo **Settings → Secrets and variables → Actions**:
- **Variables** tab → New variable → `PDE_HUB_DEPLOY_ROLE_ARN` = the step-2b role ARN.
- **Variables** tab → New variable → `PDE_DEV_DEPLOY_ROLE_ARN` = the step-2a role ARN.
- **Secrets** tab → New secret → `PDE_EXTERNAL_ID` = the shared member-trust ExternalId.

(The workflow's `preconditions` job fails loudly if either variable is empty — so a
mis-typed/absent ARN cannot produce a silent half-deploy.)

---

## Step 4 — Protect the Environments (THIS is the human-in-the-loop deploy gate)

GitHub → repo **Settings → Environments** → create `pipeline-dev` and `pipeline-hub`. For each:
- **Required reviewers** → add yourself (and/or the accountable approver).
- Optionally restrict deployment branches to `feature/story-3.2`.

Effect: when the workflow runs, GitHub **pauses before the Dev deploy job and again before the
Hub deploy job**, each waiting for a named human to click **Approve** — a logged, auditable
change-approval gate on every cross-account deploy. This is the human-in-the-loop guardrail,
stronger and more auditable than a human remembering to paste commands correctly.

---

## Step 5 — Run it (the deliberate, approved deploy)

1. GitHub → **Actions** → "PDE Story 3.2 — live deploy" → **Run workflow**.
2. Branch: `feature/story-3.2`. Type the confirmation input exactly: `deploy-story-3.2`.
3. Approve the `pipeline-dev` gate when prompted → the Dev member role deploys + self-verifies.
4. Approve the `pipeline-hub` gate when prompted → the Hub stacks deploy, the `pdlv-` namespace
   is reconciled, and the preflight runs. **The Hub job FAILS unless the preflight prints
   PASS** — so a green run is proof the Story-3.2 baseline is live.
5. Hand the run's raw logs to the INDEPENDENT validator (who authors the DoD + seals the
   verdict). The executor records the sealed verdict; **status flips to ✅ only on a sealed
   PASS**. CI never validates and never flips status.

---

## What CI does NOT change (covenant intact)
- It does **not** author acceptance criteria or judge the deliverable — the independent
  validator does, from the raw logs.
- It does **not** flip Story 3.2's status — the executor records the sealed verdict by hand.
- It does **not** promote the pipeline beyond the Dev deploy — Sandbox/Prod are Stories 3.3/3.4.
- Management `467866449172` and Pipeline-Forensics `360999005254` are never touched.
