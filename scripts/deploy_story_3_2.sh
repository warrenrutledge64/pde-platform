#!/usr/bin/env bash
# PDE Story 3.2 — one-shot live deploy (removes the human-wrong-dir / wrong-account path).
#
# WHY THIS EXISTS (VD-9 / OD-015 — seven straight environment misses, 2026-10-04..05)
# -----------------------------------------------------------------------------------
# Across attempts 1-7 the Story-3.2 branch was NEVER actually under test. Every failure
# was an operator/environment miss, never a deliverable defect:
#   * deploys run from ~ instead of the clone  -> "[ERROR]: Invalid template path"
#   * the "Dev" step run with HUB credentials   -> preflight "[ENV] dev creds are 641628980935,
#                                                   expected 946509368326"; Dev role never redeployed
#   * leftover / DELETE_FAILED pdlv- stacks from prior hand-runs -> ResourceExistenceCheck
#   * the mandatory preflight gate SKIPPED, then handed to the validator anyway.
#
# Prose guards in the LIVE-RUNBOOK kept being bypassed. Per the standing discipline
# (a repeatedly-skipped step gets a MECHANICAL guard, not more prose), this script makes
# the correct run the ONLY run that can reach the validator:
#   - it resolves the repo root from its OWN location (never depends on $PWD / ~);
#   - it HARD-VERIFIES the AWS account before each account-scoped phase (abort on mismatch);
#   - it reconciles the pdlv- namespace (incl. clearing a DELETE_FAILED stack) before deploy;
#   - it deploys the Story-3.2 stacks from the resolved repo root; and
#   - it runs scripts/preflight_story_3_2.py and ABORTS NON-ZERO unless it prints PASS,
#     so a validator can only ever be handed a run that passed the gate.
#
# TWO-ACCOUNT SHAPE (why there are two phases)
# --------------------------------------------
# The Hub stacks deploy with HUB creds (Pipeline-Hub 641628980935); the Dev member role
# deploys with DEV creds (Pipeline-Dev 946509368326). CloudShell is single-account, so you
# run this TWICE, once in each account's shell (or once in Hub if you have an assumable Dev
# profile — pass --dev-profile). Each phase refuses to run against the wrong account.
#
# USAGE (run from INSIDE the feature/story-3.2 clone)
# ---------------------------------------------------
#   # In a Pipeline-DEV 946509368326 shell (clone the repo there, cd in):
#   bash scripts/deploy_story_3_2.sh dev
#
#   # In the Pipeline-HUB 641628980935 shell:
#   bash scripts/deploy_story_3_2.sh hub
#
#   # If you have an assumable Dev profile from the Hub shell, you can do the Dev phase
#   # without switching shells:
#   bash scripts/deploy_story_3_2.sh dev --dev-profile <profile-with-dev-creds>
#
# ORDER: run `dev` FIRST (stands up the Dev member role the pipeline needs), then `hub`
# (stands up the orchestrator/codebuild/state-machine + runs the preflight to PASS). The
# `hub` phase ends by printing the preflight result; only a printed PASS clears the gate.
#
# Exit 0 = the phase succeeded (and, for `hub`, the preflight printed PASS). Non-zero =
# stop and read the ✗ lines; do NOT hand anything to the validator.

set -u

HUB_ACCOUNT_ID="641628980935"
DEV_ACCOUNT_ID="946509368326"
BRANCH="feature/story-3.2"
CANON="pdlv-hub-orchestrator pdlv-codebuild pdlv-promotion-pipeline-stack"

say()  { printf '%s\n' "$*"; }
fail() { printf '\342\234\227 %s\n' "$*" >&2; }   # ✗
pass() { printf '\342\234\223 %s\n' "$*"; }        # ✓

usage() {
  say "usage: bash scripts/deploy_story_3_2.sh <hub|dev> [--dev-profile <name>]"
  say "  hub : deploy the Hub stacks (orchestrator, codebuild, state-machine) + run the preflight"
  say "  dev : redeploy the Dev member execution role from this branch + verify it changed"
  exit 2
}

# --- Resolve the repo root from THIS script's location (never $PWD / ~) -------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"

PHASE="${1:-}"; shift || true
DEV_PROFILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dev-profile) DEV_PROFILE="${2:-}"; shift 2 || usage ;;
    *) usage ;;
  esac
done
case "$PHASE" in hub|dev) : ;; *) usage ;; esac

# aws wrapper that honours an optional profile (only used for the dev phase).
awsx() {
  if [ -n "$DEV_PROFILE" ] && [ "$PHASE" = dev ]; then
    aws --profile "$DEV_PROFILE" "$@"
  else
    aws "$@"
  fi
}

# --- Launch-pad lock: must be inside the clone, on the branch, templates present ---
cd "$REPO_ROOT" || { fail "cannot cd to repo root $REPO_ROOT"; exit 1; }
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "not inside a git clone (resolved repo root: $REPO_ROOT) — clone feature/story-3.2 and run from it"; exit 1
fi
BR="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BR" != "$BRANCH" ]; then
  fail "on branch '$BR', expected $BRANCH — run: git checkout $BRANCH && git reset --hard origin/$BRANCH"; exit 1
fi
for f in infra/hub-orchestrator-role.yaml infra/codebuild-projects.yaml \
         infra/state-machine.yaml infra/member-execution-role.yaml \
         infra/golden-path-artifact.yaml scripts/preflight_story_3_2.py; do
  [ -f "$f" ] || { fail "missing $f from $REPO_ROOT — wrong checkout"; exit 1; }
done
pass "launch-pad: inside the clone at $REPO_ROOT @ $(git log --oneline -1)"

# --- Account guard — trust sts:GetCallerIdentity, abort on mismatch -----------
acct="$(awsx sts get-caller-identity --query Account --output text 2>/dev/null || echo NONE)"
case "$PHASE" in
  hub)
    [ "$acct" = "$HUB_ACCOUNT_ID" ] || { fail "hub phase needs Pipeline-Hub $HUB_ACCOUNT_ID creds; got '$acct'. Run this from a Hub CloudShell."; exit 1; }
    pass "account verified: Pipeline-Hub $acct" ;;
  dev)
    [ "$acct" = "$DEV_ACCOUNT_ID" ] || { fail "dev phase needs Pipeline-Dev $DEV_ACCOUNT_ID creds; got '$acct'. Run this from a Dev CloudShell, or pass --dev-profile. (This is the Attempt-7 miss: the Dev step ran with Hub creds.)"; exit 1; }
    pass "account verified: Pipeline-Dev $acct" ;;
esac

# ============================================================================
# DEV PHASE — redeploy the member execution role FROM THIS BRANCH + verify.
# ============================================================================
if [ "$PHASE" = dev ]; then
  read -rs -p "ExternalId (the REAL shared secret, matches the member-trust condition): " EID && echo
  [ -n "${EID:-}" ] || { fail "no ExternalId entered"; exit 2; }
  say "deploying pde-trust-fabric (member role) into Dev $DEV_ACCOUNT_ID from $(git log --oneline -1)…"
  if ! awsx cloudformation deploy \
        --template-file infra/member-execution-role.yaml \
        --stack-name pde-trust-fabric \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides EnvironmentName=dev ExternalId="$EID" \
        --tags Project=PDE Story=3.2 Component=trust-fabric \
        --no-fail-on-empty-changeset; then
    unset EID; fail "member-role deploy failed — capture the error above; do NOT validate"; exit 1
  fi
  unset EID

  # VERIFY THE LIVE ROLE ACTUALLY CHANGED (never trust the deploy line) --------
  ok=1
  story_tag="$(awsx iam list-role-tags --role-name pde-member-execution-dev \
    --query "Tags[?Key=='Story'].Value" --output text 2>/dev/null)"
  if [ "$story_tag" = "3.2" ]; then pass "Dev role tagged Story=3.2"; else fail "Dev role Story tag is '${story_tag:-<none>}' (expected 3.2) — OLD role still live"; ok=0; fi

  pol="$(awsx iam list-attached-role-policies --role-name pde-member-execution-dev \
    --query "AttachedPolicies[?contains(PolicyName,'member-execution-permissions')].PolicyArn" --output text 2>/dev/null)"
  if [ -n "$pol" ]; then
    ver="$(awsx iam get-policy --policy-arn "$pol" --query "Policy.DefaultVersionId" --output text 2>/dev/null)"
    doc="$(awsx iam get-policy-version --policy-arn "$pol" --version-id "$ver" --query "PolicyVersion.Document" --output json 2>/dev/null)"
    if printf '%s' "$doc" | grep -q 'stack/pdlv-' && ! printf '%s' "$doc" | grep -q 'stack/pde-'; then
      pass "member policy CFN scope is stack/pdlv-* (not pde-*)"; else fail "member policy CFN scope is NOT pdlv-* only — OLD role still live"; ok=0; fi
    if printf '%s' "$doc" | grep -q 'dynamodb:CreateTable' && printf '%s' "$doc" | grep -q 'table/pdlv-'; then
      pass "member policy grants DynamoDB table-lifecycle on table/pdlv-*"; else fail "member policy missing the pdlv- DynamoDB grant — OLD role still live"; ok=0; fi
  else
    fail "could not find the member-execution-permissions policy on the role"; ok=0
  fi

  cond="$(awsx iam get-role --role-name pde-member-execution-dev \
    --query "Role.AssumeRolePolicyDocument.Statement[0].Condition" --output json 2>/dev/null)"
  if printf '%s' "$cond" | grep -q '<'; then fail "Dev trust ExternalId is a <placeholder> — the real secret was not applied"; ok=0; else pass "Dev trust ExternalId is a real value (no placeholder)"; fi

  if [ "$ok" = 1 ]; then
    say "DEV PHASE: PASS — the Dev member role is the Story-3.2 deliverable. Now run the HUB phase."
    exit 0
  else
    say "DEV PHASE: FAIL — the live Dev role is NOT the branch deliverable; do NOT proceed to Hub/validate."
    exit 1
  fi
fi

# ============================================================================
# HUB PHASE — reconcile the pdlv- namespace, deploy the three Hub stacks,
#             then run the preflight. Only a printed PASS clears the gate.
# ============================================================================

# --- Reusable pdlv--only force-delete that CLEARS a DELETE_FAILED stack -------
force_delete() {
  local S="$1"
  case "$S" in pdlv-*) : ;; *) fail "refusing to touch non-pdlv stack: $S"; return 0 ;; esac
  local st
  st="$(aws cloudformation describe-stacks --stack-name "$S" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo ABSENT)"
  [ "$st" = ABSENT ] && return 0
  say "  deleting pdlv- stack $S (status $st)…"
  aws cloudformation delete-stack --stack-name "$S"
  if aws cloudformation wait stack-delete-complete --stack-name "$S" 2>/dev/null; then return 0; fi
  st="$(aws cloudformation describe-stacks --stack-name "$S" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo ABSENT)"
  [ "$st" = ABSENT ] && return 0
  if [ "$st" = DELETE_FAILED ]; then
    local stuck
    stuck="$(aws cloudformation describe-stack-events --stack-name "$S" \
      --query "StackEvents[?ResourceStatus=='DELETE_FAILED'].LogicalResourceId" --output text | tr '\t' ' ')"
    say "  DELETE_FAILED; retrying --retain-resources $stuck"
    aws cloudformation delete-stack --stack-name "$S" --retain-resources $stuck
    aws cloudformation wait stack-delete-complete --stack-name "$S" 2>/dev/null && return 0
  fi
  fail "could NOT clear $S (status $st) — capture describe-stack-events and STOP"; return 1
}

say "STEP 1 — reconciling the pdlv- namespace to the canonical set…"
PRESENT="$(aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE \
      ROLLBACK_COMPLETE CREATE_FAILED ROLLBACK_FAILED UPDATE_ROLLBACK_FAILED \
      DELETE_FAILED REVIEW_IN_PROGRESS IMPORT_COMPLETE IMPORT_ROLLBACK_COMPLETE \
  --query "StackSummaries[?starts_with(StackName, 'pdlv-')].StackName" --output text 2>/dev/null)"
for S in $PRESENT; do
  case " $CANON " in
    *" $S "*)
      st="$(aws cloudformation describe-stacks --stack-name "$S" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo ABSENT)"
      case "$st" in
        DELETE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED|CREATE_FAILED|UPDATE_ROLLBACK_FAILED|REVIEW_IN_PROGRESS)
          say "  canonical $S is $st — clearing before deploy"; force_delete "$S" || exit 1 ;;
      esac ;;
    *) say "  stray (non-canonical) pdlv- stack: $S"; force_delete "$S" || exit 1 ;;
  esac
done
pass "pdlv- namespace reconciled (only canonical names or empty)"

deploy_hub() {
  local tmpl="$1" stack="$2" comp="$3"
  say "deploying $stack from $tmpl…"
  aws cloudformation deploy \
    --template-file "$tmpl" \
    --stack-name "$stack" \
    --capabilities CAPABILITY_NAMED_IAM \
    --tags Project=PDE Story=3.2 Component="$comp" \
    --no-fail-on-empty-changeset \
    || { fail "$stack deploy failed — capture the CREATE_FAILED ResourceStatusReason; do NOT validate"; return 1; }
  local st
  st="$(aws cloudformation describe-stacks --stack-name "$stack" --query "Stacks[0].StackStatus" --output text 2>/dev/null)"
  case "$st" in CREATE_COMPLETE|UPDATE_COMPLETE) pass "$stack -> $st" ;; *) fail "$stack -> $st (not complete)"; return 1 ;; esac
}

say "STEP 2 — deploying the Hub control plane…"
deploy_hub infra/hub-orchestrator-role.yaml pdlv-hub-orchestrator        hub-orchestrator || exit 1
deploy_hub infra/codebuild-projects.yaml    pdlv-codebuild               codebuild        || exit 1
deploy_hub infra/state-machine.yaml         pdlv-promotion-pipeline-stack state-machine    || exit 1

# --- The non-bypassable gate: preflight MUST print PASS -----------------------
say "STEP 3 — running the preflight gate (the validator may only judge a PASS)…"
pf_args=()
[ -n "$DEV_PROFILE" ] && pf_args+=(--dev-profile "$DEV_PROFILE")
if python3 scripts/preflight_story_3_2.py "${pf_args[@]}"; then
  pass "preflight PASS"
  say "HUB PHASE: PASS — Story-3.2 Hub control plane is live and the preflight gate is green."
  say "Hand this ENTIRE output to the INDEPENDENT validator; they author the DoD and seal the verdict."
  exit 0
else
  rc=$?
  fail "preflight did NOT pass (exit $rc) — the environment is NOT the Story-3.2 baseline."
  say  "Do NOT hand this to the validator. Re-run the DEV phase (member role) and/or fix the account/env, then re-run the HUB phase."
  exit 1
fi
