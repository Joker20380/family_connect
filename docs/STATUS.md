# Current state / Текущее состояние

Updated: 2026-09-10. **0.2.5 Linux HiDPI/responsiveness fixes: release pending.** Desktop **0.2.3 published and installed on Linux**, source `79eb6db`. Server remains **0.2.1**, source `8cd0f2d`.

- Linux: 0.2.3 installed from verified GitHub archive using the existing 0.2.2 updater; startup smoke passed. New icon registered; `previous` retains 0.2.2.
  Current: `~/.local/share/family-connect/current`; backup:
  `~/.local/share/family-connect-backups/20260910-131353`.
- Windows: 0.2.3 installer published; Windows CI passed broker, UI and 144 layout cases.
  User can install 0.2.3 through Check for updates; user confirmed 0.2.1 works on both systems.
  User confirmed Windows and Linux 0.2.1 both work. Further hardware DPI testing remains optional.
- Tests: 171 Python tests, 18 Linux layouts, shared Python/C# signed catalog checks.
- Server: `185.251.89.19:/opt/apps/family_connect`, product API health OK, schema 3,
  localhost `127.0.0.1:18082`; Docker reconciliation worker succeeded, timer active.
  Gateway recreated with all 3 existing peers and gateway public key preserved.
  Existing manually managed peers are not automatically enrolled into the product DB.
- Server rollback: `/opt/backups/family-connect/20260910-110930`, gateway image
  `family-connect-wireguard:rollback-20260910-110930`. Other existing labs preserved.
- Signed update catalog: `updates/pilot.json`, sequence 3, version 0.2.3, 90-day validity.
  Local signing key: `state-client-build/update-signing/ed25519.key` (never Git/CI/server).
  HTTPS downloads, user-confirmed installation; Reticulum notifications not implemented.
- Product registration/provisioning and reconciliation code deployed. Public HTTPS ingress,
  native client runtime provisioning/ACK and a full live product enrollment/revoke smoke
  remain pending. Actual WireGuard install/remove/restart was verified locally.

[Release assets](https://github.com/Joker20380/family_connect/releases/tag/v0.2.3)
· [Client CI](https://github.com/Joker20380/family_connect/actions/runs/34497885075)
· [Phase 0 CI](https://github.com/Joker20380/family_connect/actions/runs/34497884671)
· [Next actions](PLAN.md) · [Release report](releases/0.2.3.ru.md)

Desktop appearance: graphite/indigo theme, accessible controls, temporary dodecahedron icon.
Editable icon source: `clients/assets/dodecahedron.svg`. Final icon design remains deferred.
Windows 0.2.3 installation on the user PC is not yet confirmed.

0.2.3: rounded native buttons and tilted dodecahedron. Background polling keeps the
last visible state without busy flashes or unchanged-state redraws; revisions reject
late responses after user actions. Poll failure/recovery remain visible. Polling
regressions passed on Linux and Windows alongside layout checks. Icon generator:
`python scripts/generate_app_icon.py` (Pillow), editable SVG/PNG/ICO/embedded Tk output.

0.2.4 assets were published from e60d9e6 before final size/scrollbar polish. No update
catalog was signed for 0.2.4. Immutable artifacts retained; final polish ships as 0.2.5.
