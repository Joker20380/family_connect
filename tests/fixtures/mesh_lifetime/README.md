# L02.1 isolated authenticated lifetime gate

This is a **test-only source overlay**, never an installer or production worker.
Build with `build.py --go /path/to/go --xray /path/to/pinned-xray --out /fresh/path`.
The ordinary build script, product command line, endpoints, trust anchors and
Android106/reference pins are unchanged. Xray uses the same pinned revision/patch.
The fixture binary is race-instrumented; do not install, sign or distribute it.

Run `clients/desktop/tests/test_mesh_chat_lifetime_native.py` as root in a disposable
network namespace/container with loopback up, an up non-loopback interface, IPv4
address and default route (no external connectivity is required). Set
`FC_L021_WORKER` to the fixture binary. The CI workflow contains the exact recipe.
Optional `FC_L021_SERVICE_SOURCE` loads an observed old ServiceOwner source for a
red run; it is only consumed by the test. Current production code never reads it.
Also run `clients/desktop/tests/test_mesh_chat_terminal_native.py` for L02.1-R.
The fixture-only acknowledged bootstrap barrier can return an opening error, and
the peer control barrier can close the authenticated peer Mux. Neither failure
uses the Python owner's cancellation event. Native terminal/drained observations,
lease accounting and transport-open counts distinguish a dead generation from
an idle process. The IPC-boundary tests hold acquisition before dispatch and hold
late acquisition/HTTP results after native completion; cleanup remains explicit.

## What is real

ServiceOwner, ServiceHost, Binding, private native AF_UNIX/stdio IPC, MaterialOwner
native validation and durable cache readback, root flock/inherited admission,
restrictedchat Owner/Coordinator, FamilyTLS/ReliableStream/Mux and Session.Close
are real. A disposable authority issues device/gateway certificates, delegation
and CRL via the existing public authority fixture. The HTTP peer runs ChatAccess
challenge/register including device/chat proofs and revocation rejection. The
fixed mailbox stream exchanges bytes in both directions; it is not an LXMF/node
enrollment or installed messenger acceptance. Underlying reads real isolated
kernel routes. No TUN is created in this service-only gate.

## Exactly what is replaced

- External provisioning refresh is replaced by a pre-issued cache in cooldown;
  the fixture-only MaterialOwner subclass requests the normal cached path. Native
  signature/certificate/CRL/expiry validation and inspect/readback are not replaced.
- `wholedevice.openDirectory` is overlaid with paired bounded packet channels:
  external bootstrap rendezvous, Telemost signaling/ICE/VP8/RTP carrier, room-broker
  binding and remote lease maintenance are not exercised. FamilyTLS/Mux still run
  on both endpoints, using the verified client profile and issued gateway profile.
- The two fixed services terminate at loopback peers. API TLS uses the fixed product
  origin and an ephemeral matching certificate; `SSL_CERT_FILE` is added only to
  the fixture subprocess environment, not production `ENV` or product roots.
- The overlay observes actual native active lease counts, transport opens,
  authentication and cleanup using acknowledged loopback event barriers. Cleanup
  is held explicitly, not with a scheduling sleep. No PID-only success criterion.

## Remaining combined interface

This peer implements only fixed chat API/mailbox policy. It does not implement
the generic packet/DNS path needed by native `platform.Attach` / owned-TUN
`platform.Probe` and health checks. Consequently Linux Supervisor publication,
verified-profile EXISTING_EXIT borrowing and OFF→ON→OFF are **NOT_RUN**, not PASS.
Extend the isolated peer to serve that packet/DNS path and broker lease lifecycle,
then drive the actual Linux VPN owner. Do not stub publication, Attach or Probe,
or infer this gate needs production/live access or a private capsule.

The candidate public components were inspected: `telemost/local_process_test.go`
has real two-process Pion SDP/media but no FamilyTLS/owner; `messenger_local_test.go`
has local Pion+FamilyTLS+Mux but exports a TCP proxy rather than native acquisition;
`familysession/session_test.go` provides paired authenticated endpoints;
`roombroker/lease_mux_test.go` covers broker clocks/renewals but not Linux owners.
None alone closes the combined gate. This fixture uses the authenticated-pair
pattern without importing private state or changing the accepted coordinator's
refcount semantics. L02.1-R adds a separate `RetainChat` operation: under the same
coordinator lock it retains only the specified live generation, never bootstraps.
