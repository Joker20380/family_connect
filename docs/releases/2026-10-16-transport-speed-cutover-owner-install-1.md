# TRANSPORT-SPEED-CUTOVER-OWNER-INSTALL-1

**RESULT: OWNER_INSTALLED_GATEWAY_DEPLOYED_READINESS_PASS_BOUNDED.**
The owner confirmed readiness after the VPN-OFF/USB request and the warning about
the required restricted-session interruption. The already tested combined candidate
is signed, installed on the owner phone, and deployed on the NL gateway. VPN ends OFF.
No new CONNECT, speed test, call-continuity acceptance or public release is claimed.

Input review: `bc1df88a848e623b8ad2d90dd17ad5eef7a027aa`.
[Existing local checks and behavior limits](2026-10-16-transport-speed-cutover-candidate-1.md),
[safe selected receipts](evidence/2026-10-16-transport-speed-cutover-owner-install-1.json).
The source inventories, publication commit and binary hashes are different identities.

## Installed pair

| Identity | SHA256 / value |
|---|---|
| Version / code | `0.1.18-research84-ui60-4-speed-recovery1` /84 |
| Tested unsigned APK | `2cf26421b67e536b5c178af7020cade9b499fec06822c82b713461cf534f5ac1` |
| Signed AND installed APK | `28543d4690327e29a6eb6a60e52fa50232a407663ed7e610f1434cd56f86193d` |
| Embedded native | `f25124ba1c94a0c6f4258e8b67488e8febf9a1c9e88cb2073790564c3a1f4729` |
| Client cumulative inventory | `211b127d545af5c129acc93bf0ff78cac3af93707aad8def27bb6da830e2ae86` |
| Configured AND loaded gateway | `5de40b9ce9c15aac85475df05c449bddf2ecfe61a1928fa3844b4a8446b33047` |
| Gateway carrier inventory | `3693f70552d27365a56eb9f625f8afe03c01f7e513acdc04cb31e107f52d837e` |
| Package | `com.familyconnect.app.friends` |
| Existing signer | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |

No product source or build changed in this installation continuation. Native bytes
intentionally differ from UI60-4 because they include the already tested transport
engine change. The UI60-4 layout, security boundaries and configured timeouts remain
as documented in the candidate report; retry behavior is not called unchanged.

## Phone: one compatible replacement

Fresh metadata confirmed the expected UI60-4 APK, code84, actual UID10283, API31 and
ARM64. Both VPN network and VPN service were absent. The actual installed signed APK
was pulled and checked before replacement:
`1bf56c381e76913d77c4dc518961020d82d2bfec33da69777a504b7569be15ef`,
native `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2`.
It remains a private same-package/signer/code84 backup, not an executed rollback.
Storage sources have no migration delta. No downgrade bypass, uninstall or data/cache
clear is used; private identity/database contents are not read.

The existing vault/memfd workflow signs the exact unsigned artifact once at21:35:11UTC.
Signature, package/version, non-debuggable state,16K alignment and embedded native pass.
Every unsigned non-META-INF entry remains identical after signing. Installed DEX/native
payload matches the signed artifact after pulling it back. The signed hash is distinct
from both the unsigned artifact and previous installed APK.

Ordinary `install -r` succeeds at21:36:18.766UTC; readback21:36:19.442UTC confirms
the exact installed hash and unchanged UID/signer. Ordinary launch21:36:22.736UTC
creates PID24627. The bounded UID-filtered startup error sample contains no new
AndroidRuntime/linker/libc error lines; this is not a long-running crash/ANR guarantee.
Final metadata21:40:28UTC: same APK/UID/PID, VPN transport and VPN service absent.
Data preservation is supported by ordinary replacement, unchanged storage code and
package/signer/UID; no private-database content comparison is claimed.

## Gateway: existing coordination, one transition

Direct local→RU SSH failed during banner exchange, and the first read-only collector
timed out without output. Access through the authorized NL SSH ProxyJump succeeded;
no key was copied or forwarding/auth policy changed.

The prior21:33 scheduled invocation had already returned `FAIL_CLOSED`, cause
`REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED`, automatic_retry=false and alert delivery
UNAVAILABLE. This predates the candidate. Fresh durable readback found COMMITTED,
no node owners and no active writer. Existing read-only evaluate at21:38:11UTC returned
NOOP, due=[]/alerts=[], zero changed files/writes/restarts. This is not a renewal and
does not erase the failed scheduled result. The timer remains active and unchanged;
the failed service status is deliberately not reset.

Pretransition runtime: PID716284 / invocation `999c9d2561d545ce80d4b7436da3f7c1`;
configured and loaded SHA `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f`.
That exact executable is saved and rehashed on NL, not the obsolete21f0a0fd binary.
Candidate transfer hash is independently verified. Restricted session count is UNKNOWN;
the authorized interruption loses previous in-memory holders and is not a continuation
of any historical A/B request.

Existing RU coordinator/node and NL node locks protect the transition. No scheduler
stop, parallel writer, management deployment, unit/argv edit, observer activation or
credential/floor/directory rollback occurs. The replacement retains owner/group/0750;
file fsync, atomic rename and directory fsync precede the ordinary service start.

| Event,16Oct2026 | UTC |
|---|---|
| Durable transition intent |21:39:17.775373 |
| Stop completed, exit0 / PID0 |21:39:17.900220 |
| Atomic binary replacement |21:39:17.936790 |
| Start completed, exit0 |21:39:17.996531 |
| New loaded executable verified |21:39:18.055155 |
| Seed READY in new invocation |21:39:20.693753 |
| New directory confirmed on RU |21:40:25–21:40:27 |

New PID746768 / invocation `843cf76698cd472995fbc6024dfa0b6c`, NRestarts0.
Listener and strict served TLS/hostname/expected leaf pass. The new directory is
issued21:39:20.690477UTC, after this start; its hash on NL/RU becomes identical:
`8c89debec9d8e682875a7a40cc10d4b07d3bfd141dff7f0553403a7d3cac5700`.
The first RU read still had the previous directory and was recorded as publication
pending, not PASS. Existing directory-sync completed at21:40:09UTC; one later bounded
read verified publication, without a manual publish or another restart.

Final receipts21:40:23–21:40:27UTC confirm active/running, exact new loaded/configured
bytes, same unit/argv, unchanged profile/CRL/authority, no owner markers or writer,
COMMITTED transaction and matching runtime-bound directory. Posttransition evaluate
21:39:41UTC is also NOOP with zero writes/restarts. These are point readbacks and seed
evidence, not a repeated server stability/load suite or Android TUN traffic test.

## Actual bounds and remaining checks

| Boundary | UTC |
|---|---|
| Existing authority/delegation expiry |2026-10-17 13:10:22 |
| Current leaf expiry, limiting checked material |2026-10-17 00:18:20 |
| Current CRL expiry |2026-10-17 00:48:26 |
| New runtime/directory bound |2026-10-17 approximately01:39:18 |
| Next scheduled run, timer estimate at final read |2026-10-16 21:48:30.833 |
| Existing six-hour operator threshold |2026-10-17 07:10:22 |

Future scheduling/renewal is not counted as performed; checked material bounds exclude
uninspected client grants. No new authorization or security policy is introduced.

Counts: signing1; ordinary replace-install1; ordinary app launch1; gateway binary
replacement1; gateway stop/start1 each; rollback0; CONNECT0; export0; rebuild0;
new test-suite runs0; emulator0; credential renewal/recovery0; unit/argv edits0;
manual directory publication0; additional native stats readers0; public APK/binary
publication0. There are29 bounded SSH command attempts and one SCP artifact transfer,
including the two unsuccessful direct-RU observations.

Both optimizations are now installed, including the gateway downlink sender. Actual
phone throughput improvement and recovery through a later scheduled cutover remain
unmeasured. No claim that every ten-minute disconnect is fixed. Saved artifacts allow
a separately authorized compatible client replacement or binary-only gateway return;
neither procedure was performed, and old credentials/floors must not be restored.

The prior exact-pair reconnect PASS and historical failures remain unchanged. Field,
chat handoff, supervisor, historical causality and public release stay open. The phone
is left on this private candidate with VPN OFF; no owner/tester CONNECT is automated.
