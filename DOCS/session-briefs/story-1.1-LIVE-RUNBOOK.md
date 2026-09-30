# Story 1.1 — LIVE Deploy & Validation Runbook (operator copy-paste)

> **Account context for EVERY block below:**
> **AWS Organization MANAGEMENT / root account `467866449172`.**
> This is the *only* account Story 1.1 touches. Run `aws sts get-caller-identity`
> before each block and confirm `"Account": "467866449172"` — a banner comment does
> not change your credentials.
>
> **Region:** pick the home region for the trail (multi-region trail still has a
> home region for the delivery). This runbook uses `us-east-1`; substitute if you
> deploy elsewhere and record the choice in `governance/BOM.md`.
>
> **Artifact:** `infra/cloudtrail-org-baseline.yaml` (offline-proven — 28 invariants
> pass via `python3 infra/validate_template.py`). Story stays 🟡 until the gate
> below returns a recorded pass.

---

## STEP 0 — Preconditions (one-time, in the management account)

```bash
# CONTEXT: mgmt/root 467866449172
aws sts get-caller-identity --query Account --output text   # expect 467866449172

# Enable AWS Organizations trusted access for CloudTrail (required for an org trail):
aws organizations enable-aws-service-access \
  --service-principal cloudtrail.amazonaws.com

# Capture your Organization ID (o-xxxxxxxxxx) — needed as a stack parameter:
aws organizations describe-organization --query 'Organization.Id' --output text
```

> If `enable-aws-service-access` errors with AccessDenied, you are not in the
> management account (or not a delegated administrator). Fix the context before
> continuing — do NOT try to work around it.

## STEP 1 — Offline proof (optional re-run; already green in the repo)

```bash
python3 infra/validate_template.py    # expect: PASS — all 28 Story 1.1 invariants hold
```

> The full cfn-lint / cfn-guard / Checkov / Bandit static bar (Universal Criterion 3)
> runs here in CloudShell / CI, where PyPI is reachable (the build sandbox has it
> blocked). Suggested:
> ```bash
> pip install cfn-lint checkov
> cfn-lint infra/cloudtrail-org-baseline.yaml
> checkov -f infra/cloudtrail-org-baseline.yaml
> ```
> Resolve any findings before deploy.

## STEP 2 — Deploy the trail stack (management account only)

```bash
# CONTEXT: mgmt/root 467866449172, region us-east-1
ORG_ID=$(aws organizations describe-organization --query 'Organization.Id' --output text)
echo "Org: $ORG_ID"

aws cloudformation deploy \
  --region us-east-1 \
  --stack-name pde-org-cloudtrail-baseline \
  --template-file infra/cloudtrail-org-baseline.yaml \
  --parameter-overrides \
      OrganizationId="$ORG_ID" \
      ManagementAccountId=467866449172 \
      LogBucketName=pde-org-cloudtrail-logs-467866449172 \
      TrailName=pde-org-trail \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Project=PDE Story=1.1 Component=governance-cloudtrail
```

> `LogBucketName` must be globally unique. If it collides, pass a different name
> (keep the `pde-` prefix) and record it.

## STEP 3 — VALIDATE (the Phase 1 gate, CloudTrail half)

> The Phase 1 end-of-phase gate has two halves: this CloudTrail half (Story 1.1)
> and the cross-account AssumeRole half (Story 1.2). Story 1.1's own DoD is the
> CloudTrail half below.

```bash
# CONTEXT: mgmt/root 467866449172, region us-east-1

# 3a. Trail is an active, org-wide, multi-region, log-file-validated trail:
aws cloudtrail describe-trails --trail-name-list pde-org-trail \
  --query 'trailList[0].{Org:IsOrganizationTrail,MultiRegion:IsMultiRegionTrail,LogValidation:LogFileValidationEnabled,KmsKeyId:KmsKeyId,Bucket:S3BucketName}'
# EXPECT: Org=true, MultiRegion=true, LogValidation=true, KmsKeyId set, Bucket=pde-org-cloudtrail-logs-...

# 3b. Trail is actively logging:
aws cloudtrail get-trail-status --name pde-org-trail \
  --query '{IsLogging:IsLogging,LatestDeliveryTime:LatestDeliveryTime,LatestDeliveryError:LatestDeliveryError}'
# EXPECT: IsLogging=true; after a few minutes LatestDeliveryTime is populated and LatestDeliveryError is empty.

# 3c. Log files are LANDING in the new bucket for the Pipeline-* (member) accounts.
#     Org-trail objects are keyed AWSLogs/<orgId>/<accountId>/CloudTrail/<region>/...
#     Give it 5-15 min after deploy, then list per Pipeline account id:
aws s3 ls "s3://pde-org-cloudtrail-logs-467866449172/AWSLogs/$ORG_ID/" --recursive \
  | grep CloudTrail | head -20
# EXPECT: objects appearing under one or more member-account ids (the Pipeline-* accounts).
```

**PASS criteria (all must hold):**
1. `describe-trails` → `IsOrganizationTrail=true`, `IsMultiRegionTrail=true`, `LogFileValidationEnabled=true`, KMS key + bucket set.
2. `get-trail-status` → `IsLogging=true`, a populated `LatestDeliveryTime`, empty `LatestDeliveryError`.
3. `s3 ls` → CloudTrail log objects landing under the org-id prefix for the `Pipeline-*` accounts.

Record the result in `governance/RUNBOOK.md` Story 1.1:
`pass — org trail active (org/multi-region/log-validation) + logs landing for Pipeline-* accts, <date>, confirmed by <who>`.

## STEP 4 — Zero-Touch-Root check (Universal Criterion 1)

```bash
# CONTEXT: mgmt/root 467866449172
# Confirm this stack is the ONLY PDE footprint in the management account:
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName,'pde-')].StackName"
# EXPECT: exactly ["pde-org-cloudtrail-baseline"] — no other pde-* stacks in root.
```

## Backout / rollback (clean-state, Universal Criterion 4)

The log bucket is `DeletionPolicy: Retain`, so deleting the stack leaves the audit
evidence intact. To fully tear down (deliberate):

```bash
# CONTEXT: mgmt/root 467866449172, region us-east-1
# 1. Delete the stack (removes trail, bucket policy, KMS key [scheduled], alias;
#    the bucket is RETAINED because it holds audit evidence):
aws cloudformation delete-stack --stack-name pde-org-cloudtrail-baseline
aws cloudformation wait stack-delete-complete --stack-name pde-org-cloudtrail-baseline

# 2. Only if you truly want the logs gone — empty ALL versions + delete markers,
#    then delete the retained bucket (there is NO Object Lock, so this succeeds):
BKT=pde-org-cloudtrail-logs-467866449172
aws s3api delete-objects --bucket "$BKT" \
  --delete "$(aws s3api list-object-versions --bucket "$BKT" \
    --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json)"
aws s3api delete-objects --bucket "$BKT" \
  --delete "$(aws s3api list-object-versions --bucket "$BKT" \
    --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' --output json)"
aws s3api delete-bucket --bucket "$BKT"
```

> If a delete-objects call reports a null Objects list, that version class was
> already empty — safe to ignore. The KMS key enters a pending-deletion window
> (7-30 days) rather than deleting immediately; that is expected.

## Watch-items

- **Wrong account** is the #1 failure: `enable-aws-service-access` and the deploy
  MUST run in `467866449172`. Re-run `aws sts get-caller-identity` per block.
- **Delivery latency:** first log objects can take 5-15 minutes; an empty `s3 ls`
  immediately after deploy is not a failure — wait and re-check.
- **`LatestDeliveryError`** populated (e.g. `KMS.AccessDenied` or `AccessDenied`)
  means the KMS key policy or bucket policy is rejecting CloudTrail — capture the
  exact error string; it names which policy to fix. Keep Story 1.1 🟡 and fix.
- **Do NOT** add any other resource to the management account.
