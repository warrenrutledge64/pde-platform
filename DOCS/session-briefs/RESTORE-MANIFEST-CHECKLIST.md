# Restore-Point State-Manifest Capture — Operator Checklist (OD-010)

> **Purpose.** A restore point is **code + state as one unit** (see
> [`governance/RESTORE.md`](../../governance/RESTORE.md)). The git **code** half of
> `restore/phase-1-green` and `restore/phase-2-green` is cut + pushed and recorded in
> [`BOM.md`](../../governance/BOM.md) §4 — this checklist captures the paired **state
> manifest** half: a READ-ONLY projection of the deployed AWS reality at that baseline.
> Running it clears **OD-010**.
>
> **This is an OPERATOR step — it runs live in Hub CloudShell with cross-account read.**
> It is **strictly read-only**: it only `describe`/`get`/`list`s; it never creates,
> updates, or deletes anything. It handles the empty/clean case gracefully (a missing
> resource yields a null/empty field, not an error).
>
> **Target:** Pipeline-Hub `641628980935` (us-east-1). Members: Dev `946509368326`,
> Sandbox `586917955591`, Prod `466494951534`. Management `467866449172` is **zero-touch**
> and is NOT read here. Pipeline-Forensics `360999005254` is **ZTIE's**, never touched.

---

## What the manifest captures (the restore-relevant projection — RESTORE.md)

Identity + desired-state fields only (NOT volatile metadata like `StackId`/
`LastUpdatedTime`/`StackStatus`, which change on any redeploy and would flag false drift):

- **CloudFormation stacks** (Hub): per `pdlv-` stack — name, `template_sha256`, parameters,
  stack-level tags. Phase 2: `pdlv-codebuild`, `pdlv-promotion-pipeline-stack`.
- **Control plane** (Hub): Step Functions state-machine name + **definition SHA** for
  `pdlv-promotion-pipeline` and `pdlv-gate-probe`; CodeBuild project names
  (`pdlv-lint`, `pdlv-deploy`).
- **Cross-account IAM roles**: per account — role name, trust policy document, attached
  least-privilege policy documents. Hub: `pdlv-promotion-pipeline-role`,
  `pdlv-gate-probe-role`, `pdlv-codebuild-service-role`. Members (Phase-1 projection):
  `pde-member-execution-<env>` in Dev/Sandbox/Prod.

> **Governance commit pin:** also record the current governance-doc commit
> (`git rev-parse HEAD`) in the manifest, so code + state + governance restore as one unit.

---

## STEP 0 — Launch pad + confirm Hub identity

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
cd ~/pde-platform
git fetch origin && git checkout main && git reset --hard origin/main
aws sts get-caller-identity --query Account --output text   # MUST print 641628980935
mkdir -p governance/restore-manifests
GOV_SHA=$(git rev-parse HEAD); echo "governance commit: $GOV_SHA"
TS=$(date -u +%Y%m%dT%H%M%SZ); echo "timestamp: $TS"
```

## STEP 1 — Capture the HUB projection (read-only)

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1)
MANIFEST="governance/restore-manifests/manifest-${TS}-hub.json"

# CFN stacks: name + template_sha256 + params + tags (desired-state only)
cfn_stack () {
  local S="$1"
  local TPL PARAMS TAGS SHA
  TPL=$(aws cloudformation get-template --stack-name "$S" --template-stage Processed \
        --query TemplateBody --output json 2>/dev/null || echo 'null')
  SHA=$(printf '%s' "$TPL" | sha256sum | cut -d' ' -f1)
  PARAMS=$(aws cloudformation describe-stacks --stack-name "$S" \
            --query "Stacks[0].Parameters" --output json 2>/dev/null || echo 'null')
  TAGS=$(aws cloudformation describe-stacks --stack-name "$S" \
          --query "Stacks[0].Tags" --output json 2>/dev/null || echo 'null')
  printf '{"stack":"%s","template_sha256":"%s","parameters":%s,"tags":%s}' \
         "$S" "$SHA" "$PARAMS" "$TAGS"
}

# State-machine definition SHA (desired-state) for each pdlv- SM
sm_def_sha () {
  local NAME="$1" ARN DEF SHA
  ARN=$(aws stepfunctions list-state-machines \
         --query "stateMachines[?name=='$NAME'].stateMachineArn" --output text)
  [ -z "$ARN" ] && { printf '{"name":"%s","arn":null,"definition_sha256":null}' "$NAME"; return; }
  DEF=$(aws stepfunctions describe-state-machine --state-machine-arn "$ARN" \
         --query definition --output text)
  SHA=$(printf '%s' "$DEF" | sha256sum | cut -d' ' -f1)
  printf '{"name":"%s","arn":"%s","definition_sha256":"%s"}' "$NAME" "$ARN" "$SHA"
}

# IAM role projection: trust policy + attached managed-policy documents
iam_role () {
  local RN="$1" TRUST POLS
  TRUST=$(aws iam get-role --role-name "$RN" \
           --query "Role.AssumeRolePolicyDocument" --output json 2>/dev/null || echo 'null')
  POLS='[]'
  for PA in $(aws iam list-attached-role-policies --role-name "$RN" \
               --query "AttachedPolicies[].PolicyArn" --output text 2>/dev/null); do
    VID=$(aws iam get-policy --policy-arn "$PA" --query "Policy.DefaultVersionId" --output text)
    DOC=$(aws iam get-policy-version --policy-arn "$PA" --version-id "$VID" \
           --query "PolicyVersion.Document" --output json)
    POLS=$(printf '%s' "$POLS" | python3 -c "import sys,json;a=json.load(sys.stdin);a.append({'arn':'$PA','document':json.load(open('/dev/stdin'))});print(json.dumps(a))" <<<"$DOC" 2>/dev/null || echo "$POLS")
  done
  printf '{"role":"%s","trust":%s,"attached_policies":%s}' "$RN" "$TRUST" "$POLS"
}

{
  echo '{'
  echo "  \"captured_utc\": \"${TS}\","
  echo "  \"account\": \"641628980935\",\"region\":\"us-east-1\","
  echo "  \"governance_commit\": \"${GOV_SHA}\","
  echo '  "cfn_stacks": ['
  echo "    $(cfn_stack pdlv-codebuild),"
  echo "    $(cfn_stack pdlv-promotion-pipeline-stack)"
  echo '  ],'
  echo '  "state_machines": ['
  echo "    $(sm_def_sha pdlv-promotion-pipeline),"
  echo "    $(sm_def_sha pdlv-gate-probe)"
  echo '  ],'
  echo '  "codebuild_projects": '"$(aws codebuild list-projects --query "projects[?contains(@,'pdlv-')]" --output json)"','
  echo '  "iam_roles": ['
  echo "    $(iam_role pdlv-promotion-pipeline-role),"
  echo "    $(iam_role pdlv-gate-probe-role),"
  echo "    $(iam_role pdlv-codebuild-service-role)"
  echo '  ]'
  echo '}'
} > "$MANIFEST"

python3 -m json.tool "$MANIFEST" >/dev/null && echo "VALID JSON: $MANIFEST" || echo "INVALID JSON — review $MANIFEST"
```

## STEP 2 — Capture the MEMBER role projections (Phase-1 half; cross-account read)

> If your gate uses `sts:AssumeRole` into the members (VD-3b / `pde-hub-orchestrator`),
> assume each member read-only and run `iam_role pde-member-execution-<env>` there; else
> run from a read-capable principal in each member account. Record each into a
> `manifest-${TS}-<env>.json`. (Phase-1 member roles are unchanged, so this doubles as the
> Phase-1 manifest.)

```bash
# Example per member (read-only): confirm identity, then capture the role projection.
# aws sts get-caller-identity --query Account --output text   # expect 946509368326 (Dev), etc.
# iam_role pde-member-execution-dev > governance/restore-manifests/manifest-${TS}-dev.json
```

## STEP 3 — Commit + record the manifest path in BOM §4

```bash
# Target: Pipeline-Hub 641628980935 (us-east-1) — but this is a git/doc step
git add governance/restore-manifests/manifest-*.json
# Edit governance/BOM.md §4: replace the "to be captured" note in the
#   restore/phase-2-green row (and restore/phase-1-green row) with the committed
#   manifest path(s): governance/restore-manifests/manifest-<TS>-hub.json (+ -<env>.json)
git add governance/BOM.md
git commit -m "OD-010: capture restore-point state manifest(s) for Phase 1/2; record paths in BOM §4"
python3 scripts/check_docs.py          # must PASS
# open a PR (never push to main directly), merge, then OD-010 flips PAID in the RUNBOOK.
```

## Guardrails

- **READ-ONLY.** Only `describe`/`get`/`list`/`sts get-caller-identity`. Never
  create/update/delete. If any command would mutate, STOP.
- **Scope to `pdlv-` (Hub) + `pde-member-execution-<env>` (members).** Never read or
  touch ZTIE's `pde-*` Hub stacks, Pipeline-Forensics, or the management account.
- **Desired-state only.** Do not record `StackStatus`/`StackId`/`LastUpdatedTime` — they
  change on any redeploy and would flag false drift on a later `verify`.
- **Empty/clean is valid.** A missing resource yields `null`/`[]`, not an error.
- **Verify later:** a coordinated restore (RESTORE.md) re-runs this capture and diffs ONLY
  this projection against the manifest; a volatile-metadata diff is not a restore failure.
