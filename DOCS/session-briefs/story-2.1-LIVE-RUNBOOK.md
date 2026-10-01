# Story 2.1 — LIVE Validation Runbook (turnkey, STATIC BAR only)

> **Story 2.1 = the two Hub-side CodeBuild projects (RD-003/RD-004/RD-006/RD-009):**
> a **LINT / static-analysis** project (`pdlv-lint`) and a cross-account **DEPLOY**
> project (`pdlv-deploy`), plus a least-privilege CodeBuild **service role**
> (`pdlv-codebuild-service-role`) whose only cross-account power is `sts:AssumeRole`
> into the Story 1.1 member execution roles.
>
> **This is STATIC PROOF only — nothing is deployed.** Story 2.1 is template
> authoring + a static-analysis bar; the live Hub bootstrap deploy is **Story 2.3**.
> No AWS resource is created here. These steps run in **Hub CloudShell
> (641628980935)** / CI purely to lint + scan the template.
>
> **Accounts (reference only — no deploy in 2.1):** Hub `641628980935`; members
> Dev `946509368326`, Sandbox `586917955591`, Prod `466494951534`; management/root
> `467866449172` zero-touch; Pipeline-Forensics `360999005254` is ZTIE's, not PDE.
>
> **Artifact:** `infra/codebuild-projects.yaml` (offline-proven — 32 invariants via
> `python3 infra/validate_codebuild_projects.py`). Story 2.1 stays 🟡 until the
> validator seals a PASS on the static-bar output below.

---

## STEP 0 — Launch pad + get on the right code (Hub CloudShell)

Use the hardened launch pad from Story 1.2
([`story-1.2-LIVE-RUNBOOK.md`](story-1.2-LIVE-RUNBOOK.md) STEP 0 PATH A — the 3-line
named-script path) and confirm `LAUNCH-PAD VERIFY: PASS` BEFORE anything else. Then
get onto this story's branch (the 2.1 files are NOT on `main`):

```bash
aws sts get-caller-identity --query Account --output text   # expect 641628980935
cd ~/pde-platform                                           # the cloned repo
git fetch origin
git checkout feature/story-2.1
git rev-parse --abbrev-ref HEAD                             # expect: feature/story-2.1
git log --oneline -1                                        # pin this SHA as <HEAD-SHA>
ls -1 infra/codebuild-projects.yaml infra/validate_codebuild_projects.py
```

> If the files are absent, STOP — you are on the wrong branch/commit. Do not evaluate
> downstream output from a launch pad on the wrong code (the attempt-2/3 lesson).

## STEP 1 — Offline invariant checker (no network)

```bash
python3 infra/validate_codebuild_projects.py
# expect: validate_codebuild_projects: PASS — all 32 CodeBuild invariants hold
```

## STEP 2 — Static bar (cfn-lint + Checkov; cfn-guard optional)

```bash
pip install --quiet cfn-lint checkov
cfn-lint infra/codebuild-projects.yaml
checkov -f infra/codebuild-projects.yaml --framework cloudformation
# (optional, if you keep a ruleset)
# cfn-guard validate -d infra/codebuild-projects.yaml -r <your-rules>
```

**PASS criteria (the validator authors the final DoD; this is the operator target):**
- `cfn-lint` returns clean (no errors) — the template is well-formed.
- `checkov` reports no failed checks that indicate a real least-privilege / hardening
  regression (triage any informational findings against the DoD).
- The offline checker is `PASS — all 32 invariants hold`.

## STEP 3 — Spot-check the invariants by eye (adversarial)

```bash
# No pde- Hub resource name (only pdlv-); exports are pdlv-*
grep -nE '(Name|RoleName|LogGroupName|ManagedPolicyName):' infra/codebuild-projects.yaml
grep -n 'Export:' -A1 infra/codebuild-projects.yaml

# Least privilege — these should return NOTHING (prove absence):
grep -nE 'AdministratorAccess|PowerUserAccess' infra/codebuild-projects.yaml || echo "none — good"
grep -nE 'Action:\s*["'\'']\*["'\'']' infra/codebuild-projects.yaml || echo "none — good"
grep -nE 'Resource:\s*["'\'']\*["'\'']' infra/codebuild-projects.yaml || echo "none — good"

# The only cross-account power is AssumeRole into the three member roles:
grep -n 'sts:AssumeRole' infra/codebuild-projects.yaml
grep -n 'role/${MemberRoleName}-' infra/codebuild-projects.yaml

# Prove the checker actually GUARDS (temporarily break an invariant, expect FAIL):
cp infra/codebuild-projects.yaml /tmp/cb.bak
sed -i 's/pdlv-/pde-/' infra/codebuild-projects.yaml
python3 infra/validate_codebuild_projects.py; echo "exit=$?"   # expect FAIL + exit=1
cp /tmp/cb.bak infra/codebuild-projects.yaml                    # restore
python3 infra/validate_codebuild_projects.py; echo "exit=$?"   # expect PASS + exit=0
```

## STEP 4 — Zero-deploy confirmation (Universal Criteria 1 & 5)

```bash
# Story 2.1 deploys NOTHING. Confirm no pdlv- stack was created by this story:
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName,'pdlv-')].StackName"
# EXPECT: [] — the live Hub deploy is Story 2.3, not 2.1.
```

Record in `governance/RUNBOOK.md` Story 2.1 the validator's sealed one-line verdict:
`pass — codebuild-projects.yaml passes cfn-lint + Checkov + the 32-invariant offline checker; pdlv- naming, Project=PDE tags, and least-privilege (AssumeRole-only cross-account, no wildcard/admin) confirmed; nothing deployed (static proof), <date>, confirmed by <who>`.

## Watch-items

- **Static only — do NOT deploy in 2.1.** The Hub bootstrap deploy is Story 2.3.
- **`pde-` in a Hub resource name = a regression** (RD-009). Only `pdlv-` on the Hub;
  the `pde-member-execution-<env>` reference is correct (member accounts, Story 1.1).
- **No broad Hub deploy policy** — the deploy project's cross-account power is
  `sts:AssumeRole` into the three named member roles only (RD-006).
- **Checkov triage:** read findings against the DoD; an informational note is not
  automatically a FAIL, but any real wildcard/privilege finding is.
- **Pipeline-Forensics (`360999005254`) is ZTIE's — never a target.** Management/root
  `467866449172` is zero-touch.
