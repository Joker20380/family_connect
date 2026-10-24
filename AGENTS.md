# Family Connect — session entry point

Before starting work, read `docs/STATUS.md` and the **current-priority section** of
`docs/PLAN.md`, then the selected task ID, its dependencies and completion gate.
Use `docs/README.md` to locate only the relevant runbook/source/evidence. STATUS and
PLAN are the current state and queue; `*.history-*.md`, implementation logs and
dated release checkpoints are historical evidence, not simultaneous active NEXTs.
A queued task is not permission to start it automatically after the selected task.

## Documentation routing

Always read:

- `docs/STATUS.md`
- current-priority section of `docs/PLAN.md` (`Current engineering priority / Текущий critical path`)
- the selected PLAN task and its applicable gates; read history only to resolve a
  specific question or contradiction, not the entire checkpoint feed

Additional documents only for the area being touched:

- restricted WebRTC / 5N: `docs/architecture.md`, relevant current sections of
  `docs/reticulum/HOME_GATEWAY_DESIGN.md`; read `docs/legal/DEPENDENCY_LICENSE_AUDIT.md`
  only for dependency/source reuse.
- Android transport: relevant Android code-map and client docs.
- fleet: fleet docs.
- release: release runbook.

Do not require reading historical release reports, implementation logs, or unrelated
platform docs for every task.

Work in this repository, not the neighbouring microtrader project. Open new sessions
with this directory as the project root so these instructions are loaded.
User instructions take precedence. Continue authorized work; do not ask again merely
because a runbook describes a deployment step. Respect actual sandbox permissions.

## Commit and push policy

Owner instruction,2026-10-24: commit and push every completed logical change
immediately, including its source, tests and documentation. Do not accumulate
finished work locally until the end of a long session. This is standing permission
to commit and push; do not ask again for each step. A later explicit local-only or
no-push instruction takes precedence. A development pause still allows a separately
requested source checkpoint; it does not resume implementation.

Before committing, inspect the staged diff and check for secrets, private user data
and accidental build output. Keep state directories, source capsules, raw private
evidence, keys/profiles, product databases, backups and release-signing secrets out
of Git. Preserve them locally; never force-add ignored files to satisfy "everything".
Commit safe sources/tests/docs and sanitized manifests/checksums, not private state.

Use the existing agreed branch/upstream and ordinary non-force pushes. Preserve
other work; never reset/clean or rewrite published history to make a push succeed.
Label incomplete work as a checkpoint, not a release or acceptance PASS. A source
push does not authorize deployment, release tags, public installers/catalog changes
or server policy changes. Verify the remote branch SHA after pushing and report the
commit and outcome. If authentication/network or a divergent remote blocks pushing,
retain the local commit and report the exact blocker; do not claim it was pushed.

After every version change, update documentation in the same task: STATUS, PLAN,
the dated release report, and applicable RU/EN guides/download links/checksums.
Distinguish built, installed, publicly distributed and invitation-page versions;
verify public artifacts before documenting rollout as complete.

At the start, check git status and the latest deployment/release result. Preserve
uncommitted work. Do not assume a build is installed or a commit is deployed. Before
ending, update STATUS (including any unfinished work), PLAN and the dated release
report with exact versions, tests, rollout/rollback paths and remaining checks.

Authorized Family Connect gateway hosts: `185.251.89.19:/opt/apps/family_connect`
and `186.246.45.246:/opt/apps/family_connect` (Amsterdam, explicitly authorized by
the user on 2026-09-13; native WG pilot under `amsterdam/`).
`186.246.51.201` is excluded. Never operate neighbouring MicroTrader services. Client
private keys/profiles, product DB, backups and release signing secrets stay out of Git,
CI and command output. Public anchors and signed catalogs may be committed.

Release key: local `state-client-build/update-signing/ed25519.key`, never CI/server.
Use `scripts/sign_update.py` only after release assets have passed platform CI and
have been downloaded and checked. Update sequence must increase; never replace an
already published version/tag with different binaries.

Choose checks by the changed risk and mandatory gate, starting with relevant tests.
Do not rerun the entire historical suite after every small change without a concrete
reason. Keep full/release gates where required; this rule does not authorize hiding
mandatory tests. For documentation-only tasks, verify content, links and whitespace.

Python checks: `python -m pytest -q` using control and identity lockfiles and the
relevant test selection. TestClient
may stall in the local sandbox; request the normal outside-sandbox test execution if
that known restriction recurs. Linux layout check needs a display/Xvfb. Windows UI
must pass Windows CI; a Linux cross-build alone is not a runtime validation.

Do not enable subagents unless the user explicitly requests delegation.

Linux frontend is GTK 4/libadwaita from 0.2.7, not Tk. System Python must provide GI
and Gtk 4.8+/Adw 1.2+. Run GUI checks with dbus-run-session and Xvfb; headless CI uses
GSK_RENDERER=cairo, GTK_A11Y=none only in CI. Never set those for the installed app.
Keep the six-file Linux archive compatible with existing updaters. Never publish before
rendering and interaction checks; preserve immutable releases and offline signing.

Windows0.2.13+ releases use the independent signed `updates/windows.json` catalog.
After accepted native CI and artifact verification, publish the immutable Windows
installer and sign this catalog offline with `scripts/sign_update.py --platform windows`
and an increasing sequence. Update the Windows catalog with every Windows version;
do not leave a newer public installer invisible to Check for updates. Preserve the
legacy Linux/shared `updates/pilot.json`; Windows0.2.12 and earlier need one manual transition.
