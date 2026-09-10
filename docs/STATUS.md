# Current state / Текущее состояние

Updated: 2026-09-10. Desktop **0.2.5 published and installed on Linux**, source `d7d9c87`.
Server remains **0.2.1**, source `8cd0f2d`.

- Linux: installed from verified GitHub archive with the existing 0.2.3 updater;
  startup smoke passed, `~/.local/share/family-connect/previous` retains 0.2.3.
  Current: `~/.local/share/family-connect/current`.
- User reported 0.2.3 HiDPI clipping and sluggishness. Fixed font-aware startup sizing,
  redundant layout work, shared poll/action queue, selector and confirmation styling.
  Real laptop: effective font scale 2.06 despite Tk reporting 1.0; window 988×1028,
  all main actions visible. Small screens retain scrolling; scrollbar hides when unneeded.
- Real read-only VPN/UI probe: first 5-second sample included an 850 ms callback gap.
  Follow-up after a 2-second warm-up: maximum 17.9 ms / p95 16.3 ms at 16 ms target;
  paint <=3.2 ms, drain <=1.6 ms. Steady-state stalls were not reproduced; startup pause
  not conclusively attributed. Confirm perceived responsiveness with the user.
- Tests: 27 desktop Python tests; 24 Linux layouts (100–250%), initial action visibility,
  quiet polling/stale replies and slow-poll action independence. Windows CI passed
  broker, UI, polling regression and 144 layouts. Client and phase0 CI succeeded.
- Windows: 0.2.5 installer available. Changes this release target Linux; Windows behavior
  unchanged. User installation of 0.2.5 has not been confirmed.
- Catalog `updates/pilot.json`: sequence 4, version 0.2.5, 90-day validity. HTTPS downloads,
  Ed25519 verification and user-confirmed installation. Reticulum delivery remains planned.
  Private release key stays local under `state-client-build/update-signing/ed25519.key`.
- Intermediate 0.2.4 assets were published from e60d9e6 before final sizing polish;
  no catalog was signed for 0.2.4. Immutable release retained; clients update directly to 0.2.5.
- Server `185.251.89.19:/opt/apps/family_connect`: product API schema 3, localhost
  `127.0.0.1:18082`, gateway/worker/timer deployed in 0.2.1, 3 legacy peers preserved.
  Backup `/opt/backups/family-connect/20260910-110930`; rollback gateway image
  `family-connect-wireguard:rollback-20260910-110930`. Server unchanged by desktop release.
- Pending: live product enrollment/revoke smoke, runtime provisioning/ACK and public
  HTTPS ingress, Reticulum update delivery, native invitation/storage flows.

[Release](https://github.com/Joker20380/family_connect/releases/tag/v0.2.5)
· [Client CI](https://github.com/Joker20380/family_connect/actions/runs/34500466930)
· [Phase0 CI](https://github.com/Joker20380/family_connect/actions/runs/34500466896)
· [Release report](releases/0.2.5.ru.md) · [Plan](PLAN.md)

Temporary icon: `clients/assets/dodecahedron.svg`; regenerate PNG/ICO/embedded icon
with `python scripts/generate_app_icon.py` (Pillow). Final icon design deferred.
