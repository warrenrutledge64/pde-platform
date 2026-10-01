# PDE Hub CloudShell Bootstrap (Story 1.2)

> **The operator's launch pad.** A documented, reproducible setup of the
> **Pipeline-Hub (`641628980935`) AWS CloudShell** environment that every PDE
> bootstrap action runs from: token-authenticated repository access + the tooling
> (AWS CLI, Python 3 / Boto3, cfn-lint) needed to deploy and validate PDE
> infrastructure. This is the environment the **Phase-1 gate** script
> ([`../scripts/phase1_gate.py`](../scripts/phase1_gate.py)) and all Phase-2
> bootstrap deploys run in.
>
> **Account / region:** Pipeline-Hub `641628980935`, region `us-east-1`.
> **Direction (RD-006 orchestrate-and-pull):** the Hub *directs*; execution is
> local to each member. The management/root account `467866449172` is **zero-touch**.

---

## 0. Before you start — confirm WHERE you are (every session)

CloudShell inherits the credentials of the console role you launched it from.
**Trust the output of `get-caller-identity`, not a tab label or a banner** (the #1
Story 1.1 operator trap was being in a different account than assumed):

```bash
aws sts get-caller-identity --query Account --output text   # expect 641628980935
```

If this is not `641628980935`, switch to the Pipeline-Hub console (or the right
role) and relaunch CloudShell before doing anything else.

> **Feed CloudShell commands ONE LINE AT A TIME.** Multi-line pastes can mis-feed
> (a known CloudShell behaviour); run each command and read its output before the
> next.
>
> **`/tmp` and `$HOME` persistence:** CloudShell persists `$HOME` (up to 1 GB)
> across sessions, but **`/tmp` is wiped on session recycle**. Keep the cloned repo
> and anything you need under `$HOME`; never rely on a file left in `/tmp`.

---

## 1. Tooling check (AWS CLI, Python 3 / Boto3, cfn-lint)

AWS CloudShell ships the **AWS CLI v2**, **Python 3**, **pip**, and **boto3**
preinstalled — and most current CloudShell images also ship **cfn-lint**. Confirm
them; install cfn-lint only if it is missing.

```bash
aws --version                 # aws-cli/2.x …   (preinstalled)
python3 --version             # Python 3.x      (preinstalled)
python3 -c "import boto3; print('boto3', boto3.__version__)"   # preinstalled
```

```bash
# Install ONLY if cfn-lint is not already present. CloudShell runs pip inside a
# virtualenv, where `pip install --user` FAILS with "User site-packages are not
# visible in this virtualenv" — do NOT use --user; a plain install into the active
# venv is correct.
cfn-lint --version 2>/dev/null || pip install --upgrade cfn-lint
cfn-lint --version            # confirm present + on PATH
```

> **Why not `--user`:** CloudShell activates a virtualenv, which disables user
> site-packages. `pip install --user cfn-lint` therefore errors — but if cfn-lint is
> already installed (common), that error is harmless noise. The line above sidesteps
> it: it runs the install only when cfn-lint is actually absent, and without `--user`.

Optional (the fuller static bar used in CI / Story 1.1's runbook):

```bash
pip install --user cfn-guard-rules checkov bandit   # policy-as-code + IaC/py scanning
```

---

## 2. Token-authenticated repository access (clone PDE)

### 2.0 Create the fine-grained PAT (first time / when it expires)

`pde-platform` is a **private** repo, so the clone needs a token. Create a
**fine-grained** PAT (least privilege, not a classic token):

**GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
tokens → Generate new token.**

| Field | Choose | Why |
|-------|--------|-----|
| **Token name** | e.g. `pde-cloudshell` | so you can find + revoke it |
| **Resource owner** | **`warrenrutledge64`** | must own `pde-platform`, or the token can't see it |
| **Expiration** | short (e.g. 7 days) | it only needs to live for the live run |
| **Repository access** | **Only select repositories → `pde-platform`** | least privilege (not "All repositories") |
| **Repository permissions → Contents** | **Read-only** | the ONE permission a `git clone`/`fetch` needs |

Leave everything else at **No access** (Metadata auto-sets to read-only — expected).
**Generate token**, copy the `github_pat_…` value, and paste it ONCE at the silent
`GitHub PAT:` prompt below. Only grant **Contents: Write** if you later *push* from
CloudShell (not needed for Story 1.2 — read-only).

> **Org-owned caveat:** if the repo ever lives under a GitHub **organization**, the
> org may require fine-grained tokens to be *approved* before they work (org Settings
> → Third-party Access → Personal access tokens). A 403/404 on clone *with* a valid
> token points here. For `warrenrutledge64`-owned repos this does not apply.

### 2.1 Clone with the credential helper (token NEVER in the URL)

GitHub is **source control only** (PDE constraint). CloudShell has no SSH keys, so
authenticate over HTTPS — but **never embed the token in the clone URL**. Hand the
PAT to git ONCE via a credential helper, so it lands only in `~/.git-credentials`
(mode 600) and never in `.git/config`. (Attempt 1 of the Story 1.2 live gate FAILED
precisely because a token-in-URL clone left the PAT in `.git/config`.)

> **Secret hygiene (hard rule):** a Personal Access Token embedded in a clone URL
> ends up **in the remote URL inside `.git/config` and in your shell history**. Use
> the credential-helper flow below instead. Prefer a **fine-grained PAT** scoped to
> *only* this repository (*contents: read*, plus *write* if you push from here). If a
> token is ever echoed to the transcript, **rotate it immediately** in GitHub.

> **Non-interactive on purpose:** do NOT use an interactive `read -p` for the PAT in a
> pasted multi-line block — CloudShell's terminal buffer swallows the following lines as
> the password input. Put the PAT in the first line, populate the credential helper
> *before* the clone, and keep the clone URL clean (no `username@` — that `@` would trip
> the `.git/config`-clean gate).

```bash
GH_PAT="paste_your_token_here_keep_the_quotes"

cd ~
rm -rf ~/.git pde-platform                            # clean start (idempotent)
git config --global credential.helper store
printf 'https://warrenrutledge64:%s@github.com\n' "$GH_PAT" > ~/.git-credentials
chmod 600 ~/.git-credentials
git clone https://github.com/warrenrutledge64/pde-platform.git   # CLEAN url, no token
cd pde-platform
unset GH_PAT
```

**Check out the story's branch** — PDE work-in-progress lives on a feature branch,
not `main`, so a plain clone of `main` will be MISSING the story's files:

```bash
git fetch origin
git checkout feature/story-1.2          # the branch carrying the current story's work
git rev-parse --abbrev-ref HEAD         # confirm you are on the expected branch
git config --get remote.origin.url      # confirm NO '@token@' in the URL
```

> Why this matters (Story 1.1 + 1.2-attempt-1 lessons combined): the validator's
> CloudShell *did not have the repo on the right branch*, so every
> `--template-file infra/…` / `scripts/…` reference failed `No such file or
> directory` and `git show <sha>` was `invalid object name`. **Cloning AND checking
> out the right branch is a prerequisite for every deploy** — the templates/scripts
> must be on disk first. Verify with the launch-pad check in the live runbook before
> doing anything else.

---

## 3. The one secret you need — the ExternalId (not committed, not echoed)

The trust fabric (Story 1.1) requires an `sts:ExternalId` on every Hub→member
`AssumeRole` (confused-deputy protection). It is **`NoEcho`** in the template and
**must never be committed or printed**. Set it as an environment variable for the
session (so it stays out of files and command history where possible):

```bash
read -rs -p "PDE ExternalId: " PDE_EXTERNAL_ID && export PDE_EXTERNAL_ID && echo
```

> `read -rs` reads it **silently** (no echo) — the value is never shown on screen.
> It must match the value the member-role trust condition enforces (the same value
> `pde-hub-orchestrator` will present in Phase 2). Long-term home: Hub Secrets
> Manager / SSM SecureString (Phase 2). **If it ever leaks, rotate it on all three
> members.**

---

## 4. The Phase-1 gate script (authored here; live run is Phase 2 / VD-3b)

The committed Boto3 gate — [`../scripts/phase1_gate.py`](../scripts/phase1_gate.py)
— assumes the member execution role (`pde-member-execution-<env>`) in Dev →
Sandbox → Prod sequentially (as `pde-hub-orchestrator`), presenting the ExternalId,
and prints each returned account id. Its own offline proof bar is
[`../scripts/test_phase1_gate.py`](../scripts/test_phase1_gate.py) (24 invariants,
no AWS/network).

```bash
python3 scripts/test_phase1_gate.py        # offline: expect PASS — all 24 invariants
python3 scripts/phase1_gate.py --help      # see the usage; no boto3 call yet
```

> **Option B (stakeholder-chosen, 2026-09-30):** `pde-hub-orchestrator` is created
> in **Phase 2**, so the *live cross-account* run of this script is the deferred
> **VD-3b** — it executes in Phase 2 once that role exists, from this same bootstrap
> environment. **Running it live is NOT part of Story 1.2's Definition of Done.** No
> throwaway Hub principal is stood up early.

When Phase 2 has created `pde-hub-orchestrator` and this CloudShell session is
operating *as* that role, the live run is simply:

```bash
export PDE_EXTERNAL_ID='<the-shared-secret>'    # (via `read -rs` as in §3)
python3 scripts/phase1_gate.py                  # expect: PASS — assumed all 3 members
# → prints dev=946509368326, sandbox=586917955591, prod=466494951534
```

---

## 5. Story 1.2 live proof (what the operator actually validates now)

Per Option B, Story 1.2's live Definition of Done is **reachability + tooling +
repo access** from Hub CloudShell — see the turnkey
[`session-briefs/story-1.2-LIVE-RUNBOOK.md`](session-briefs/story-1.2-LIVE-RUNBOOK.md).
In short, from Pipeline-Hub `641628980935` CloudShell:

1. `aws sts get-caller-identity` returns the Hub account `641628980935`.
2. AWS CLI v2, Python 3, Boto3, and cfn-lint are all present and runnable.
3. The repo clones over the credential-helper flow (**no token in the URL**) and
   HEAD is on `feature/story-1.2`, so the templates/scripts are on disk.
4. The **launch-pad VERIFY** block (runbook STEP 2a) returns `PASS` — pinned commit
   present, all four artifacts on disk, no token in the git config.
5. The committed gate script passes its offline proof (`test_phase1_gate.py`) and
   `--help` runs.

On that recorded pass, Story 1.2 closes Phase 1 (restore tag + inventory row).

---

## Watch-items (carried from Story 1.1 — real lessons)

- **Zero-touch management account.** Nothing in `467866449172`. The gate script
  hard-refuses to target the Hub or management accounts.
- **Derive per-account values FROM the account**, never hand-edit a per-account
  literal — the gate script does this internally (fixed account→env table). The #1
  Story 1.1 failure was a copy-pasted wrong `EnvironmentName`.
- **Never dump a role's trust document to inspect it** — `aws iam get-role` returns
  the full `AssumeRolePolicyDocument`, which includes the ExternalId value. Inspect
  with a projection (`--query 'Role.RoleName'`) or a presence boolean instead.
- **Pipeline-Forensics `360999005254` is ZTIE's account** — not part of PDE; never
  a target.
