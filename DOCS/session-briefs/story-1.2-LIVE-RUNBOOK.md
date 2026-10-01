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

## STEP 0 — Be in the Hub account

```bash
aws sts get-caller-identity --query Account --output text    # expect 641628980935
```

**PASS:** output is exactly `641628980935`. If not, switch to the Pipeline-Hub
console / role and relaunch CloudShell before continuing.

## STEP 1 — Tooling present and runnable

```bash
aws --version                                                # aws-cli/2.x (preinstalled)
python3 --version                                            # Python 3.x (preinstalled)
python3 -c "import boto3, sys; print('boto3', boto3.__version__)"   # preinstalled
pip install --user --upgrade cfn-lint                        # not preinstalled — add it
export PATH="$HOME/.local/bin:$PATH"
cfn-lint --version                                           # confirm on PATH
```

**PASS:** AWS CLI v2, Python 3, boto3, and cfn-lint each print a version with no
error.

## STEP 2 — Token-auth repo access (clone + scrub the token)

```bash
cd ~
git clone https://<TOKEN>@github.com/warrenrutledge64/pde-platform.git
cd pde-platform
git remote set-url origin https://github.com/warrenrutledge64/pde-platform.git
git remote -v                                                # confirm NO token in the URL
ls infra/member-execution-role.yaml scripts/phase1_gate.py   # templates/scripts on disk
```

**PASS:** the clone succeeds, the remote URL has no embedded token, and the Story
1.1 template + the Phase-1 gate script are present on disk.

> **Secret hygiene:** if the `<TOKEN>` ever appears in terminal output, **rotate it
> immediately** in GitHub. Prefer a fine-grained PAT scoped to this repo only.

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
3. **STEP 2** — token-auth clone works; repo (templates + gate script) is on disk;
   remote URL carries no token.
4. **STEP 3** — the committed gate script passes its offline proof (24 invariants)
   and `--help` runs.
5. **STEP 4** — management account is zero-touch (no `pde-` stacks).

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
