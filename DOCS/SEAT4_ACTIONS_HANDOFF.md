# Seat 4 GitHub Actions — Human setup handoff
Status: planned; no UI changes or App credentials made by this document.

1. In the private repository GitHub UI, open Settings > Environments. Check whether required reviewers are available for a **private** repository under the active plan. If unavailable, STOP and report the limitation before adding secrets.
2. When supported, create `seat4-staging` (no credentials) and `seat4-production` (required Human reviewer, disallow self-review if offered, branch restriction). Screenshot the protection settings without secrets.
3. In private repo Settings > Actions > General, inspect allowed Actions, job token permissions, workflows from fork pull requests, and artifact retention. Use read-only default job token and minimum permitted Actions.
4. In GitHub App settings, preserve `Troikauge-Seat4` single-repository Contents read-only access. Do not broaden until required by a reviewed task.
5. Do NOT make or paste a private key/token into chat. After an authenticated workflow is prepared and protected, provision a private key only through a secured secret-setting process. App ID is not secret; installation ID alone does not authenticate.
6. Approve any future scoped privileged operation separately from PR acceptance. No ordinary PR merge or review automatically ratifies Troikauge OS governance.

Next artifact after evidence: PRIVATE repository workflow proposal, audited via an approved pathway that does not restore Codex Connector access to the private repository.
