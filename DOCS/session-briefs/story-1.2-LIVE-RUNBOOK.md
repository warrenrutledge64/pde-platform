# Story 1.2 — LIVE Validation Runbook (turnkey, Option B)

> **Story 1.2 = the Hub CloudShell bootstrap environment + the committed Phase-1
> gate script.** It CLOSES Phase 1. Full setup detail is in
> [`../CLOUDSHELL_BOOTSTRAP.md`](../CLOUDSHELL_BOOTSTRAP.md); this runbook is the
> **tight PASS/FAIL live gate** the operator runs and the independent validator
> seals.
>
> **Option B (stakeholder-chosen, 2026-09-30):** `pde-hub-orchestrator` is created
> in **Phase 2**, so Story 1.2's live DoD is **Hub-CloudShell reachability + tooling
> + token-auth repo access**, plus the gate script **committed** (offline-proven).
> The live cross-account `AssumeRole` run is the deferred **VD-3b** (Phase 2) — it is
> **NOT** part of 1.2's DoD, and no throwaway Hub principal is stood up.
>
> **Account / region:** Pipeline-Hub `641628980935`, `us-east-1`. Management/root
> `467866449172` is **zero-touch**. Run `aws sts get-caller-identity` before each
> block and trust the OUTPUT, not a label. Feed commands ONE LINE AT A TIME.

---

> ## ⚠ EXECUTION INTEGRITY (read before you run anything — attempts 1 & 2 both failed here)
> Both prior FAILs were the **launch pad never being on the right code**: attempt 1
> cloned `main` (feature files absent); attempt 2 pasted the OLD token-in-URL command
> with the literal `YOUR_TOKEN` placeholder and landed on an unrelated commit. **The
> gate script was never even reached.** To make this impossible:
> - Run the **ONE-SHOT BOOTSTRAP** block below exactly as-is (replace only the PAT at
>   the prompt). Do not hand-edit, do not paste fragments from an older message, and
>   do not paste a `git clone https://...@github.com` line from anywhere else.
> - It ends by printing `LAUNCH-PAD VERIFY: PASS`. **If you do not see that exact
>   line, STOP** and paste the full output back — do not run STEP 1+.

## STEP 0 — Stand up + VERIFY the launch pad

> **`pde-platform` is a PRIVATE repo** — a `raw.githubusercontent.com` URL will NOT
> fetch anonymously, so there is no public one-liner.
>
> **⚠ NEVER paste a bare `set -e` into interactive CloudShell** — if any later command
> returns non-zero, `set -e` **terminates your login shell** (the session "resets").
> This bit Story 1.2 (session reset after a pasted `set -e`). Both paths below avoid
> that: PATH A has no `set -e`; PATH B runs it inside a child `bash` (a subshell, so it
> can't kill your session).

### PATH A — named script (RECOMMENDED: 3 short lines, nothing big to mis-paste)

Run these **one line at a time**. No `set -e`. The token goes at git's password prompt
(paste your **PAT**, not an account password); the committed script then sets up the
credential helper, checks out the branch, and runs the fail-loud VERIFY.

```bash
cd ~ && rm -rf ~/.git pde-platform
```
```bash
git clone https://warrenrutledge64@github.com/warrenrutledge64/pde-platform.git
```
```bash
cd pde-platform && git checkout feature/story-1.2 && bash scripts/bootstrap_launchpad.sh
```

**PASS:** the script ends with **`LAUNCH-PAD VERIFY: PASS`** (`641628980935` confirmed,
HEAD on `feature/story-1.2`, scripts on disk, no token in `.git/config`).

### PATH B — inline one-shot (reset-safe heredoc; copy the WHOLE block)

Runs entirely inside a child `bash` (`bash <<'EOF' … EOF`), so the `set -e` inside it
can never terminate your interactive session. Copy from `bash <<'EOF'` through `EOF`.
It prompts once for your PAT (silent) and keeps the token out of the URL/`.git/config`.

```bash
bash <<'EOF'
set -e
aws sts get-caller-identity --query Account --output text    # MUST print 641628980935
if [ "$(git -C "$HOME" rev-parse --show-toplevel 2>/dev/null)" = "$HOME" ]; then
  echo "✗ \$HOME is a git repo — run:  rm -rf ~/.git ~/pde-platform  then re-run"; exit 2
fi
cd ~ && rm -rf pde-platform
git config --global credential.helper store
read -rs -p "GitHub PAT: " GH_PAT && echo
printf 'https://warrenrutledge64:%s@github.com\n' "$GH_PAT" > ~/.git-credentials
chmod 600 ~/.git-credentials && unset GH_PAT
git clone https://github.com/warrenrutledge64/pde-platform.git   # CLEAN url — no token in it
cd pde-platform
git fetch origin && git checkout feature/story-1.2
set +e
ok=1
echo "HEAD branch: $(git rev-parse --abbrev-ref HEAD)   HEAD sha: $(git rev-parse --short HEAD)"
git merge-base --is-ancestor 677b632 HEAD 2>/dev/null && echo "✓ remediation commit 677b632 present" || { echo "✗ remediation commit 677b632 NOT present — wrong branch/code"; ok=0; }
for f in scripts/phase1_gate.py scripts/test_phase1_gate.py infra/member-execution-role.yaml DOCS/CLOUDSHELL_BOOTSTRAP.md; do
  [ -f "$f" ] && echo "✓ on disk: $f" || { echo "✗ MISSING: $f"; ok=0; }
done
git config --get remote.origin.url | grep -q '@' && { echo "✗ TOKEN in remote URL"; ok=0; } || echo "✓ remote URL carries no token"
grep -Rqs '@github.com' .git/config && { echo "✗ credential-pattern in .git/config"; ok=0; } || echo "✓ .git/config clean"
[ "$ok" = 1 ] && echo "LAUNCH-PAD VERIFY: PASS" || echo "LAUNCH-PAD VERIFY: FAIL — do NOT proceed; paste this output back"
EOF
```

**PASS (either path):** the output ends with **`LAUNCH-PAD VERIFY: PASS`**.

> This supersedes the step-by-step STEP 2 / STEP 2a below (kept for reference / manual
> runs). Once you have seen `LAUNCH-PAD VERIFY: PASS`, continue to STEP 1.

## STEP 1 — Tooling present and runnable

```bash
aws --version                                                # aws-cli/2.x (preinstalled)
python3 --version                                            # Python 3.x (preinstalled)
python3 -c "import boto3; print('boto3', boto3.__version__)" # preinstalled
# cfn-lint: install ONLY if it is not already present. CloudShell runs pip inside a
# virtualenv, so `pip install --user` FAILS ("User site-packages are not visible in
# this virtualenv"). Do NOT use --user; a plain `pip install` into the active venv is
# correct — and most CloudShell images already ship cfn-lint, so this is often a no-op.
cfn-lint --version 2>/dev/null || pip install --upgrade cfn-lint
cfn-lint --version                                           # confirm present + on PATH
```

**PASS:** AWS CLI v2, Python 3, boto3, and cfn-lint each print a version with no
error. (If `cfn-lint --version` already printed `1.5x.x`, the tool is present and the
install line is a no-op — that is a PASS, not a failure. The `--user` error you may
have seen from an older copy of this runbook is harmless because cfn-lint was already
installed; this updated line avoids it entirely.)

## STEP 2 — Token-auth repo access (token NEVER in the remote URL)

> **Why this changed (attempt-1 FAIL, 2026-09-30):** the old flow embedded the
> token in the clone URL and then relied on a manual scrub line — which was skipped,
> leaving the PAT in `.git/config`. **New rule: the token is never written into the
> remote URL at all.** It is handed to git ONCE via a credential helper, so there is
> nothing to scrub.

```bash
cd ~
rm -rf pde-platform                                          # clean start (idempotent)
# Hand the PAT to git ONCE, out of the URL and off the command line (read -rs = no echo):
git config --global credential.helper store                 # (CloudShell $HOME is per-user)
read -rs -p "GitHub PAT: " GH_PAT && echo
printf 'https://warrenrutledge64:%s@github.com\n' "$GH_PAT" > ~/.git-credentials
chmod 600 ~/.git-credentials
unset GH_PAT                                                 # drop it from the shell env
# Clone over a CLEAN URL (no token in it); git pulls the PAT from the helper:
git clone https://github.com/warrenrutledge64/pde-platform.git
cd pde-platform
```

**Then check out THIS story's branch (the 1.2 artifacts are on `feature/story-1.2`,
NOT yet on `main`):**

```bash
git fetch origin
git checkout feature/story-1.2
git rev-parse --abbrev-ref HEAD                              # expect: feature/story-1.2
```

**PASS:** the clone succeeds and HEAD is on `feature/story-1.2`.

> **Secret hygiene:** the PAT lives only in `~/.git-credentials` (mode 600), never in
> `.git/config` and never on screen. Prefer a fine-grained PAT scoped to THIS repo
> (contents: read). If a token ever appears in terminal output, **rotate it
> immediately** in GitHub. To remove it after the session: `rm -f ~/.git-credentials`.

## STEP 2a — VERIFY the launch pad (fail-loud gate — attempt-1 would have stopped here)

Run this ONE block. It fails loudly (`✗`) if the pinned commit is missing, the
scripts are not on disk, or a token lingers in the git config — the exact three
things that sank attempt 1. **Do not proceed to STEP 3 unless every line prints `✓`.**

```bash
# in ~/pde-platform, on feature/story-1.2
ok=1
git cat-file -e fcfe4f3d 2>/dev/null && echo "✓ pinned commit fcfe4f3d present" || { echo "✗ pinned commit MISSING — you are not on the fetched branch"; ok=0; }
for f in scripts/phase1_gate.py scripts/test_phase1_gate.py infra/member-execution-role.yaml DOCS/CLOUDSHELL_BOOTSTRAP.md; do
  [ -f "$f" ] && echo "✓ on disk: $f" || { echo "✗ MISSING: $f"; ok=0; }
done
if git config --get remote.origin.url | grep -q '@'; then echo "✗ TOKEN in remote URL — scrub it"; ok=0; else echo "✓ remote URL carries no token"; fi
if grep -Rqs '@github.com' .git/config; then echo "✗ credential-pattern in .git/config"; ok=0; else echo "✓ .git/config is clean"; fi
[ "$ok" = 1 ] && echo "LAUNCH-PAD VERIFY: PASS" || echo "LAUNCH-PAD VERIFY: FAIL — fix the ✗ lines before STEP 3"
```

**PASS:** every line is `✓` and the last line reads `LAUNCH-PAD VERIFY: PASS`.

## STEP 3 — The committed Phase-1 gate script proves out offline

```bash
python3 scripts/test_phase1_gate.py          # expect: PASS — all 24 gate invariants hold
python3 scripts/phase1_gate.py --help        # usage prints; no AWS call made
```

**PASS:** `test_phase1_gate.py` reports `PASS — all 24 gate invariants hold`
(exit 0) and `--help` prints the usage.

## STEP 4 — Zero-touch management account (Universal Criterion 1)

```bash
# CONTEXT: management/root 467866449172 (only if you have read access there)
aws sts get-caller-identity --query Account --output text    # expect 467866449172
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName,'pde-')].StackName"
# EXPECT: [] — Story 1.2 deploys NOTHING anywhere, least of all the mgmt account.
```

**PASS:** `[]` — no PDE stacks in the management account (Story 1.2 is docs +
a committed script; it deploys nothing).

---

## PASS criteria (all must hold)

1. **STEP 0** — CloudShell is in Pipeline-Hub `641628980935`.
2. **STEP 1** — AWS CLI v2, Python 3, boto3, cfn-lint all present and runnable.
3. **STEP 2** — token-auth clone works via a credential helper (no token in the URL)
   and HEAD is on `feature/story-1.2`.
4. **STEP 2a** — `LAUNCH-PAD VERIFY: PASS` — pinned commit present, all four artifacts
   on disk, and no token in the git config.
5. **STEP 3** — the committed gate script passes its offline proof (24 invariants)
   and `--help` runs.
6. **STEP 4** — management account is zero-touch (no `pde-` stacks).

> **Deferred to Phase 2 (NOT a failure, NOT in this gate):** the live Hub→member
> `sts:AssumeRole` run of `scripts/phase1_gate.py` — it needs `pde-hub-orchestrator`,
> which Phase 2 creates. That is **VD-3b**.

## Record the result

In [`../../governance/RUNBOOK.md`](../../governance/RUNBOOK.md) Story 1.2:

`pass — Hub CloudShell (641628980935) reachability + tooling (AWS CLI v2 / Python 3 / Boto3 / cfn-lint) + token-auth repo clone proven live; Phase-1 gate script committed + offline-proven (24 invariants); mgmt account zero-touch; live cross-account AssumeRole deferred to Phase 2 (VD-3b), <date>, confirmed by <who>`

**On PASS — this CLOSES Phase 1:**
1. flip Story 1.2 🟡 → ✅ (summary row + detail header + Validation Result);
2. capture `restore/phase-1-green` (annotated tag at the validated commit) +
   write the state manifest (per [`../../governance/RESTORE.md`](../../governance/RESTORE.md));
3. add the restore-point row + any new inventory to
   [`../../governance/BOM.md`](../../governance/BOM.md);
4. flip the **Phase 1** row in the Progress Summary to ✅.

**On FAIL:** Story 1.2 stays 🟡; fix the specific failing step and re-run. Do not
advance to Phase 2.

## Backout

Nothing deployed → nothing to back out. To reset the bootstrap environment, delete
the cloned repo (`rm -rf ~/pde-platform`) and re-clone. The committed script/docs
are plain source changes revertable by the normal git revert procedure
([`../../governance/RESTORE.md`](../../governance/RESTORE.md)).
