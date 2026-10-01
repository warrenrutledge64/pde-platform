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
preinstalled. Confirm them, then add **cfn-lint** (not preinstalled) into the
persistent user site so it survives a session recycle.

```bash
aws --version                 # aws-cli/2.x …   (preinstalled)
python3 --version             # Python 3.x      (preinstalled)
python3 -c "import boto3, sys; print('boto3', boto3.__version__)"   # preinstalled
```

Install cfn-lint for the current user (persists in `$HOME/.local`):

```bash
pip install --user --upgrade cfn-lint
cfn-lint --version            # confirm it is on PATH; if not, see the note below
```

> If `cfn-lint` is not found after a `--user` install, add the user bin to PATH for
> this session (and your `~/.bashrc` to persist it):
> ```bash
> export PATH="$HOME/.local/bin:$PATH"
> ```

Optional (the fuller static bar used in CI / Story 1.1's runbook):

```bash
pip install --user cfn-guard-rules checkov bandit   # policy-as-code + IaC/py scanning
```

---

## 2. Token-authenticated repository access (clone PDE)

GitHub is **source control only** (PDE constraint). Clone over **HTTPS with a
token embedded in the URL** — the convention for CloudShell, which has no SSH keys.

> **Secret hygiene (hard rule):** a Personal Access Token (`ghp_…`) embedded in a
> clone URL **will appear in your shell history and can leak into terminal
> output**. If a token is ever echoed to the transcript, **rotate it immediately**
> in GitHub (Settings → Developer settings → Tokens). Prefer a **fine-grained PAT**
> scoped to *only* this repository with *read* (and, if you push from here,
> *contents: write*) permission.

Clone (replace `<TOKEN>` with your PAT — do not paste the real token into any file):

```bash
cd ~
git clone https://<TOKEN>@github.com/warrenrutledge64/pde-platform.git
cd pde-platform
git rev-parse --abbrev-ref HEAD       # confirm the branch you expect
```

Keep the token out of the on-disk git config (the clone writes it into
`.git/config` remote URL). After cloning, scrub it from the stored remote and let
git prompt / use a credential helper instead:

```bash
# Replace the token-embedded remote with a clean HTTPS URL (token no longer at rest):
git remote set-url origin https://github.com/warrenrutledge64/pde-platform.git
git remote -v                          # confirm no token in the URL
```

> Why this matters for Story 1.1's lesson: the validator's CloudShell *did not have
> the repo*, so `aws cloudformation deploy --template-file infra/…` failed with
> `Invalid template path`. **The clone above is a prerequisite for every deploy** —
> the template must be on disk first. That is exactly what Story 1.2 establishes.

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
3. The repo clones over token-auth HTTPS and the templates/scripts are on disk.
4. The committed gate script passes its offline proof (`test_phase1_gate.py`) and
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
