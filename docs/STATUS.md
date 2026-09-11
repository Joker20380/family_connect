# Current state / Текущее состояние

Updated:2026-09-11. Desktop **0.2.9 published**, source `42f9d32`.
Linux/Windows release assets checked; signed update catalog sequence8 published in7650f32 and verified at the canonical URL. Linux **0.2.7 remains installed**; Windows last reported0.2.7.
No device installation performed. Server **0.2.1**, deployment source8cd0f2d/server
checkout117611c; TCP component **0.1.0** unchanged.

## Latest checkpoint — 2026-09-11

- Windows AWG signed profile/DPAPI, broker session/shared recovery, installer and UI
  implemented after native engine acceptance12/12 in CI34648502108/source29f8f27.
  Local issuer25 checks passed; platform/AWG broker/TCP regression CI pending.
  Explicit transport switching only; automatic WG→AWG→TCP remains next.
  No release/device/gateway changes. [Integration report](releases/2026-09-11-windows-awg-integration.ru.md).

### AWG engine foundation

- Windows AWG worker prepared from pinned amneziawg-go with stdin-only config,
  fresh Wintun, bound IPv4 outer UDP and no UAPI listener; native Windows CI pending.
  No broker/profile/GUI AWG integration or rollout yet; TCP remains accepted separately.
  [AWG engine report](releases/2026-09-11-windows-awg-engine.ru.md).

### Earlier TCP health checkpoint

- Windows TCP bound health monitoring implemented: two targets, two failed cycles,
  shared bounded recovery, in-flight cancellation before cleanup. Source9863427 passed
  clients34646258699 (336 layouts), native/session34646258684 (84/84 HTTP,
  14 DNS, 10 cleanup scenarios) and phase0 34646258740. Downloaded hashes verified.
  External REALITY/full routing/production probes remain unaccepted; no rollout.
  [Health report](releases/2026-09-11-windows-tcp-health.ru.md).

### Earlier recovery checkpoint

- Windows TCP engine-crash recovery implemented: three retries after successful cleanup,
  15/30/60s backoff, SID ownership retained, cancellation/service stop prevents reconnect,
  exhausted budget visible in UI. Source7de6e69 passed clients34643426316 (336 layouts),
  native/session34643426300 (66/66 HTTP, 11 DNS, 8 cleanup scenarios), phase0 34643426354.
  Downloaded artifact hashes verified; no release/device/server change.
  Health monitoring/external REALITY/full routing still pending.
  [Recovery report](releases/2026-09-11-windows-tcp-recovery.ru.md).

### Earlier packaging/UI checkpoint

- Windows TCP packaging/UI implemented: pinned engine bundled with licenses/hash checks,
  WG/TCP selection, separate activation, TCP-only connect, pending cancellation and
  asynchronous error visibility. Platform runtime CI34641891335 passed (288 layouts, installed payload/broker/uninstall);
  native/session34641891317 and phase0 34641891414 passed, source34a3211.
  Downloaded installer hash verified; no release/device/server change.
  [Packaging and UI report](releases/2026-09-11-windows-tcp-ui.ru.md).

### Earlier broker session checkpoint

- Windows TCP broker network session implemented9f32b0c, accepted with harness6d207a2.
  Async connect/cancel, SID ownership, own IPv4/IPv6 routes/DNS/NRPT, durable journal,
  engine-exit cleanup and SCM restart recovery. Actual LocalSystem scoped CI passed
  24/24 IPv4/IPv6 HTTP,4 OS DNS checks, other-user refusals and5 cleanup scenarios;
  prior native lifecycle18/18 retained. Native/session CI34639769072, phase0
  CI34639769135 and implementation platform CI34639148397 passed. Downloaded hashes verified.
  Test account setup changed from PowerShell to direct WinAPI; password stays in memory.
  Full external REALITY/default-route path not accepted here; CI uses scoped routes/domain.
  Normal installer has no tcp engine directory and GUI has no TCP control yet. Next:
  packaging/UI/recovery, full-routing acceptance before distribution, then Windows AWG.
  No release/device/server changes; Android then Reticulum and deferred user tests retained.
  [Complete session evidence](releases/2026-09-11-windows-tcp-session.ru.md) ·
  [Operations and limits](windows-tcp-session.ru.md).

### Earlier process lifetime checkpoint

- Windows TCP process lifetime primitive completed, sourcedc8df7d. Pinned binary checks,
  kill-on-close Job Object, stdin-only config after job assignment, unexpected-exit
  observation. Native CI34637235553 passed18/18 local TUN/VLESS requests across explicit
  stop, owner crash and engine crash; no orphan process/adapter, routes/DNS preserved.
  Both binary tamper cases refused. Wintun first-install Windows environment defect fixed.
  Client CI34637235600 all platforms and phase0 CI34637235589 passed; downloaded hashes
  reverified. Actual owner is isolated CI harness, not broker/SCM; TCP connect still
  unexposed. Next: broker network session/routes/DNS + crash/restart cleanup, then UI/AWG.
  No release/device/server change; Android then Reticulum order and deferred tests retained.
  [Lifecycle evidence](releases/2026-09-11-windows-tcp-lifecycle.ru.md).

### Earlier Windows profile checkpoint

- Windows TCP signed profile/broker storage completed, source4ba46e1. Strict device-bound
  Ed25519 grant, sequence floor, atomic LocalSystem DPAPI storage and offline issuer.
  300 Python tests; C# shared fixture/config +29 rejection checks; actual installed
  Windows broker18 checks passed. Client CI34633788708 all platforms and phase0
  CI34633788755 passed. Docker test-stage dependency and test-client ValueTask wait fixed.
  No release/device/server change. TCP connect remains unimplemented in broker/GUI;
  next lifecycle/routes/DNS, then UI/recovery and Windows AWG. User order confirmed:
  finish Windows, then Android transports, then stage5 Reticulum; updater/Play not gates.
  [Profile and CI evidence](releases/2026-09-11-windows-tcp-profile.ru.md).

### Earlier Windows engine checkpoint

- Windows TCP engine foundation completed, source ba929a0. Pinned Xray/Go and signed
  Wintun build passed actual Windows CI 34629412460; phase0 passed. Two fresh TUN/VLESS
  runs delivered 12/12 local HTTP responses; forced exit/adapter cleanup passed twice,
  default IPv4/IPv6 routes and DNS preserved. Downloaded binaries match build manifest.
  Preview only: REALITY/external VPN, broker/profile/routes/DNS integration, AWG and
  physical Windows acceptance remain pending. No release/install/server change.
  Next: Windows broker TCP lifecycle and validated protected REALITY profile.
  User network/load tests and Android updates remain deferred.
  [Windows engine evidence](releases/2026-09-11-windows-tcp-engine.ru.md).

### Earlier setup release

- Standalone TCP Setup0.1.0 published separately, source7eee3c3.281 tests and exact
  platform/TCP/AWG/phase0 CI passed. Downloaded archive matches prior VM-tested hash;
  detached setup signature created offline/verified with production anchor and published
  as updates/tcp-setup-0.1.0.json. Trusted verifier/anchor are required before bootstrap.
  No device/server changes. User keeps Android manual APK updates deferred; no Android
  update-check button/Google Play rollout. Next: native Windows AWG/TCP transport work.
  [Setup release/trust evidence](releases/2026-09-11-tcp-setup-release.ru.md).

### Earlier desktop release

- Desktop0.2.9 published from42f9d32 after exact Linux/Windows/Android CI; TCP and
  phase0 passed. Downloaded SHA256SUMS/Linux contents verified, Windows preview reviewed.
  Catalog signed offline, sequence8; signature/new-version/rollback checks passed in
  isolated updater state. Devices/server unchanged, network tests deferred. Next:
  trusted initial TCP Setup delivery, native Windows/Android transports/device acceptance.
  [Release evidence](releases/2026-09-11-release-0.2.9.ru.md).

### Earlier release preparation

- Source checkpoint180d79f pushed to main. All exact-source CI passed: clients
  (Linux/Windows/Android), TCP, AWG, phase0. No release job ran. Downloaded CI setup
  matches previously tested SHA256; downloaded Linux archive six files match git180d79f.
  Versions remain0.2.8 in source; review archive must not replace published0.2.8.
  Draft0.2.9 notes prepared; next version bump/exact-source CI/immutable publication
  and offline catalog signing. Installed versions/server unchanged, network tests deferred.
  [CI and artifacts](releases/2026-09-11-platform-ci.ru.md).

### Previous integration checkpoint

- User deferred further network/load tests and requested moving development forward.
  Functionality demonstrated; ordinary-load stability remains an open known limitation.
  Standalone TCP Setup sources/tests/CI/VM recipes integrated from bootstrap worktree
  into main; existing5 client prompt/recovery edits preserved/reviewed. pytest.ini now
  excludes operator archives from discovery.273 tests and display-backed GTK recovery
  passed; setup builds reproducibly to the previously VM-tested hash, six-file desktop
  compatibility retained. No install/server/network changes, CI/push/release not run.
  Next: source checkpoint/platform CI and trusted setup/new client release preparation.
  [Integration and deferred tests](releases/2026-09-11-setup-integration.ru.md).

### Earlier network evidence (further testing deferred by user)

- Isolated fresh-engine matched checks passed twice: TUN60/60, SOCKS60/60,
  direct60/60 concurrent +80/80 before/after. Installed Xray hash verified in container.
  All60 local TUN handshakes matched, max0.482ms; capture drops0, external socket peak6.
  Short low-load windows13.6/27.5s did not reproduce host failures; background load vs
  namespace/path remains unresolved. Containers removed, host rules unchanged, VPN off.
  Next: bounded isolated concurrency steps with fresh engines and per-request capture.
  [Isolated comparison](releases/2026-09-11-first-laptop-isolated.ru.md).

### Earlier offload comparison

- First-laptop pinned-all offload comparison completed. Final exact A/B/A VPN16/20→18/20→14/20,
  direct20/20 in all five phases. Twelve VPN TCP-connect timeouts; no DNS dependency.
  Offload disabling did not eliminate failures. Xray FD64→89→157 far below limit;
  sockets/queues grew, causal attribution remains open. Ettool TSO restoration also
  toggled mangleid; operator restore now uses two calls and full-feature equality passed.
  VPN off, exact rules cleanup and all feature restoration verified; no test timers.
  Next: isolated matched TUN/SOCKS/pinned direct with fresh engine and request timing.
  [Offload report](releases/2026-09-11-first-laptop-offload.ru.md).

### Earlier paired capture

- First-laptop paired headers completed: VPN35/40, direct39/40 during VPN,
  direct20/20 before/after. Four VPN TCP-connect timeouts and one DNS timeout;
  direct failure also DNS (shared resolver); pinned direct32/32. Zero capture drops.
  78 matched flows with outbound missing suffix retried >=10s, including53 with
  server prefix1327/no payload response; NIC vs external loss remains unproven.
  Exact cleanup passed, VPN off, server unchanged. Next: pinned-all control and bounded
  offload A/B/A with socket snapshots and restoration guard.
  [Paired report](releases/2026-09-11-first-laptop-paired.ru.md).

### Earlier first-laptop baseline

- First-laptop off→on→off now completed: normal-user direct20/20, pkexec→runuser
  direct20/20 before, VPN19/20 with direct20/20, direct20/20 after. Baseline contexts
  identical. One VPN HTTP-response timeout AFTER successful TLS; earlier second-laptop
  TLS timeout cause not established. Full IPv4/IPv6 rules restored, TUN/marker absent,
  VPN off. No code/install/server changes. Next: paired headers with current peer filters.
  [First-laptop result](releases/2026-09-11-first-laptop-resume.ru.md).

### Previous handoff (superseded for first-laptop test status)

- User paused second-laptop diagnosis and requested moving subsequent tests to first laptop.
  Transfer/tests on first have NOT started. Second last checked: TCP inactive; TSO/GSO on/on,
  rollback timers absent. Offload A/B/A completed, but control path failed too; inconclusive.
- TCP bootstrap and signed component installed on Ubuntu24.04.5 amd64, separate client
  provisioned, GUI import/connect/disconnect verified. New TCP identity added on gateway;
  previous TCP/WG/AWG identities preserved. Stable release versions above unchanged.
- Repeated password mechanism reproduced and client fix installed on second: standalone
  TCP monitors without automatic privileged restart; no redundant down for inactive final TCP.
  Main264 tests and GTK recovery passed. Fix is in uncommitted main files, not a published release.
  Repo pilot on first reads changed main on next launch; installed stable0.2.7 remains unchanged.
- Network failures unresolved: new Wi-Fi improved VPN36/40 vs direct40/40; timeout persists
  at10s. Bidirectional capture zero drops,23/116 selected flows show outbound payload gap.
  Offload A/B/A VPN1/20→3/20→1/20; direct0/20→1/20→0/20, so no causal offload conclusion.
- Standalone setup sources remain /tmp/fc-tcp-bootstrap, archived locally;269 tests originally,
  combined worktree273 after client fix. Independent-kernel Debian VM installation passed.
  Packaging integration, remote CI, trusted setup publication and new client release pending.
- Ubuntu appearance/terminal transfer, backups, all tests and next actions are recorded in
  [complete checkpoint](releases/2026-09-11-session-checkpoint.ru.md),
  [network report](releases/2026-09-11-ubuntu-network.ru.md),
  [appearance/rollback](ubuntu-laptop-settings.ru.md).

## Earlier milestones (historical state)

- Manual cancellation of the new TCP updater passed on laptop: genuine pkexec 126,
  GTK cancellation message, busy cleared/selection preserved, no repeat for 18 seconds.
  Component hashes and backup list unchanged; no policy/cache changes. Source unchanged.
  Next: trusted bootstrap distribution for clean Linux machines, VM/hardware acceptance
  and new client release. Stable app/server/published TCP unchanged.
  [Manual updater cancellation](releases/2026-09-11-tcp-updater-cancel.ru.md).

- Root-owned TCP updater and GTK pilot install implemented and installed on laptop.
  Fixed-operation broker verifies its trusted files and signed catalog; GUI confirms,
  handles cancellation and blocks busy/connected installs. Real desktop GTK→pkexec→broker
  signed installation passed; installed files match source/published TCP 0.1.0, TCP inactive.
  260 tests, 24 Xvfb layouts, 6 pilot geometries and recovery passed; screenshot reviewed.
  Host layout timing assertion also fails on previous UI; retained observation.
  Backup directory root:root mode corrected 0775→0755 after safe bootstrap refusal.
  Stable app/server unchanged; next pilot launch exposes button. All remote CI passed
  for 92308a4 (clients/TCP/AWG/phase0);
  manual Cancel now passed; fresh-machine bootstrap distribution and new client release remain.
  [Updater/UI report](releases/2026-09-11-tcp-updater.ru.md).

- TCP component **0.1.0 published and signed**, source/tag 7d1e738, catalog sequence 1
  in commit 53a000c. All main platform/TCP/AWG/phase0 CI and TCP tag release passed.
  Downloaded artifact matches local repack; fresh systemd DNS/HTTPS/reinstall/SIGKILL
  acceptance passed. Public HTTPS fetch as non-root and production-signature root install
  passed, followed by DNS/HTTPS and cleanup; disposable container removed.
  Stable laptop/server unchanged. Next: root-owned broker/bootstrap + explicit UI install,
  then native Windows/Android and VM/hardware gate before broad rollout.
  [Published pilot and evidence](releases/2026-09-11-tcp-release.ru.md).

- Authenticated TCP delivery implemented as an operator CLI: separate Ed25519 domain,
  component sequence/version floors, bounded HTTPS/hash/archive checks and root reverify.
  250 tests passed; ephemeral-key real bundle install/reinstall passed in Debian systemd.
  Initially tested with ephemeral key; production signature/public HTTPS now passed above.
  Remote CI and first TCP publication now completed; trusted broker/bootstrap and UI
  integration remain before broad rollout.
  [Delivery report](releases/2026-09-11-tcp-delivery.ru.md) · [Runbook](tcp-delivery.ru.md).

- Real systemd acceptance passed in a fresh Debian 12 Docker container (shared host kernel).
  Found/fixed missing procps/sysctl dependency: installer now refuses before writes.
  Corrected bundle: fresh install, actual resolved + application DNS, 6 VPN HTTPS checks,
  active-install refusal, stop/reinstall/profile preservation and SIGKILL ExecStopPost cleanup.
  IPv4/IPv6 rules restored, table/TUN/marker absent; both test containers removed.
  230 tests passed; filesystem tamper/rollback suite passed again. No host/server upgrade.
  Next: authenticated component delivery, native Windows/Android and platform CI;
  independent VM/hardware clean-install coverage remains a rollout gate.
  [Systemd evidence](releases/2026-09-11-tcp-systemd.ru.md).

- Separate Linux amd64 TCP component bundle implemented: deterministic archive, checksum
  preflight, active-service refusal, private backups, per-file atomic replacement and
  rollback on failure; existing profiles preserved and service never auto-started.
  229 Python tests passed; isolated filesystem install/tamper/upgrade/reload rollback passed.
  Xray matches cached pinned-revision image; repeated archive SHA256 identical.
  Initial filesystem test used stubs; real systemd container acceptance is now recorded above.
  CI artifact steps added but remote CI/signing/release not run; host install unchanged.
  [Bundle report](releases/2026-09-11-tcp-bundle.ru.md) · [Install runbook](linux-tcp-install.ru.md).

- TCP source integration into main completed after targeted review: installer refuses
  active/pending TCP state before writes; WG health prefers paired AWG endpoint when
  TCP differs. Full main suite 226 passed, GTK regression/kernel namespace checks passed,
  six-file updater archive compatibility verified. Review fix ca2a63a retained in pilot branch.
  Stable installed app/server unchanged; repository-based AWG pilot launcher now uses TCP
  backend on next launch. System helper dependencies were not reinstalled automatically.
  Next: reproducible clean-Linux component packaging/install, native platform integration,
  then fresh platform CI/new signed release. No push/remote CI/release yet.
  [Integration review and rollout limits](releases/2026-09-11-tcp-integration.ru.md).

- Manual system authorization cancellation passed: real TCP-helper pkexec returned 126,
  actual AuthorizationError reached recovery completion, policy stopped; no repeat pkexec
  for 18 s and no TUN. Watchdog/controller cleanup passed, no UDP fault or polkit changes.
  Recovery state was staged for this cancellation case; earlier full GTK network recovery
  supplies separate end-to-end coverage. Functional Linux pilot checklist now exercised.
  Next: review/integrate experimental diff, then current tests/CI and release preparation.
  Initial unlocalized backend AssertionError remains an open observation; not a reliability guarantee.
  [Manual cancellation evidence](releases/2026-09-11-polkit-cancel.ru.md).

- Real GTK/production LinuxTCP/pkexec recovery passed: established AWG → TCP in 59.88 s;
  connected/restored UI, selected profile preserved, actual Disconnect and close-after-
  disconnect passed. Root controller applied only endpoint UDP fault and verified cleanup.
  GTK recovery regression also passed, including injected AuthorizationError.
  Close-while-connected real dialog also passed: cancel preserves monitoring, confirm
  stops monitoring and leaves VPN as warned; controller then disconnected/cleaned it.
  Real polkit Cancel now passed in a separate test; no policy changes
  or temporary-authorization revocation were used. Stable launcher/releases unchanged.
  [GTK live evidence and acceptance limits](releases/2026-09-11-tcp-gtk.ru.md).

- Established AWG → TCP backend/policy recovery exercised on the laptop: one initial
  unlocalized AssertionError, then two successive passes at 45.32 s and 45.57 s after
  two failed health cycles. Real endpoint UDP blocks counted 1047/1154 packets.
  Unprivileged TCP health, resolved query, disconnect policy stop and cleanup passed.
  All three attempts cleaned up; no tunnels/test firewall left. No product code change.
  First failure remains an open observation; not a GTK/polkit end-to-end acceptance.
  Next: real experimental Linux UI/recovery/authorization-cancel acceptance before release.
  [Recovery evidence and limits](releases/2026-09-11-awg-tcp-recovery.ru.md).

- Corrected TCP helper installed and short laptop smoke passed: 3 bound HTTPS health
  checks, resolved query, gateway bypass/public TUN route, 3 local routes preserved.
  Cleanup restored complete IPv4/IPv6 policy-rule baseline; TUN/marker absent.
  Backup: /var/backups/family-connect/tcp-routing-1789119289/helper.
  New helper remains installed; test tunnel stopped. Main launcher/stable releases unchanged.
  Bounded backend/policy recovery now has two passes; see latest report above.
  [Installed-helper report](releases/2026-09-11-tcp-host-smoke.ru.md).

- New Wi-Fi baseline and TCP retest completed: gateway max 53.9 ms (was 496),
  Wi-Fi retries +7 (was +433); all baseline targets/HTTPS 30/30. Matched TCP test
  passed 120/120: direct/TUN/SOCKS HTTPS and direct/TUN DNS each 24/24, cleanup passed.
  Code/timeouts unchanged. Bounded isolated acceptance passed; not a long-run guarantee.
  Corrected helper installation/short smoke now passed; AWG → TCP recovery remains.
  User has completed network change; no further switch is pending.
  [Network-change comparison](releases/2026-09-11-network-change.ru.md).

- Current roadmap: **stage 4, client packaging/platform acceptance**. WG works;
  AWG/recovery passed in Linux pilot, not yet a cross-platform stable rollout.
  [Development roadmap](ROADMAP.ru.md).
- Local-link comparison completed: Wi-Fi gateway 30/30, median 31.35 ms, max 496 ms;
  VPS 26/30, control 28/30, direct HTTPS 30/30 (up to 2.608 s). Correlated gateway,
  control and HTTPS delays; Wi-Fi retries +433 including background traffic.
  Local network contributes jitter; this does not explain every prior TLS failure.
  Superseded by successful retest after user changed Wi-Fi; see latest result above.
  No installed code changed.
  [Local-link evidence](releases/2026-09-11-local-link.ru.md).

- Paired TCP-header diagnosis completed (experiment `2674d20`): 72/72 handshakes matched across client/server.
  In the failing round client SYN→SYN-ACK took 0.788–1.315 s, while server response
  took 9–73 microseconds (max across all flows 0.846 ms); two SYN retries were observed
  at both ends. Delay is outside server SYN processing; loss location is not proven.
  Full series: direct/TUN HTTPS 24/24, SOCKS 23/24, both DNS 24/24, server HTTPS 30/30.
  Post-test host routes use Wi-Fi/main. Next: compare local gateway/VPS latency and
  wireless counters before any host rollout. Capture cleanup passed; no deployment.
  [Paired capture report](releases/2026-09-11-tcp-packets.ru.md).

- Matched TCP diagnostics completed (experiment `d776b41`): two isolated 24-round series with identical HTTPS
  endpoint/timeouts. TUN 48/48, SOCKS 47/48, direct 47/48; tunnel UDP DNS 46/48,
  direct UDP DNS 45/48. SOCKS failure was TLS setup timeout; direct failure occurred
  after TLS while waiting for HTTP data. Gateway TCP snapshots show SYN-SENT/retrans,
  without per-request socket attribution. Root cause/censorship not established.
  Both cleanup checks passed. No host install, server mutation or release.
  Paired TCP-header comparison is now complete; see latest report above.
  [Matched diagnosis](releases/2026-09-11-tcp-matched.ru.md).

- TCP routing correction implemented in experimental commit `6d7f569`: preserve more-specific
  main routes; explicit gateway /32 bypass plus prohibit-on-missing-route; exact cleanup,
  collision checks, legacy marker support and retry after cleanup failure.
  Real-kernel network-none container checks passed; 222 Python tests passed.
  Not installed on the laptop; no host VPN test or server change in this stage.
  Isolated live traffic: first TUN/SOCKS 24/24 each, UDP DNS 23/24; expanded comparison
  TUN 24/24, SOCKS 22/24, tunnel UDP DNS 23/24, TCP DNS 22/24, direct UDP DNS 22/24.
  Cleanup passed. Direct DNS also timed out; all prior instability is not resolved.
  Matched comparison completed below the routing milestone; see latest diagnosis above.
  [Routing correction](releases/2026-09-11-tcp-routing.ru.md).

- TCP diagnosis update: direct server HTTPS 36/36; long SOCKS-only comparison 216/216
  checks passed, but long full-TUN comparison degraded (including independent SOCKS).
  Local HTTP stayed 36/36. Packet capture confirms gateway-directed RST on TUN;
  no gateway SYN on TUN was found. Code review found missing preservation of more-specific
  main-table routes before TUN lookup. This is a concrete routing defect; it does not yet
  prove the cause of every timeout. No correction installed or release published.
  TCP service/tunnel/test rules are verified off/removed; main WG/AWG code unchanged.
  [Diagnosis and evidence](releases/2026-09-11-tcp-diagnosis.ru.md).

- TCP experiment: VLESS + REALITY deployed separately on TCP/443; Xray 26.3.27.
  Linux TUN/helper installed; isolated HTTPS/DNS and unauthorized-client rejection passed.
  One real blocked-WG/AWG → TCP run passed in 16.81 seconds. Repeated requests still
  time out; increasing probe timeouts did not resolve this. Cause remains unknown.
  222 Python tests (78 desktop), GTK layout/recovery checks passed locally; no CI/release.
  Source checkpoint `fa3c71e` is preserved separately in local branch `pilot/tcp-reality-2026-09-11`;
  main WG/AWG launcher and stable app remain on previous code. TCP service is inactive
  on the laptop; interface, policy rules and test firewall tables verified removed.
  Server TCP container remains deployed. Resume diagnosis before integrating/releasing TCP.
  [Checkpoint and next diagnostic step](releases/2026-09-11-tcp.ru.md).

- User priority: connection resilience. AWG 2.0 pilot deployed separately on UDP/51821;
  existing WG/three peers preserved. Linux root helper installed and real host AWG
  handshake/HTTPS verified. Real blocked-WG → AWG fallback test passed, then cleaned up.
  Client implementation is an unreleased working-tree pilot; installed stable 0.2.7
  and published 0.2.8 catalog remain unchanged. Separate AWG pilot launcher available.
  AWG milestone: 189 Python tests passed (45 desktop). Upstream engine tests, isolated AWG data
  test, 24 GTK layouts and six additional pilot-label layouts passed.
  Established-session monitoring/recovery now implemented in the open Linux pilot:
  15-second checks, two failed cycles, three bounded attempts with 15/30/60-second backoff.
  Explicit disconnect/selection/close/auth cancellation stop recovery. Two independent
  bound HTTPS probes; 199 Python tests and GTK recovery/layout checks passed.
  Established WG endpoint block recovered through AWG in 44.05 seconds on the laptop.
  Updated root helper installed; no new stable release or server change in this stage.
  Native Windows/Android AWG, stable TCP integration and Reticulum delivery remain pending.
  Same server/IP and UDP limitation. [Recovery report](releases/2026-09-10-recovery.ru.md).
  [AWG rollout report](releases/2026-09-10-awg.ru.md) · [evidence](awg-resilience-result.json).

- Windows now follows the Linux 0.2.7 composition: compact branding, rounded status card,
  single-column buttons, smaller typography, content-sized startup window, themed
  confirmation/device-code dialogs and dark main title bar on supported Windows.
  Windows-specific activation and broker behavior preserved. Initial connection status
  no longer becomes Working during unrelated actions.
- Windows runtime checks: 96 layouts (RU/EN, four states, three sizes, 100–250%),
  nested card labels, polling/stale replies and confirmation cancellation; broker,
  installed UI and driver checks passed. CI-generated preview saved below.
- 0.2.8 artifacts downloaded and SHA256SUMS verified before offline catalog signing.
  Catalog sequence 7; signature verified from published commit 3171fed. Main raw URL
  propagation now verified with the installed updater: old version detects 0.2.8 and
  0.2.8 detects no newer version. Earlier cached 0.2.7 response is resolved.
  No personal Windows machine was accessed; user must run the installer or in-app update.

- Android test APK from successful CI shared with user (debug build, profile import).
  Existing local `state-v2/pilot-clients/fc-ru-android.conf` verified against active and
  persistent gateway public key/addresses; mode 0600, ignored by Git. Phone import,
  handshake and external-IP test remain pending. No Android key rotation or server change.
- Windows device code after reinstall matches the existing peer at 10.77.0.4. Fresh
  signed activation issued locally under `state-client-build/activation/`, expires for
  import 2026-09-11 19:53 UTC. Import on Windows and actual connection test remain pending.
  Existing three peers preserved; no gateway mutation/restart was needed.

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
  User confirmed Linux 0.2.7 appearance and behavior are good.
- Checks: 27 desktop Python tests, 24 GTK layouts (100–250%), coherent initial state,
  unchanged/stale polling, action independence and confirmation cancellation. GTK 4.8 /
  libadwaita 1.2 compatibility verified locally. Windows CI passed broker/UI/layout
  checks; all client jobs and phase0 passed.
- Linux prerequisites: Python GI, GTK >=4.8, libadwaita >=1.2, cryptography and
  NetworkManager. Ubuntu/Debian packages: `python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
  python3-cryptography`. Already present on this laptop; no system packages changed.
  Other hosts must install prerequisites before updating; failed smoke retains old app.
- Catalog `updates/pilot.json`: sequence 7, version 0.2.8, 90-day validity. HTTPS
  downloads, Ed25519 verification, user-confirmed installation. Reticulum delivery
  remains planned. Private signing key stays local under
  `state-client-build/update-signing/ed25519.key` and is never committed.
- Intermediate 0.2.4 release remains immutable without a signed catalog; later versions
  supersede it. Do not overwrite published binaries/tags.
- Server `185.251.89.19:/opt/apps/family_connect`: product API schema 3, localhost
  `127.0.0.1:18082`, gateway/worker/timer deployed in 0.2.1, three legacy peers preserved.
  Backup `/opt/backups/family-connect/20260910-110930`; rollback gateway image
  `family-connect-wireguard:rollback-20260910-110930`. No server changes for this release.
- Live product smoke passed on 2026-09-10: HTTP enrollment/replay rejection, staging,
  periodic worker install/persistence, revision 1 publish/fetch and local signature/decryption
  verification, revoke and rejection of an outstanding fetch proof, periodic worker removal.
  All three legacy peers and allowed IPs unchanged. Test device/entitlement revoked;
  audit and address reservation retained. No real client handshake/runtime apply tested.
  See [live report](live-product-smoke.ru.md) and [result](live-product-smoke-result.json).
- Pending: runtime provisioning/ACK and public HTTPS ingress, Reticulum update delivery,
  native invitation/storage flows; physical Windows/Android connection checks.

[Release](https://github.com/Joker20380/family_connect/releases/tag/v0.2.8)
· [Client CI](https://github.com/Joker20380/family_connect/actions/runs/34522112485)
· [Phase0 CI](https://github.com/Joker20380/family_connect/actions/runs/34522112544)
· [Release report](releases/0.2.8.ru.md) · [Plan](PLAN.md)

Temporary icon: `clients/assets/dodecahedron.svg`; regenerate PNG/ICO/embedded icon
with `python scripts/generate_app_icon.py` (Pillow). Final icon design deferred.
