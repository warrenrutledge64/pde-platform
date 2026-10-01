#!/usr/bin/env bash
# PDE Hub CloudShell launch-pad bootstrap (Story 1.2).
#
# ONE named command instead of a copy-pasted block — this removes the paste-a-stale-
# fragment failure that sank attempts 1 & 2 (the operator kept re-running an old
# token-in-URL `git clone https://YOUR_TOKEN@github.com/...` line). It:
#   1. confirms you are in Pipeline-Hub 641628980935 (fail-safe refuse otherwise),
#   2. hands your GitHub PAT to git via the credential helper — the token is NEVER
#      written into the clone URL or .git/config (only ~/.git-credentials, mode 600),
#   3. clones a CLEAN URL and checks out feature/story-1.2 (where the 1.2 artifacts
#      live — they are NOT on main),
#   4. runs a fail-loud launch-pad VERIFY and prints LAUNCH-PAD VERIFY: PASS/FAIL.
#
# pde-platform is a PRIVATE repo, so a raw.githubusercontent.com URL needs auth —
# you cannot fetch this script anonymously. Run it one of two ways from a Pipeline-Hub
# CloudShell session:
#
#   A) FETCH-AND-RUN with a token (private-repo raw fetch via the GitHub API):
#        read -rs -p "GitHub PAT: " GH_PAT && echo
#        curl -fsSL -H "Authorization: Bearer $GH_PAT" \
#          -H "Accept: application/vnd.github.raw" \
#          https://api.github.com/repos/warrenrutledge64/pde-platform/contents/scripts/bootstrap_launchpad.sh?ref=feature/story-1.2 \
#          -o /tmp/bootstrap_launchpad.sh
#        bash /tmp/bootstrap_launchpad.sh      # it will prompt for the PAT again for the clone
#      (The script re-prompts for the PAT; that is fine. Or just use path B.)
#
#   B) SIMPLEST for a private repo — paste the inline ONE-SHOT block from the
#      LIVE-RUNBOOK STEP 0 (it clones + checks out + VERIFYs inline), OR after a
#      manual clone+checkout of feature/story-1.2:
#        bash scripts/bootstrap_launchpad.sh
#
# You will be prompted ONCE for your PAT (silent, no echo). Prefer a fine-grained PAT
# scoped to THIS repo only (contents: read). To remove it after the session:
#   rm -f ~/.git-credentials
#
# Exit 0 = LAUNCH-PAD VERIFY: PASS. Non-zero = stop and read the ✗ lines.

set -u

HUB_ACCOUNT_ID="641628980935"
REPO_OWNER="warrenrutledge64"
REPO_NAME="pde-platform"
BRANCH="feature/story-1.2"
REMEDIATION_COMMIT="677b632"   # must be an ancestor of HEAD (attempt-2 fix)
REQUIRED_FILES=(
  "scripts/phase1_gate.py"
  "scripts/test_phase1_gate.py"
  "infra/member-execution-role.yaml"
  "DOCS/CLOUDSHELL_BOOTSTRAP.md"
)

say()  { printf '%s\n' "$*"; }
fail() { printf '✗ %s\n' "$*"; }
pass() { printf '✓ %s\n' "$*"; }

# --- 1. Must be in the Hub account (trust the OUTPUT, not a label) ------------
acct="$(aws sts get-caller-identity --query Account --output text 2>/dev/null)"
say "Caller account: ${acct:-<none>}"
if [ "$acct" != "$HUB_ACCOUNT_ID" ]; then
  fail "not in Pipeline-Hub ($HUB_ACCOUNT_ID) — refusing to proceed. Relaunch CloudShell from the Hub."
  exit 1
fi
pass "in Pipeline-Hub $HUB_ACCOUNT_ID"

# --- 1b. Guard: $HOME must NOT itself be a git repo ---------------------------
# Real failure mode (Story 1.2 attempts 1-3): a stray `git init` had turned
# /home/cloudshell-user into a repo (HEAD = a bogus "Initial commit"). Every clone
# ran against that stray repo instead of cloning PDE, so the gate scripts were never
# on disk. Detect it and refuse with a precise fix, instead of cloning into a
# nested-repo mess.
if git -C "$HOME" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  home_top="$(git -C "$HOME" rev-parse --show-toplevel 2>/dev/null)"
  if [ "$home_top" = "$HOME" ]; then
    fail "\$HOME ($HOME) is itself a git repo — a stray 'git init' will hijack the clone."
    say  "  Fix (removes only the accidental git metadata, NOT your files):"
    say  "    rm -rf \"$HOME/.git\" && rm -rf \"$HOME/$REPO_NAME\""
    say  "  Then re-run this bootstrap. (See Story 1.2 attempts 1-3 — this was the root cause.)"
    exit 1
  fi
fi

# --- 2. Hand the PAT to git via the credential helper (never into the URL) ----
# Skip the clone/credential setup if we are ALREADY inside a correct checkout
# (path B: the operator cloned+checked out manually, then ran this from the repo).
in_repo=0
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  top="$(git rev-parse --show-toplevel)"
  if [ "$(basename "$top")" = "$REPO_NAME" ]; then in_repo=1; cd "$top"; fi
fi

if [ "$in_repo" = 0 ]; then
  git config --global credential.helper store
  # read -rs: silent, no echo of the secret
  read -rs -p "GitHub PAT: " GH_PAT && echo
  if [ -z "${GH_PAT:-}" ]; then fail "no PAT entered — aborting"; exit 2; fi
  printf 'https://%s:%s@github.com\n' "$REPO_OWNER" "$GH_PAT" > ~/.git-credentials
  chmod 600 ~/.git-credentials
  unset GH_PAT
  cd ~ || exit 1
  rm -rf "$REPO_NAME"
  if ! git clone "https://github.com/${REPO_OWNER}/${REPO_NAME}.git"; then
    fail "git clone failed — check the PAT and repo access"; exit 1
  fi
  cd "$REPO_NAME" || exit 1
fi

git fetch origin >/dev/null 2>&1
git checkout "$BRANCH" >/dev/null 2>&1 || { fail "could not check out $BRANCH"; exit 1; }

# --- 3. Fail-loud launch-pad VERIFY -------------------------------------------
ok=1
say "HEAD branch: $(git rev-parse --abbrev-ref HEAD)   HEAD sha: $(git rev-parse --short HEAD)"
if git merge-base --is-ancestor "$REMEDIATION_COMMIT" HEAD 2>/dev/null; then
  pass "remediation commit $REMEDIATION_COMMIT present"
else
  fail "remediation commit $REMEDIATION_COMMIT NOT present — wrong branch/code"; ok=0
fi
for f in "${REQUIRED_FILES[@]}"; do
  if [ -f "$f" ]; then pass "on disk: $f"; else fail "MISSING: $f"; ok=0; fi
done
if git config --get remote.origin.url | grep -q '@'; then
  fail "TOKEN in remote URL"; ok=0
else
  pass "remote URL carries no token"
fi
if grep -Rqs '@github.com' .git/config; then
  fail "credential-pattern in .git/config"; ok=0
else
  pass ".git/config clean"
fi

if [ "$ok" = 1 ]; then
  say "LAUNCH-PAD VERIFY: PASS"
  say "Next: python3 scripts/test_phase1_gate.py   (expect PASS — all 24 gate invariants hold)"
  exit 0
else
  say "LAUNCH-PAD VERIFY: FAIL — do NOT proceed; paste this output back"
  exit 1
fi
