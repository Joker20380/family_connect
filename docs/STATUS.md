# Current state / Текущее состояние

Updated: 2026-09-10. Desktop **0.2.7 published and installed on Linux**, source `68b6ffb`.
Server remains **0.2.1**, source `8cd0f2d`.

- Linux frontend now uses GTK 4/libadwaita. Compact header, rounded connection card,
  native selector/dialogs, one column of actions and content-sized height. Initial data
  is applied together; unchanged polling does not change widget properties.
- Installed from checksum-verified GitHub archive using the existing 0.2.6 updater;
  new GTK startup smoke passed. Current: `~/.local/share/family-connect/current`;
  `~/.local/share/family-connect/previous` retains 0.2.6. Launcher icon/app ID refreshed.
- Real laptop GTK 4.22/libadwaita 1.9 on native Wayland: 390×548 logical pixels.
  Eight-second read-only probe: two initial state renders, no periodic property updates;
  after two seconds warm-up, max/p95 timer interval 16.2 ms at a 16 ms target,
  0.154 CPU seconds. Earlier Tk sample had a 1.4-second gap outside Python handlers.
  This short measurement is not a universal performance guarantee; user should reopen
  the app and confirm perceived smoothness and appearance.
- Checks: 27 desktop Python tests, 24 GTK layouts (100–250%), coherent initial state,
  unchanged/stale polling, action independence and confirmation cancellation. GTK 4.8 /
  libadwaita 1.2 compatibility verified locally. Windows CI passed broker/UI/layout
  checks; all client jobs and phase0 passed.
- Windows: 0.2.7 installer available; native Windows behavior unchanged by this release.
  Personal Windows installation of this version is not confirmed.
- Linux prerequisites: Python GI, GTK >=4.8, libadwaita >=1.2, cryptography and
  NetworkManager. Ubuntu/Debian packages: `python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
  python3-cryptography`. Already present on this laptop; no system packages changed.
  Other hosts must install prerequisites before updating; failed smoke retains old app.
- Catalog `updates/pilot.json`: sequence 6, version 0.2.7, 90-day validity. HTTPS
  downloads, Ed25519 verification, user-confirmed installation. Reticulum delivery
  remains planned. Private signing key stays local under
  `state-client-build/update-signing/ed25519.key` and is never committed.
- Intermediate 0.2.4 release remains immutable without a signed catalog; later versions
  supersede it. Do not overwrite published binaries/tags.
- Server `185.251.89.19:/opt/apps/family_connect`: product API schema 3, localhost
  `127.0.0.1:18082`, gateway/worker/timer deployed in 0.2.1, three legacy peers preserved.
  Backup `/opt/backups/family-connect/20260910-110930`; rollback gateway image
  `family-connect-wireguard:rollback-20260910-110930`. No server changes for this release.
- Pending: live product enrollment/revoke smoke, runtime provisioning/ACK and public
  HTTPS ingress, Reticulum update delivery, native invitation/storage flows.

[Release](https://github.com/Joker20380/family_connect/releases/tag/v0.2.7)
· [Client CI](https://github.com/Joker20380/family_connect/actions/runs/34519568050)
· [Phase0 CI](https://github.com/Joker20380/family_connect/actions/runs/34519567996)
· [Release report](releases/0.2.7.ru.md) · [Plan](PLAN.md)

Temporary icon: `clients/assets/dodecahedron.svg`; regenerate PNG/ICO/embedded icon
with `python scripts/generate_app_icon.py` (Pillow). Final icon design deferred.
