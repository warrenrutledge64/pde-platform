# Platform Delivery Engine (PDE) — Backup & Restore-Point Procedure

> A **coordinated code + state** restore capability: when a slice goes badly,
> revert both the source (git) and the live state (whatever the code
> deploys/produces) back to a known-good restore point, as one unit. This is the
> defense against code-vs-deployed drift.

## What a "restore point" is

A restore point pairs two halves, captured together:

1. A **git tag** — `restore/phase-N-green` — marking the exact commit that passed
   a phase's end-of-phase validation.
2. A **state manifest** — a versioned file capturing the live state at that moment.
   For PDE, "state" means the deployed AWS reality across the account topology: the
   set of CloudFormation stacks and their template hashes + parameters (in the
   management account, the Hub, and each Spoke), the Org-wide CloudTrail
   configuration (trail name, S3 log bucket, KMS CMK, `IsOrganizationTrail`
   status), the cross-account IAM execution roles (name + trust policy + attached
   least-privilege policy per account), and the control-plane resources (Step
   Functions state-machine ARN + definition hash, CodeBuild project names). The
   manifest is committed to the repo and reflected in [`BOM.md`](BOM.md).

Restoring one without the other is never necessary — they move as a unit.

## Tagging convention

| Purpose | Format | Example |
|---------|--------|---------|
| Phase end-of-phase restore point | `restore/phase-<N>-green` | `restore/phase-0-green` |

**Rules:**
1. **Pass-only** — created only after the phase's live validation passes and is
   confirmed. Never on inference.
2. **Immutable** — once pushed, never moved, re-pointed, or deleted. A superseding
   phase gets its own new tag; the old one stays.
3. **Annotated** (`git tag -a`) — carries a message, author, and date.
4. **Paired with a manifest** — recorded in [`BOM.md`](BOM.md).

The `restore/` prefix is reserved exclusively for restore points, so
`git tag -l 'restore/*'` lists exactly the restore points and nothing else.

```bash
# Create (only on a confirmed pass, at the phase's green commit):
git checkout main && git pull --ff-only origin main
git tag -a restore/phase-<N>-green -m "Phase <N> pass: <what was validated>, <date>, confirmed by <who>"
git push origin restore/phase-<N>-green

# List / inspect:
git tag -l 'restore/*'
git show restore/phase-<N>-green --no-patch

# Check out (inspect a known-good state; detached HEAD is expected):
git fetch --tags origin
git checkout restore/phase-<N>-green
git checkout main
```

## Protected main line

`main` must be **change-by-review only**: require a pull request, block direct
pushes, block force-pushes, block deletion. This is what makes restore-point
history trustworthy. The repo owner (warrenrutledge64) enables this via the
repository's branch-protection / ruleset settings. **Note (free private repos):**
GitHub does not *enforce* branch protection or rulesets on a private repo under a
free personal plan — the rule can be created but is not enforced until the repo is
public or on a paid plan. Until then, treat PR-only as **self-enforced by
convention**: the executor never pushes to `main` directly and always opens a PR.

## Git-side revert procedure

**Never force-push `main`.** Reverting preserves history.

**Revert a merged change (preferred):**
```bash
git checkout -b revert/<desc>
git revert <bad-commit-sha>            # for a merge commit: git revert -m 1 <merge-sha>
git push origin revert/<desc>
# open a PR and merge it (main is PR-only)
```

**Roll `main` back to a restore point:**
```bash
git fetch --tags origin
git checkout -b restore/back-to-phase-<N>-green
git restore --source=restore/phase-<N>-green --staged --worktree -- .
git commit -m "Restore code to restore/phase-<N>-green"
git push origin restore/back-to-phase-<N>-green
# open a PR and merge it
```

> **Code is only half.** Reverting git returns the **source** to a known-good
> point. The **live state** is reverted using the manifest (see state-capture and
> coordinated-restore steps below). Always revert **both together**.

## State capture (PDE)

A **read-only** Python 3 / Boto3 procedure that queries the live AWS environment
across the account topology and writes a timestamped, versioned manifest, then
updates [`BOM.md`](BOM.md). Capture must **never** mutate the live system, and must
handle the empty/clean case gracefully (a fresh account with nothing deployed
yields an empty-but-valid manifest, not an error).

What it captures (the restore-relevant projection — identity + desired-state
fields, **not** raw resource objects, so volatile metadata does not flag false
drift):
- **CloudFormation stacks** — per account: stack name, `template_sha256`,
  parameters, stack-level tags. (Deliberately *not* `StackStatus`, `StackId`,
  or `LastUpdatedTime`, which change on any successful redeploy.)
- **Org-wide CloudTrail** — trail name, S3 log-bucket name, KMS CMK id,
  `IsOrganizationTrail`, `IsMultiRegionTrail`, `LogFileValidationEnabled`.
- **Cross-account IAM roles** — per Spoke: role name, trust policy document,
  attached/inline least-privilege policy document.
- **Control plane** — Step Functions state-machine name + definition SHA;
  CodeBuild project names.

The manifest is written under a versioned path (e.g.
`governance/restore-manifests/manifest-<UTC-timestamp>.json`), committed, and its
path recorded in the BOM section-4 restore-point row.

## Coordinated restore (PDE)

A procedure that, given a restore-point tag: **(1)** checks out the tagged commit
(`git checkout restore/phase-<N>-green`); **(2)** re-applies the state pinned in
that manifest by re-deploying each captured CloudFormation stack from the tagged
templates + parameters **and** re-applying the captured stack-level tags
(`aws cloudformation deploy --template-file ... --parameter-overrides ... --tags
...` — tags must be re-applied, or the restored stack loses them and correctly
fails the projected verify); **(3)** verifies the resulting live state matches the
manifest by re-running the read-only capture and diffing **only the
restore-relevant projection** above (name / template_sha256 / parameters / tags for
stacks; identity + desired-state fields for the rest). A diff of volatile metadata
alone is not a restore failure.

## Restore validation (acceptance)

1. Capture a restore point on a known-good state (tag + manifest).
2. Make a deliberate trivial change to code and to one piece of live state.
3. Run the coordinated restore back to the captured point.
4. Confirm **both** the code and the live state return to known-good, and the
   inventory reflects reality.
