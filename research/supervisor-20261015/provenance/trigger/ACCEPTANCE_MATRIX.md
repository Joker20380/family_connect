# Acceptance matrix and evidence semantics

The `sealed-*` receipts use fresh disposable local Family fixtures. Earlier `final-*`
receipts remain immutable: both unchanged baseline and candidate reached the short-lived
fixture's credential limit when advancing the test lease clock. They are infrastructure
headroom failures, not repaired product tests. The original one-hour fixture policy was
not extended. New local fixture identities were generated; production renewal count0.

| Requirement | Test/evidence | Result scope |
|---|---|---|
| Real upstream closure / native Gorilla1011 | TestAcceptanceRealGorillaBoundary; real-stack trigger receipt | Actual upstream socket closed first, actual close frame read by Gorilla; no constructed CloseError/classifier shortcut |
| Inactive behaviour | TestAcceptanceDisabledBoundary; three-way full-suite; inherited-file hashes | Same upstream pointer, no bridge/control by default; no policy/wire changes |
| Armed but unused | Five real JSON round trips; real media before command; TestAcceptanceUnusedExpiry | No fault, no busy polling, parent service context remains alive after control expiry |
| Invalid binding | TestAcceptanceRejectBindingAndState | hash/PID/startticks/InvocationID/generation/room/TTL/nonce/schema/state mismatch cannot consume |
| Actual stale command | acceptanceRealPion invalid generation before valid command | REJECTED and real seed classifier still empty; then one valid command |
| UID/filesystem | TestAcceptanceSocketPermissionsUnprivilegedAndCleanup; RootPolicyEntry | Kernel UID0 authorization, socket0600/private0700, actual root config entry under /run; bad modes/symlink/occupied socket rejected |
| Malformed/oversized | TestAcceptanceMalformedAndOversized | strict2048B JSON, duplicate/unknown/case-variant fields rejected |
| Helper crash/service stop | ConfigurationAndLifecycle/UnusedExpiry | Partial request bounded1s, stop removes listener, no command consumption; absolute enablement expiry |
| Restart/replay | binding PID/startticks, consumed latch, real-stack post-cleanup replay | Old exact command cannot target another process/generation; no autonomous command persisted |
| Persistent stream, old cache | TestAcceptanceRealPionContinuity×3 and root run | Real Pion/SDP/ICE/RTP/Family/Reliable/Mux/TCP, one socket/stream, unchanged D, new authenticated bootstrap→READY |
| Second generation | same real-stack fixture | First failure root-local control, second local provider close; two recoveries, one control consumption |
| Lease | real-stack lease-clock fixture plus baseline/candidate TestLease*×3 | Authenticated renewal and post-old-deadline data; accelerated lease clock only, not a live elapsed renewal claim |
| Stale cleanup/callback | same real-stack fixture and inherited supervisor matrix | Old seed cleanup cannot touch new generation/dedicated session |
| Write/unlink failure | TestAcceptanceRealPionReceiptFailure×3 | Directory0500 makes audit write and automatic socket unlink fail; protocol recovery/TCP/old-cache still pass; explicit local cleanup after restoring mode |
| Retention/privacy | StorageRetentionPrivacyAndFailure; structured allowlist scan | atomic link/no overwrite, max4096B,64 matching regular files by mtime,foreign files preserved,0600 |
| Terminal/security policy | inherited supervisor/security matrix×3 |1002/1008/malformed/UNKNOWN/security-expiry not expanded; bounded exhaustion/stop remain inherited |
| Resources | RESOURCE_FINAL in six race real-stack fixtures | old WS/PC/retained peers0 after cleanup; bounded FD/goroutine variation; no live rooms |
| Public absence | default binary strings and Go build inputs | command/config flag/socket marker absent, no remote listener, no fixture tags |
| API/AKI/skew/ACK/publisher | unchanged API archive + fresh pinned-reference regressions | Not packaged/replaced by this gateway candidate; preserved old-client contract and19 Store tests |

All negative commands are rejected before action. No outcome is inferred solely from
the helper reply. `CONSUMED` may have `action_applied=false` if natural closure won a
race; that invocation cannot retry. Accepted live evidence needs action, independent
reader1011, supervisor outcome and actual media/stream/old-cache receipts together.

The isolated local validation build includes only the previously accepted local-provider
test routing overlay, not in the frozen research executable. The same frozen research
binary is specified for future real-provider canary/deployment; that operational canary
is NOT_RUN here. Provider-generated1011 is NOT_PROVEN by this injected close experiment.
