# Automatic Telemost Room Broker — isolated 5N-RB-1 control plane

`RoomProvider.CreateRoom(ctx)` is independent of Family sessions. The only
provider implementation is `TelemostRoomProvider`: one official PUBLIC conference
creation per accepted setup, without application retries, pools or reuse.
`YANDEX_TELEMOST_OAUTH_TOKEN` is read server-side from the environment only.
Never pass it to the Android build, APK, descriptor, logging or a committed file.

## Integration and identity

The existing `familysession.Configuration` verifies the authority, current signed
CRL, Family, revision, certificate lifetime, device role and identity key binding.
The control adapter uses those admission checks over TLS 1.3 HTTP/1.1 rather than
the data-plane ALPN. It explicitly checks HTTP/1.1 before adapting the protocol
field passed to the existing Family claim verifier; it does not disable chain,
hostname, gateway pin, role, expiry or revocation validation. TLS tickets and
resumption remain disabled. Gateway profiles are reloaded per handshake/request
and once per second while a setup is retained. Revocations must be published in
that signed profile: this is not a new ProductStore watcher or production issuer.

The isolated issuer `pilot.telemost_family_fixture` already enrolls and authorizes
identities through ProductStore. This task reuses its profiles, not an independent
identity database. Existing Python `/v2/provisioning` and deployed services are
unchanged. `cmd/room-broker` is an opt-in control facade colocated with the existing
Amsterdam carrier, not a new production deployment or transport orchestrator.

All endpoints are POST JSON and require admitted device mTLS:

- `/v1/rooms/challenge`: reserve a random 256-bit setup authorization for this
  Family/device. Body `{"setup_id":""}`; response contains `setup_id` only.
- `/v1/rooms/create`: consume that authorization once. Replays conflict, with no
  extra provider request. The synchronous response contains a descriptor only
  after the gateway's existing `telemost.Session.Connect` succeeds.
- `/v1/rooms/claim`: consume the device-bound descriptor once before joining.
- `/v1/rooms/cancel`: cancel only this device's setup and close its gateway.

Other bodies use `{"setup_id":"<authorization>"}`. The descriptor contains only
`transport`, `setup_id`, `join_url`, `expires_at`. Keep it private and ephemeral.
HTTP responses disable caching; routine events contain no device/room identifiers.

After existing Family TLS admission, a small adapter sends a fresh 32-byte
challenge inside that encrypted session. The Android device signs the
purpose-separated setup ID and challenge using its existing Ed25519 identity key.
The gateway verifies the key authenticated on the control request before enabling
Mux. This binds a fresh carrier to the requesting device/setup without changing
Family TLS, ReliableStream, VP8, Mux, DNS or TCP. Old proofs, another setup ID or
another device key cannot activate the setup. No new cipher or key exchange exists.

## Lifecycle and bounds

`AUTHORIZED → CREATING → CREATED → GATEWAY_JOINING → READY → CLIENT_ISSUED →
ACTIVE → CLOSED`; terminal alternatives are FAILED, EXPIRED, CANCELLED.
Creation: **15s**, gateway READY: **45s**, unused authorization/descriptor: **60s**,
maximum setup/session lifetime: **10min**. A descriptor claim does not extend the
unused timeout; only successful bound Family admission activates it. Maximum
**one outstanding per Family/device, 32 globally**, including reservations and
active sessions. Provider responses are bounded to16KiB, control bodies256B,
descriptor responses4KiB. The standalone process also has a hard lifetime.

Terminal events/reasons are emitted, then retained state is removed after gateway
cleanup. No permanent tombstones are necessary: an unknown old random ID cannot
start a new setup. Cancellation propagates to HTTP creation, signaling and the
carrier. Broker shutdown waits for owned work. No Telemost delete API is invented:
expiry means Family Connect stops using/accepting the descriptor, not that the
provider removes its conference object. Rapid sequential authorized setups are
not governed by a long-term quota in this MVP.

BOOT-1 uses `ChallengeAfterCleanup` for an already authenticated exchange: an active
or started terminal setup for the same Family/device/key is allowed to finish its
normal cleanup before another challenge is requested. The wait ends only after
gateway close and slot removal, and never evicts the old session. It is bounded by
the caller's context (BOOT-1 retains its120s total budget), with authorization and
identity rechecks at the existing interval. Pending non-active setup duplicates
still fail immediately. HTTP `Challenge` remains immediate, and single-device,
global outstanding, replay and authorization guards remain unchanged.

## Isolated use

Run `cmd/room-broker --family-config <private-gateway-profile>` on the gateway.
It listens on loopback by default and refuses non-loopback listeners. An explicit
authenticated ingress is required; the short test runner uses SSH port forwarding
and `adb reverse`. That proves physical Android-originated mTLS requests, not
production bootstrap reachability from a restricted cellular network.

Diagnostic Android reads a private `files/broker.input` control endpoint and
`files/family.input` profile plus the existing `files/mux.input` public smoke
configuration. It must receive **no** manual `room.input`. The shared native CLI
uses `--broker-url`; the broker endpoint is not a Telemost join URL. The legacy
`FC_TELEMOST_ROOM`/`room.input` path remains an explicit diagnostic override and
cannot be combined with automatic mode.

Focused checks:

```sh
FC_FAMILY_TEST_FIXTURES=/private/disposable-family go test -race ./roombroker ./familysession ./telemost ./cmd/telemost-binary
go vet ./roombroker ./cmd/room-broker ./cmd/telemost-binary
```

The ProductStore-backed control/binding tests explicitly skip without fixtures;
acceptance must provide them. Provider tests use only fake credentials and local
HTTP mocks. No performance sweep is part of this gate.

See [the report](../../docs/releases/2026-09-28-webrtc-5n-room-broker.ru.md) for the
actual live verdict, source/artifact provenance, cleanup and limits. No TUN, generic
UDP, room pooling, HA, provider-account rotation, seamless migration or load claim.
