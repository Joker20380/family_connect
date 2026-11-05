# MESH credential renewal — native boundary checkpoint / 5 November2026

## Result and scope

**SOURCE/TEST CHECKPOINT, NOT A DEPLOYED RENEWAL FIX.** Continuation of the selected
Android MESH incident after [118 field delivery](2026-11-05-android118-field.md).
The [overnight outage](2026-11-05-mesh-overnight-checks.md) attributes one dropped session
to scheduled maintenance stopping both gateways, not the earlier signaling/DNS failures.

This checkpoint proves the native rotation boundary with disposable Ed25519 certificates,
signed CRLs, Family TLS, lease-control streams and persistent TCP. Production source,
wire protocol, maintenance timers, policy and installed binaries are unchanged.
Android118 remains the opt-in field download/owner installation; default invitation/updater
113/catalog7, Linux0.2.11 and Windows0.2.16/catalog12 unchanged. Both NL nodes retain70e6c0fc;
no phone action, backend/MESH restart or private profile publication. Field acceptance OPEN.

## Confirmed implementation boundary

- `production_controller.py` labels scheduled leaf/CRL renewal `zero_downtime=False`,
  acquires/quiesces all nodes and requires all readers stopped before preparation.
  `production_node.py` relies on this invariant for grant planning, staging, publication
  and reconciliation. Removing stop calls or their guards is not a valid fix.
- `SessionAuthorizer` reloads the current profile and verifies the established peer against
  its authority/CRL/claims. Atomic same-holder successor publication can preserve authorized
  traffic before the original security deadline.
- `familysession.Open` captures the minimum local/peer leaf, signed CRL and authority
  expiry. `gateway.go` passes this fixed deadline to the lease handler. Longer-lived files
  do **not** authenticate a new peer certificate within an existing TLS session and must
  not silently extend that session's deadline.

## Added executable checks

`carrier/roombroker/credential_rotation_test.go` needs no environment fixture/provider.
Fresh disposable keys remain in memory/temporary0600 profiles. Existing ProductStore-backed
fixtures are preserved, sharing setup through `newLeaseMuxWithProfiles`.

1. Separate leaf-limited and CRL-limited cases establish Family TLS and one loopback TCP
   stream. Atomically replace the profile with signed same-holder successor leaves/CRL,
   read back exact bytes and reauthorize the original holder. A **new** Family handshake
   authenticates a different leaf serial with the same holder and a later deadline.
2. The **old** mux/TCP stream transfers exact bytes before/after two lease renewals, with
   only one accepted TCP socket. Its lease clips at the original security bound. Advancing
   the controlled lease clock expires ownership and closes the socket; neither the Family
   deadline nor the cryptographic verification clock is changed. Not a wall-clock soak.
3. A real newly signed CRL revokes the predecessor leaf between offer and renewal request.
   The held request is denied; sequence/deadline unchanged. This tests lease reauthorization,
   not immediate active-setup watcher latency.
4. Foreign authority, changed Family and unmet CRL floor each deny renewal without lease
   mutation or fallback to stale authorization.

At09:16UTC, Go1.26.1 `-race` results:

- `go test -race ./roombroker -run '^TestLeaseCredential' -count=20 -json`:
  **120 leaf-case executions PASS**,160 records including parents, zero skips/failures.
- `go test -race ./roombroker ./familysession ./tcpforward -count=1 -json`, with fresh
  disposable ProductStore profiles: **288 leaf cases PASS**,329 test records. Twenty
  root/canonical ownership cases skip on the non-root host; three optional performance/
  process-harness cases skip without dedicated inputs. Not a fresh root/performance PASS;
  unchanged production guards retain their separately recorded overnight evidence.
- `gofmt` and whitespace checks pass. Raw evidence remains under ignored
  `state-client-build/mesh-renewal-continuity-20261105/`; no keys/profiles in Git.

## Remaining implementation and completion gate

This is not seamless renewal. Remaining work within the same selected incident:

1. **Authenticated in-session successor transition.** Versioned bounded messages and a
   session-bound freshness proof for both peers, not a longer timeout. Validate same
   Family/device/gateway/key bindings, trust, monotonic revision/CRL and validity. Preserve
   the old hard deadline until both sides acknowledge the exact successor generation.
   Reject replay, another setup, partial/late ACK, expired/revoked predecessor and untrusted
   successor; serialize with traffic/expiry/cancellation. Unsupported118 peers retain their
   old bound. Authority changes require their separate existing gate.
2. **Coordinated live publication.** A separately validated online path is eligible only
   for compatible same-holder leaf/CRL refresh with unchanged grant/authority/revision
   bindings and no new revocation requiring denial. Preserve single-writer locking,
   per-node preparation/readback, durable decisions and crash reconciliation. Staggered
   restarts still kill users pinned to that node. Existing quiesced machinery remains for
   ineligible/emergency changes; no timer pause or expired-material rollback.
3. **Acceptance before activation.** Real Family/mux/DNS/TCP continuity across the old
   security deadline with authenticated successors; replay/revocation/corruption and
   crash-at-each-transition negatives; legacy118 compatibility; exact platform CI. Deliver
   the same accepted gateway build to both NL nodes and verify running hashes. Observe a
   scheduled renewal with traffic on both nodes, then physical lossy/screen-off and
   field-user allowlist checks. Do not infer these from the local harness.

Rollback: tests/shared test scaffolding/docs only; no deployed runtime to restore. A normal
follow-up source revert can remove the checkpoint without changing118 or catalogs. The
separate direct118 route rollback is in its delivery report. Source push is not deployment
or acceptance; remaining implementation, field evidence and CI outcomes stay explicit.
