# Story 3.2 · GATE 1 — Raw Environment-Baseline Evidence

> **Purpose:** this is the RAW evidence the operator captured live for the BLIND Gate-1
> validator to judge GO / NO-GO on whether the live AWS environment IS the Story-3.2 baseline.
> It is NOT a verdict and carries NO builder judgment / DoD. The validator authors its own
> environment-baseline Definition of Done (per `story-3.2-gate1-VALIDATOR-HANDOVER.md`) and
> judges the RAW reads below itself — it must NOT trust the preflight PASS lines as the ruling.
>
> **Target commit under test:** `feature/story-3.2` @ `32e6480`
> **Captured:** 2026-10-07 (live, by the operator in per-account CloudShell sessions)
> **Accounts:** Hub `641628980935` · Dev `946509368326` (each proven by `aws sts get-caller-identity`)
>
> Story 3.2 remains 🟡 / VD-9 OPEN regardless of the Gate-1 outcome — Gate 1 is a precondition
> checkpoint, not the story's validation.

---

## A. Preflight PASS lines (corroborating evidence — NOT the ruling)

Per-account preflight (`scripts/preflight_story_3_2.py --scope hub|dev`); the two scoped PASSes
together are the full baseline.

### A.1 — Hub scope (run in Hub 641628980935)
```
  [ok  ] orchestrator trust names ONLY pdlv-codebuild-service-role
  [ok  ] orchestrator has a PermissionsBoundary
  [ok  ] orchestrator holds ONLY sts:AssumeRole (no local Hub power)
  [ok  ] orchestrator assume targets pde-member-execution-<env> (not pde-cross-account-deployer)
  [ok  ] state-machine definition has NO EXTERNAL_ID (resolved at the edge)

preflight_story_3_2 [hub]: PASS — live Hub infra matches the Story-3.2 baseline; safe to trigger the pipeline + validate.
```

### A.2 — Dev scope (run in Dev 946509368326)
```
  [ok  ] Dev member role tagged Story=3.2 (branch deployed, not the Story=1.1 role)
  [ok  ] Dev member CFN scoped to stack/pdlv-* (not pde-*)
  [ok  ] Dev member grants concrete DynamoDB table-lifecycle on table/pdlv-*
  [ok  ] Dev member trust ExternalId is a real value (not a <placeholder>)

preflight_story_3_2 [dev]: PASS — live Dev infra matches the Story-3.2 baseline; safe to trigger the pipeline + validate.
```

---

## B. Raw AWS reads (what the validator judges)

### B.1 — Hub 641628980935

**Account proof**
```json
{
    "UserId": "AROAZKZARI3DQIAQ4OJJ2:warren",
    "Account": "641628980935",
    "Arn": "arn:aws:sts::641628980935:assumed-role/AWSReservedSSO_AdministratorAccess_288152a9b7a24f52/warren"
}
```

**`pdlv-hub-orchestrator` trust + permissions boundary**
```json
{
    "Trust": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TrustOnlyTheCodeBuildDeployServiceRole",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::641628980935:role/pdlv-codebuild-service-role"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    },
    "Boundary": {
        "PermissionsBoundaryType": "Policy",
        "PermissionsBoundaryArn": "arn:aws:iam::641628980935:policy/pdlv-hub-orchestrator-boundary"
    }
}
```

**`pdlv-hub-orchestrator` attached policies**
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "pdlv-hub-orchestrator-assume-members",
            "PolicyArn": "arn:aws:iam::641628980935:policy/pdlv-hub-orchestrator-assume-members"
        }
    ]
}
```

**`pdlv-hub-orchestrator-assume-members` document (default version v1)**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::946509368326:role/pde-member-execution-dev",
                "arn:aws:iam::586917955591:role/pde-member-execution-sandbox",
                "arn:aws:iam::466494951534:role/pde-member-execution-prod"
            ],
            "Effect": "Allow",
            "Sid": "AssumeSpecificMemberExecutionRolesOnly"
        }
    ]
}
```

**`pdlv-promotion-pipeline` state-machine definition**
```json
{
  "Comment": "PDE promotion pipeline: Dev -> (approve) -> Sandbox -> (approve) -> Prod. Each deploy starts the pdlv-deploy CodeBuild project (.sync); each approval is a native waitForTaskToken pause.",
  "StartAt": "DeployDev",
  "States": {
    "DeployDev": {
      "Type": "Task",
      "Resource": "arn:aws:states:::codebuild:startBuild.sync",
      "Parameters": {
        "ProjectName": "pdlv-deploy",
        "EnvironmentVariablesOverride": [
          { "Name": "TARGET_ENV", "Type": "PLAINTEXT", "Value": "dev" },
          { "Name": "TARGET_ROLE_ARN", "Type": "PLAINTEXT", "Value": "arn:aws:iam::946509368326:role/pde-member-execution-dev" }
        ]
      },
      "Next": "AwaitSandboxApproval"
    },
    "AwaitSandboxApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish.waitForTaskToken",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:641628980935:pdlv-promotion-approval",
        "Message": {
          "stage": "Awaiting Sandbox Approval",
          "promoteTo": "sandbox",
          "taskToken.$": "$$.Task.Token",
          "executionId.$": "$$.Execution.Id"
        }
      },
      "Next": "DeploySandbox"
    },
    "DeploySandbox": {
      "Type": "Task",
      "Resource": "arn:aws:states:::codebuild:startBuild.sync",
      "Parameters": {
        "ProjectName": "pdlv-deploy",
        "EnvironmentVariablesOverride": [
          { "Name": "TARGET_ENV", "Type": "PLAINTEXT", "Value": "sandbox" },
          { "Name": "TARGET_ROLE_ARN", "Type": "PLAINTEXT", "Value": "arn:aws:iam::586917955591:role/pde-member-execution-sandbox" }
        ]
      },
      "Next": "AwaitProdApproval"
    },
    "AwaitProdApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish.waitForTaskToken",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:641628980935:pdlv-promotion-approval",
        "Message": {
          "stage": "Awaiting Prod Approval",
          "promoteTo": "prod",
          "taskToken.$": "$$.Task.Token",
          "executionId.$": "$$.Execution.Id"
        }
      },
      "Next": "DeployProd"
    },
    "DeployProd": {
      "Type": "Task",
      "Resource": "arn:aws:states:::codebuild:startBuild.sync",
      "Parameters": {
        "ProjectName": "pdlv-deploy",
        "EnvironmentVariablesOverride": [
          { "Name": "TARGET_ENV", "Type": "PLAINTEXT", "Value": "prod" },
          { "Name": "TARGET_ROLE_ARN", "Type": "PLAINTEXT", "Value": "arn:aws:iam::466494951534:role/pde-member-execution-prod" }
        ]
      },
      "Next": "PromotionSucceeded"
    },
    "PromotionSucceeded": {
      "Type": "Succeed"
    }
  }
}
```

### B.2 — Dev 946509368326

**Account proof**
```json
{
    "UserId": "AROA5YYC2ZQDCR7ECNMO6:warren",
    "Account": "946509368326",
    "Arn": "arn:aws:sts::946509368326:assumed-role/AWSReservedSSO_AdministratorAccess_b0c3529e45556e9b/warren"
}
```

**`pde-member-execution-dev` tags**
```json
{
    "Tags": [
        { "Key": "Story", "Value": "3.2" },
        { "Key": "Model", "Value": "orchestrate-and-pull" },
        { "Key": "Project", "Value": "PDE" },
        { "Key": "Environment", "Value": "dev" },
        { "Key": "ManagedBy", "Value": "cloudformation" },
        { "Key": "Component", "Value": "trust-fabric" }
    ]
}
```

**`pde-member-execution-dev` trust policy**  _(ExternalId is a real value; the principal is the orchestrator role's unique id)_
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "TrustSpecificHubOrchestratorRole",
            "Effect": "Allow",
            "Principal": {
                "AWS": "AROAZKZARI3DREAID4I27"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "Ce5b9dd5ed6a8db563167546a0f2ec2f"
                }
            }
        }
    ]
}
```

**`pde-member-execution-dev` attached policies**
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "pde-member-execution-permissions-dev",
            "PolicyArn": "arn:aws:iam::946509368326:policy/pde-member-execution-permissions-dev"
        }
    ]
}
```

**`pde-member-execution-permissions-dev` document (default version v1)**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LocalCloudFormationStackOps",
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResources",
                "cloudformation:GetTemplate",
                "cloudformation:ListStackResources",
                "cloudformation:CreateChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:DeleteChangeSet",
                "cloudformation:ValidateTemplate",
                "cloudformation:TagResource",
                "cloudformation:UntagResource"
            ],
            "Resource": "arn:aws:cloudformation:*:946509368326:stack/pdlv-*/*"
        },
        {
            "Sid": "LocalPdlvDynamoDbArtifactOnly",
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DeleteTable",
                "dynamodb:UpdateTable",
                "dynamodb:DescribeTable",
                "dynamodb:DescribeContinuousBackups",
                "dynamodb:DescribeTimeToLive",
                "dynamodb:UpdateContinuousBackups",
                "dynamodb:UpdateTimeToLive",
                "dynamodb:ListTagsOfResource",
                "dynamodb:TagResource",
                "dynamodb:UntagResource"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:946509368326:table/pdlv-*",
                "arn:aws:dynamodb:*:946509368326:table/pdlv-*/index/*"
            ]
        },
        {
            "Sid": "ReadOnlyDescribe",
            "Effect": "Allow",
            "Action": [
                "cloudformation:ListStacks",
                "cloudformation:ListExports",
                "cloudformation:ListImports"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## C. Operator capture notes (facts only — NOT judgment)

These are environment facts for the validator's awareness; they do not pre-judge GO/NO-GO:

- The Hub control plane was stood up via `scripts/deploy_story_3_2.sh hub` (all three canonical
  stacks `pdlv-hub-orchestrator`, `pdlv-codebuild`, `pdlv-promotion-pipeline-stack` reached
  `CREATE_COMPLETE`/`UPDATE_COMPLETE`); the Dev member role via `… dev` (sealed `DEV PHASE: PASS`).
- During stand-up two environment issues from PRIOR attempts were cleared (operator-side, not
  deliverable changes): (1) a `pdlv-promotion-pipeline-stack` stuck in `DELETE_FAILED` because
  `pdlv-gate-probe` had TWO executions RUNNING since 2026-10-02 (stopped; stack delete then
  completed and recreated clean); (2) the `pdlv-hub-orchestrator` trust had a STALE unique id
  (`AROAZKZARI3D3WTSW43MU`) left over from a prior codebuild-role recreate — the orchestrator
  stack was deleted + recreated so the trust re-resolved to the live `pdlv-codebuild-service-role`
  (now shows the full ARN above). The Hub-scope preflight that initially FAILED on this exact axis
  then PASSED — i.e. the preflight correctly caught a real stale-trust defect before any validation.
- `pde-member-execution-dev` trust principal shows the orchestrator role's unique id
  (`AROAZKZARI3DREAID4I27`) rather than an ARN; this is normal IAM behaviour and resolves to the
  live `pdlv-hub-orchestrator` role (the member deploy ran AFTER the orchestrator recreate).
