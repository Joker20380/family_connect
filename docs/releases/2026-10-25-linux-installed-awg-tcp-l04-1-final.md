# L04.1-LIVE-2 — final installed E/F checkpoint,25.10.2026

**PARTIAL / review pending. E PASS; F1 PASS; F2 local contract PASS, full gate
not accepted because its first server continuity readback failed.** No new
architecture/task ID. R2 is DONE/review accepted in source/package scope.
P1/P2 and A/B1/B2/C1/C2/D remain accepted on exact .4 and were **not repeated**.
Parent L04.1 remains IN_PROGRESS. STOP. NEXT — final review L04.1.

[Sanitized evidence](evidence/l04-1-final-20261025.json).
[Accepted R2 source/package evidence](2026-10-25-linux-queued-connect-close-l04-1-live-2-r2.md).
[Historical .4 continuation](2026-10-25-linux-installed-awg-tcp-l04-1-live-2-continuation.md).

## Immutable candidate

Entry main `9e9bf16db397a0ce8cf0b559cbe8a7278c95aef9`.
Only the reviewed local **0.2.12~l03.2.5** was used; no rebuild, repack, installed
patch, source change, new product credentials, assignment or manual configuration
fetch. No public installer/catalog/policy or external server mutation was performed.

- Candidate `f0ee17609cfc8dbaf48edfa0f33b417754f9674d578168fa4cbb1c47d51d3f95`.
- Candidate source `1c2beb6bc687c94d2a9312da0545b6e985749752`.
- Unchanged system `8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d`.
- System source `053c4e5f9532ca927f49a78f9c0ed17903375baf`.
- Embedded system archive SHA256 `ddd74c2132a76ac833b587d9df6409d779ce6afcdaa45fafd23faa86d7817726`.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| FamilyConnect-0.2.12~l03.2.5-x86_64.AppImage | 57928184 | `dd013ce6be2a93be817b38aac9632e5b51b00419fbbc4da154d7e0b8b0f9db32` |
| FamilyConnect_0.2.12~l03.2.5_amd64.deb | 55987676 | `3b583fbdb69e726357d3b5d707629dd5dbe502078c1735cb9899de2dfb46d9ab` |

Exact artifact/member verification passed before use:707 user members, six legacy
members, matching candidate/system contracts. Installed inventory/import and
system READY checks passed; final guest artifact hashes remained exact. Historical
.4 and public assets were not touched. This is internal guest installation, not
workstation installation or public rollout. No release tag or version change.

## Environment and fixture boundary

New disposable Ubuntu24.04.5 KVM, kernel6.8.0-147, systemd255.4, QEMU7.2.22,
encrypted disks, ordinary UID1000, real TUN/NetworkManager/resolved/polkit,
GTK/libadwaita, private D-Bus/Secret Service and virtual display. No allow-all
polkit rule, installed-app GTK test override or fake backend success.

Only the already authorized protected test home was streamed into the guest;
operator material stayed outside it. Existing identity and signed nl assignment
were reused. Seven original protected files remained byte-identical. GUI setup
was explicitly confirmed and authenticated through the real pkexec dialog;
exact system READY followed with no VPN/TUN/owner. Each E/F scenario booted an
independent clean encrypted snapshot of this installed, disconnected baseline.

External instrumentation observed the installed App and its actual executors,
Future, callbacks and authorization requests. It activated the existing GTK
controls; it did not replace product methods or installed files. E alone used a
bounded Event on the original normal executor. No fixture cancellation occurred.
F2 launched the **original FUSE-mounted AppImage**, sharing the DEB-installed
system component and the same protected initial state. No AppImage close/reopen
positive gate, fresh-DNS repeat, upload, provisioning or reconnect loop was run.

Preparation-only fixture corrections occurred before any E/F Connect: debugger
thread scheduling/namespace handling and password-field text entry. The affected
unprivileged preparation process was discarded; setup completed after correcting
input in its existing dialog. No E/F user action was repeated. All scenario
processes started clean after these corrections; they are not evidence of a new
product defect or a waived product failure.

## E — queued Connect / Close: PASS

Exact DEB, normal Friends AWG selected. One Event occupied the single normal
worker. One Connect produced CONNECTING/busy and a queued, non-running Future;
helper requests0, owner/TUN0, generation0/pending null, no application journal.
One ordinary Close cancelled that Future **in product code**, closed the window,
set busy=false/action=None and advanced revision3→4.

After worker release, no Connect/backend/helper mutation ran. The cancelled
initialized callback executed without changing the closed GUI state or revision.
Network, settings and protected files were unchanged. Reopening the installed
application showed DISCONNECTED, generation0/pending null and no owner/TUN.
Three stable pre-action server observations and the post-read were identical.

This supersedes only the .4 E defect. Historical .4 evidence did not prove a late
VPN start: its cleanup fixture cancelled before releasing its worker.

## F1/F2 — Disconnect during bounded transfer

Each scenario used one normal Connect, verified actual transport owner/TUN and
HTTPS200 with expected egress, then one Disconnect while the bounded transfer
was running and had delivered bytes. F1 also verified the current AWG handshake;
F2 verified the installed Xray process. Normal helper import/up/down counts were
exactly1/1/1 per scenario; no second Disconnect or helper termination occurred.

| Observation | F1, exact DEB/AWG | F2, original AppImage/TCP |
| --- | ---: | ---: |
| Bytes received when Disconnect was clicked | 4096 | 8192 |
| Final bounded transfer bytes | 162279 | 90386 |
| Transfer exit | 28, timeout | 28, timeout |
| GUI terminal | DISCONNECTED | DISCONNECTED |
| Observed late poll/health completions, no CONNECTED | 18 | 49 |
| Final normal generation / pending | 3 / null | 3 / null |
| Application journal | IDLE | IDLE |
| Network/DNS/firewall baseline equality | PASS | PASS |
| Owner/TUN/transport workers after cleanup | 0/0/0 | 0/0/0 |
| Identity/cache/signed floors/settings preservation | PASS | PASS |
| Full scenario outcome | **PASS** | **PARTIAL: server readback limitation** |

Transfers were capped at60s, requested524288 bytes and rate-limited8192 bytes/s.
Both were incomplete at the bound after Disconnect. These are bounded terminal
timeouts, not throughput measurements or proof that the timeout itself has only
one possible cause. The process was running with received data at the single
Disconnect; cleanup and callback assertions were checked independently.

Normal catalog lookup started the existing shared catalog host once per F case.
This was not an Auto VPN connection: its read-only state was DISCONNECTED,
desired=false, selected empty, with no Auto/MESH owner. The idle catalog unit
remained after normal Disconnect and ended at VM shutdown; that shutdown is not
claimed as product transport cleanup. No journal/pending was manually cleared.
F2's intentional TCP selection precedes its settings baseline; subsequent
connection/disconnection preserved that baseline.

## F2 first server readback failure — retained, not waived

Three F2 pre-action reads were consistent; the last completed at20:57:29UTC.
TCP reached CONNECTED at20:58:27UTC. The single Disconnect was clicked at20:58:38
and the GUI reached DISCONNECTED at20:58:40. Local cleanup assertions passed.
The first post-action server read then failed its existing requirement that the
registry service be active/running. No next action, source correction or scenario
replay followed.

Read-only inspection subsequently showed a service transition: inactive from
20:58:36UTC, active again at20:58:49UTC, with a new invocation and Result=success.
The reason/initiator is **not established**; this checkpoint issued no server
mutation. A bounded unit-journal query timed out, and was not retried. This is an
observed server continuity failure, not a proven GUI/TCP product defect.

The later forensic read at21:00:40UTC verified the same registry archive, catalog,
device binding and assignment; test AWG row/live peer and persisted/runtime TCP
user remained1/1 and1/1. Foreign records, gateway configuration, network structure
and gateway service identities were unchanged. The **only changed comparison
field was registry.service_sha256**, reflecting the service instance transition.
This later observation does **not** replace the failed first readback or establish
uninterrupted server continuity. Full F2 and L04.1-LIVE-2 are therefore not marked
PASS/DONE. Review must decide the effect of this limitation; no automatic replay
or source correction is authorized.

Only read-only terminal observation and safe guest cleanup followed the failure.
TCP stayed disconnected through transfer termination and49 later poll callbacks;
all local resources and state checks stayed correct.

## Cleanup, validation and remaining gate

The guest is shut down; no VPN owner/TUN/transport worker remains. Disposable
encrypted scenario/base disks, disk key, guest access material, seed and raw
guest logs/screenshots are removed before committing this checkpoint. Original
protected test state and its future device-teardown receipt are preserved;
read-only preflight passes. No device revoke or gateway record deletion occurred.
Host routing/DNS/rules were unchanged in the final readback interval; no host
network/service configuration was modified during this task.

Only sanitized documentation/JSON is committed. JSON validation,408 document links
with no errors, secret/known-credential scan (including all-ref history), staged
five-file scope and whitespace checks PASS; public source guard2928/0 blocked.
The ordinary push is followed by remote main SHA verification. Product source is unchanged,
so broad product suites/CI are not rerun for this installed documentation-only QA.
R2's Linux/AWG/TCP/package CI PASS and full-suite54/54/54 failures (historical
Docker53) remain as recorded; there is no new general CI PASS claim and no changes
to voice/Windows observations.

No rollout/rollback is performed: failed continuity is retained for review,
private VM copies are discarded, and immutable candidate/public versions stay
unchanged. This report and its JSON are the one final receipt for this continuation;
the documentation commit/push identity is available in Git history.

**L04.1-LIVE-2 PARTIAL / review pending. L04.1 IN_PROGRESS.**
L04.2, L05, test-device teardown and publication remain **NOT_RUN**.
**STOP. NEXT — final review L04.1.**
