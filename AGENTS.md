# Family Connect — session entry point

Before starting work, read `docs/STATUS.md`, then `docs/PLAN.md`. Use
`docs/README.md` to locate a runbook. These are the current state and next actions;
`docs/implementation-log.*.md` and dated release reports are historical evidence.

Work in this repository, not the neighbouring microtrader project. Open new sessions
with this directory as the project root so these instructions are loaded.
User instructions take precedence. Continue authorized work; do not ask again merely
because a runbook describes a deployment step. Respect actual sandbox permissions.

At the start, check git status and the latest deployment/release result. Preserve
uncommitted work. Do not assume a build is installed or a commit is deployed. Before
ending, update STATUS (including any unfinished work), PLAN and the dated release
report with exact versions, tests, rollout/rollback paths and remaining checks.

Only `185.251.89.19:/opt/apps/family_connect` is the Family Connect gateway host.
`186.246.51.201` is excluded. Never operate neighbouring MicroTrader services. Client
private keys/profiles, product DB, backups and release signing secrets stay out of Git,
CI and command output. Public anchors and signed catalogs may be committed.

Release key: local `state-client-build/update-signing/ed25519.key`, never CI/server.
Use `scripts/sign_update.py` only after release assets have passed platform CI and
have been downloaded and checked. Update sequence must increase; never replace an
already published version/tag with different binaries.

Python checks: `python -m pytest -q` using control and identity lockfiles. TestClient
may stall in the local sandbox; request the normal outside-sandbox test execution if
that known restriction recurs. Linux layout check needs a display/Xvfb. Windows UI
must pass Windows CI; a Linux cross-build alone is not a runtime validation.

Do not enable subagents unless the user explicitly requests delegation.
