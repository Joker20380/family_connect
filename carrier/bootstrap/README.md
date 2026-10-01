# 5N-BOOT-1: cached restricted rendezvous

Implementation and deterministic checks do not establish physical acceptance.
**30 September: isolated physical BOOT-1 PASS**, cached-state Redmi cellular →
real Telemost bootstrap → separate dedicated DNS/HTTPS; no forwarding/manual URL.
See the [dated report](../../docs/releases/2026-09-30-webrtc-5n-boot1-bootstrap.ru.md).
No production deployment, client version change or full-device integration.

## Boundaries and trust

`directory.go`: strict version-1 JSON directory, Family binding, issued/expiry
times, 1–4 seeds (`transport`, `join_url`, expected gateway identity). Only exact
Telemost HTTPS `/j/` URLs; no query, fragment, userinfo, alternative port or host.
8 KiB maximum; maximum age/lifetime one hour; no future issuance. Credentials,
private keys, provider OAuth and dedicated descriptors are not directory fields.
Duplicates, unknown fields, stale/equal conflicting replacements are rejected.

Timestamp contract (5N-TIME-COMPAT): absolute RFC3339 instants, accepting uppercase
`T`/`Z` or numeric `±HH:MM` offsets. Canonical Family Connect directory JSON uses
UTC with trailing `Z`; offsets are converted arithmetically, never relabeled.
The shared Go/Python wire profile supports optional1–9 fractional digits
(nanoseconds), clock hours00–23, minutes/seconds00–59, and valid calendar dates;
naive timestamps, malformed offsets, leap seconds, extra precision and junk fail
closed. Expiry is exclusive, future issuance forbidden, lifetime≤1h unchanged.
Python compares exact UTC nanoseconds rather than truncating fractions to seconds
or microseconds; integer readiness envelope expiry remains conservative seconds.
Go seed publication explicitly converts the inherited context deadline to UTC,
and every `Directory` JSON serializer canonicalizes both timestamps. Python
delivery emits normalized UTC timestamps; sync/cache may preserve authenticated
input bytes rather than silently rewriting a snapshot. No standalone directory
signature/MAC binds a timestamp spelling. Issuer signatures/X509/CRLs are separate
and unchanged. Replay ordering uses instants; equal-issued changed content still
fails. Android additionally preserves its stricter equal-issued JSON equality
check; normalization occurs before new delivery, not inside the encrypted vault.
Shared fixture: `tests/vectors/bootstrap-timestamps.json` (repository root), with
the real failure's timestamps and synthetic Family/gateway/seed values only.

Attempt #4 clock-precision regression: a valid live seed can have fractional
`issued_at` within the receiver's current second. Python callers must not truncate
their current clock before comparing with that exact timestamp. Live validation
uses nanoseconds sampled after reading the bytes; there is no future-issuance
grace window and expiry stays exclusive. Producer and native validation are
unchanged. The synthetic `tests/vectors/bootstrap-live-issuance.json` preserves
the live field/value classes and precision. Tests exercise real `SeedManager`
publication → Go JSON serialization → isolated Python → native parsing and
synthetic signed Python delivery → Android's native `ValidateDelivery`.
The closed Python `directory-check` CLI persists bounded error categories before
exit; see the [operator contract](../../deploy/friends/restricted/README.md).

Delivery is `GET /v1/bootstrap/directory` on the existing Room Broker TLS1.3/mTLS
control trust model, using `RequestAuthorizer`, not the application update key or
a new signing root. The Android diagnostic native core obtains it directly while
ordinary control works. A protected cache uses mode0600, nonblocking cross-process
flock, one fixed staging file/write/fsync/rename/directory-fsync (a crash cannot
accumulate staging files). A corrupt/expired
cache is unusable; a rejected refresh preserves a valid cache. An identical
refresh is a no-op. Android supplies `getNoBackupFilesDir()`; backup is disabled.
File-system protection is the authenticity boundary after authenticated delivery;
the directory is **not independently signed** and not claimed confidential.

Already-provisioned devices must cache state **before** a restriction event.
Fresh install while completely restricted is out of scope. Expiry, changed trust
or loss of the sole seed fails closed; obtain a new directory through ordinary
authenticated control. No recovery from a stale seed, automatic transport policy,
multi-seed failover or persistent server restart recovery is claimed.

## Seed and carrier

`SeedManager` uses the existing `RoomProvider` once to create a separate seed,
then joins through the existing Telemost VP8 adapter. The directory is published
only after `Connect` returns READY, and withdrawn on failure/exit/expiry. This is
not a normal per-device ten-minute broker setup. One seed per process, no pool,
no provider retries, no promise to delete provider conferences on shutdown.

The existing adapter consumes SFU video slots, not authenticated per-device
connections. **A shared raw ReliableStream is unsafe.** BOOT-1 wraps carrier
packets in a small `FCB1` envelope: kind, random32-byte client exchange identifier,
random32-byte server lease identifier, payload. OPEN/ACCEPT select one lease;
lost OPEN is retried once per second within the admission deadline; ACCEPT
replies for that same lease are rate-limited to two per second, not new workers.
client/server DATA directions and both identifiers must match. This is routing,
not authentication or cryptography. Family TLS provides the security boundary.
No competing exchange is queued or started. Others boundedly observe
`seed_busy_or_unavailable` at admission timeout and may explicitly retry later.
No packet from a different lease enters the admitted byte stream. Malicious SFU
or participants can still deny service; confidentiality/integrity/authorization
do not rely on room secrecy. SFU slot selection can cause bounded failure, not a
claim of safe simultaneous multi-party service. Bootstrap-only track readers are
capped at four; normal dedicated carrier configuration is unchanged.

## Authenticated protocol and handoff

1. Lease → existing ReliableStream → existing Family TLS1.3 (no new stack).
2. `SessionAuthorizer` reuses the control authorizer with the original Family
   ALPN, certificate chain, role, Family, identity, revision, CRL and expiry checks.
3. Existing `Broker.Challenge` generates the one-use server setup ID, sent in
   `HELLO`. The client echoes exactly that ID in `REQUEST_TRANSPORT`.
4. Existing `Broker.Create` waits for dedicated gateway READY. `Claim` binds the
   same authenticated identity. Only then `TRANSPORT_READY` carries the descriptor.
5. Client `BYE`, server `BYE`, final client `BYE`; server permits up to3s final
   drain for ReliableStream retransmission. Failed exchanges return generic
   `ERROR` without provider details. A successful transfer closes bootstrap.
6. The existing diagnostic CLI joins the **different dedicated room**, calls
   `familysession.Open` and `roombroker.BindClient`, then the unchanged Mux proof.

The server creates no Mux on a bootstrap session. Raw Mux, TCP OPEN, DNS QUERY,
DATA, arbitrary proxy bytes, unexpected messages, oversized JSON and duplicate
REQUESTs fail closed. A duplicate/reconnected old setup ID cannot create another
room. No client-chosen idempotency key or unbounded replay tombstones are stored.

Failure before confirmed handoff cancels the setup through Broker semantics.
After descriptor delivery, a crashed client/failed dedicated join/admission is
bounded by the broker's unused60s expiry; bootstrap is already closed and does
not secretly call ordinary control to cancel. Once bound, normal dedicated
gateway/Mux cleanup applies. This deliberately favors bounded cleanup over
pretending that a disconnected receiver's delivery state is knowable.

## Limits

| Resource | Limit |
| --- | --- |
| Directory / seed count / validity | 8192 bytes / 4 (one published) / ≤1h |
| Active bootstrap exchanges | 1 per single seed/process; no pending queue |
| Bootstrap carrier connect / unauthenticated admission | 45s / 30s |
| Exchange / final BYE drain | 120s / ≤3s |
| Control request / READY reply | 256 bytes / 4096 bytes |
| Routing envelope / payload / inbound queue | 69 bytes / 33000 bytes / 16 packets |
| Bootstrap VP8 readers / cache-prep HTTP sockets | 4 / 8 |
| Provider / dedicated READY | 15s / 45s (existing broker) |
| Dedicated outstanding / per-device | 32 / 1 (existing broker) |
| Dedicated unused / lifetime / auth recheck | 60s / 10min / 1s |

Existing bounded Telemost reassembly and ReliableStream windows remain in force.
Revocation requires publication of the existing fresh signed CRL/profile; no new
instantaneous ProductStore-to-gateway revocation distribution is introduced.
One rejected or timed-out exchange does not spawn a competing exchange while its
worker is still exiting. Seed shutdown joins owned exchange workers.

## Isolated physical acceptance (PASS, 30 September)

Prerequisites: physical Redmi Note9 Pro/Android12/arm64, cellular ON/Wi-Fi OFF,
no active VPN, no existing diagnostic installation, disposable ProductStore
profiles, Linux bootstrap-broker binary and diagnostic APK built from this tree.
Only server/runner environment may contain `YANDEX_TELEMOST_OAUTH_TOKEN`.
Do not print environment, upload credentials to CI, use a live URL as an argument,
or use the historical Room Broker forwarding runner for this gate.

Build `./cmd/bootstrap-broker` with Go; use the existing
[Android build procedure](../../clients/android/telemost-runtime/README.md).
Generate disposable profiles with `python -m pilot.telemost_family_fixture --out`
pointing to a new private directory outside Git. Then run:

```sh
python pilot/android-telemost/bootstrap_acceptance.py \
  --adb "$ANDROID_HOME/platform-tools/adb" \
  --binary /tmp/fc-bootstrap-broker --apk /tmp/fc-bootstrap-diagnostic.apk \
  --family-dir /tmp/fc-bootstrap-profiles --out /tmp/fc-bootstrap-evidence
```

The runner uses only authorized Amsterdam `186.246.45.246`, task-owned `/tmp`
processes and a temporary mTLS listener on port18444 (override `--port` if needed).
It does not change firewalls, systemd, product databases or production services.
SSH carries server setup/evidence only, **no forwarding flags**. Android's prep
HTTP goes directly over cellular to that listener. If inaccessible, stop; do not
substitute adb reverse, SSH control ingress or paste a room URL.

Phase A: automatic seed READY → authenticated directory fetch/cache → successful
diagnostic process exit → force-stop and check process absence. No room enters
Android/test inputs. Phase B: replace diagnostic ordinary control endpoint with
`https://127.0.0.1:1`; the core explicitly proves `control_unavailable` before
loading cached state. No other normal endpoint is configured for recovery.
Phase C: cached seed → real Telemost → Family TLS → broker request/descriptor.
Phase D: bootstrap closes, dedicated carrier/admission/setup binding follows.
Phase E: short existing public Mux A/AAAA/NXDOMAIN + four verified HTTPS200.

Runner evidence requires ordered events and process restart, never promotes
unit tests to live PASS, and only writes PASS after cleanup succeeds. Final gateway
evidence is read after shutdown and SSH/log closure: dedicated resource closure
may occur during that bounded shutdown, not immediately after Android exits. ADB is for
diagnostic installation/config/start/restart and bounded evidence; it is not a
transport. Set radios beforehand; the runner does not modify radio settings.
Cleanup stops the exact task-owned remote executable, removes its directory,
uninstalls the diagnostic app and waits for the SSH child. Preserve allowlisted
evidence, then remove task-owned disposable profiles/binaries/logs locally.

No TUN, orchestrator, second carrier, generic UDP, HA, stream migration, field
coverage, production capacity or beta rollout follows from this gate.
