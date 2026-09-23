# Contributing to Family Connect

Start with [STATUS](docs/STATUS.md), [PLAN](docs/PLAN.md) and the
[documentation map](docs/README.md). They distinguish current behavior from dated experiments.
The repository-wide [license decision](docs/licensing.md) remains pending.

## Changes and reports

Keep changes focused. Describe the problem, expected behavior, exact platform/version,
validation performed and remaining limits. Documentation corrections and reproducible bug
reports are useful. Do not include keys, invitation tokens, profiles, databases or personal
messages. Security-sensitive reports follow [SECURITY.md](SECURITY.md).

Do not alter deployment, protocol or release-signing behavior as a side effect of a UI/docs
change. Tests should establish behavior, not merely repeat implementation details.

## Development setup and checks

The public main branch is an earlier source snapshot than the distributed Android beta49.
The matching source checkpoint remains to be published; the commands below describe
the intended build/check process, not a reproducible beta49 build from current main.

- **Python/control/identity:** use an isolated virtual environment, install
  `control/requirements.lock` and `device_identity/requirements.lock`, then run
  `python -m pytest -q`. Messenger tests also use `messenger/requirements.lock`.
- **Linux:** system Python needs GI, GTK 4.8+, libadwaita 1.2+ and cryptography.
  Run desktop tests and GUI smoke/layout checks using the commands in
  [.github/workflows/clients.yml](.github/workflows/clients.yml). GUI checks need a
  display or dbus-run-session with Xvfb; CI renderer overrides are not app defaults.
- **Windows:** build and run installer, broker and UI checks on Windows using the same
  workflow and [native build guide](docs/windows-native.en.md). Cross-compilation alone
  does not validate Windows runtime behavior.
- **Android:** use the JDK/SDK/Gradle versions and pinned native dependency setup in the
  client workflow. Run the matching variant's unit/lint/build checks; hardware VPN and
  UI acceptance are separate. The default build includes multiple ABIs; ARM64 friends
  builds explicitly use `-PfcTargetAbi=arm64-v8a`. Never substitute debug signatures
  for the established friends update key.

## Documentation and languages

`README.md` is the canonical English product introduction. `README.ru.md` is its Russian
semantic equivalent. Change both in the same patch, preserving section order, platform
statuses, limitations and download destinations. `README.en.md` is a compatibility link,
not a third copy. The PR checklist makes the translation check explicit.

Use [STATUS](docs/STATUS.md) for current facts. Date historical reports and mark superseded
instructions. Check relative links and anchors, render Mermaid in a compatible renderer,
and visually inspect images. Run `python3 scripts/check_public_docs.py --all` for local links, anchors and image paths,
then check its external URL list and render changed Mermaid diagrams. Run
`git diff --check`; there was no dedicated Markdown CI
workflow at the time of this audit. Do not add guessed downloads or synthetic app screenshots.

## Releases

After every version change, update STATUS, PLAN and the dated release report in the
same task. Update the public RU/EN guides, download links and checksums when distribution
changes. Record candidate, installed, public and invitation-page versions separately;
include validation, rollback and outstanding checks. See the
[version documentation checklist](docs/releases.md#documentation-with-every-version).

Read [release distribution](docs/releases.md) and [update signing](docs/updates.en.md).
Release assets are immutable. Offline signing follows successful platform checks and
verification of downloaded assets; private signing keys do not enter CI or the server.
