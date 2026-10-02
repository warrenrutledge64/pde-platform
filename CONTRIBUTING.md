# Contributing to pde-platform

This repo is governed by a lightweight spec-driven process (see
[`governance/METHODOLOGY.md`](governance/METHODOLOGY.md)). The authoritative status
ledger is [`governance/RUNBOOK.md`](governance/RUNBOOK.md). A few conventions keep
`main` honest.

## Branches & PRs

- Work on a per-story branch (`feature/story-<id>` for deliverables,
  `docs/story-<id>-*` for close-out/governance-only changes).
- Open PRs with the base branch `main`. Never commit directly to `main`.
- The CI static bar (`.github/workflows/static-bar.yml`) runs on every PR that
  touches `infra/**`. It is **checkout-proof** — GitHub checks out the exact PR
  head, so the logs always reflect the code about to merge.

## Merge order: deliverable + close-out land together

**Rule: never merge a deliverable (`infra/**`) into `main` while the Validation &
Advancement Gate is still ARMED.**

A story's PR must carry BOTH the deliverable AND its validated close-out before it
is merged. "Close-out" means, on the branch head:

1. the sealed **Validation Result** recorded (verbatim) on the story,
2. the story status flipped to ✅,
3. the story's **Validation Debt** entry cleared, so the RUNBOOK's
   `**Gate status:**` line reads **DISARMED**.

### Why

If the deliverable merges first and the close-out lands later, `main` carries the
deployed artifact with a **stale ledger** — the story reads 🟡 on the source of
truth even though it passed — and the close-out has to be reconciled afterward in a
follow-up PR. This is the **fix-after-merge trap**; it bit Story 2.2 twice (PRs #24
and #25, see `OD-008`). It also strands any fixes discovered during validation on a
branch ahead of `main`.

### How it is enforced

- **CI merge-order guard** (`scripts/check_merge_order.py`, wired into the static
  bar): a PR that changes a deliverable while the gate is **ARMED** turns the PR
  **red**. Once the close-out disarms the gate at head, it goes **green**.
- **Convention: merge only when the PR is green.** Server-side branch protection is
  _not_ enforced on this private/free repo, so the red/green CI signal plus this
  convention is the guard — not a platform-blocked merge. Treat a red merge-order
  check as a hard stop.

Run it locally before pushing:

```sh
python3 scripts/check_merge_order.py --self-test
python3 scripts/check_merge_order.py --base origin/main
```

## Before you push

Run the offline bar from the repo root (PyPI is blocked in the dev sandbox, so the
heavier tools — cfn-lint / checkov — run in CI, not locally):

```sh
python3 scripts/check_docs.py                       # governance-doc consistency
python3 -m unittest scripts.test_check_docs         # its tests
python3 -m unittest scripts.test_check_merge_order  # merge-order guard tests
python3 infra/validate_state_machine.py --self-test # deliverable invariant checkers
```

## Validation discipline (why CI, not a hand-run)

Validate on a **checkout-proof** target — CI on the PR head — rather than a
hand-pasted clone. Across Story 2.2's 8 validation attempts, every wasted cycle was
a human clone/checkout problem (wrong repo, a literal `<TOKEN>` placeholder the shell
mis-parsed, or a stale pre-fix commit); none were real deliverable defects. See
`governance/METHODOLOGY.md` §7.
