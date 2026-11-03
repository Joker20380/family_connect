# Isolated AWG3.1 / REALITY data-plane canary

Opt-in native acceptance, not a production health observer or a client release gate.
It uses fresh disposable keys, three containers and two Docker `--internal` networks:
client ↔ gateway ↔ controlled DNS/HTTPS origin. The origin is not directly reachable
from the client. No public target, user profile, production registration, invitation,
paid/cohort mutation, host network/PID/mount, published port or service restart is used.

## Run

Linux Docker with `/dev/net/tun`, namespace-local NET_ADMIN and the existing local
images `family-connect-amneziawg:3.1-desktop`, `family-connect-xray:26.3.27-pilot1`,
`fc-fleet-bootstrap-2-operator:local` is required. The latter contains Python,
cryptography, curl, dig, iproute2, nft and CA tools. The build context contains only
the fixture source and Dockerfile, never repository state or profiles.

```sh
python3 scripts/test_fleet_canary.py --build --report /absolute/private/new-receipt.json
```

The report must not exist. Private0600 receipt records exact image/native source
bindings and sanitized outcomes, not keys, UUID credentials, raw stderr or traffic.
The image checks the already qualified AWG3.1 engine/CLI and Xray hashes at build
and each invocation. Source hash must match the running image: omitting `--build`
cannot silently qualify a stale fixture. Local base tags are not a fully pinned
reproducible release/CI supply chain; record the resulting image, never deploy it.

## Gates

- Read-only containers, all capabilities dropped except NET_BIND_SERVICE and
  NET_ADMIN for client/gateway; ephemeral `/run` and `/tmp`, no private host mounts.
- No direct route to the origin before or after the tunnel; no direct TCP fallback.
- REALITY wrong client identity and wrong server public key both rejected while
  the native client is running; valid credential must carry domain-based HTTPS.
- AWG wrong server public key rejected, then new handshake + nonzero receive/send
  counters + DNS through the interface + certificate-verified HTTPS through NAT.
- The origin echoes a fresh request nonce and observed gateway-side source address;
  a generic200, unrelated cached response or direct egress cannot pass.
- Origin sees exactly two application HTTPS requests (one per valid transport) and
  DNS queries. Local TLS1.3 origin has a disposable certificate explicitly trusted
  by this fixture, never `curl -k`; it is not a public PKI/Internet acceptance.
- Client child processes, interface and SOCKS listener are cleaned up; then all
  run-labelled containers/networks must disappear. Cleanup failure makes the run FAIL.

Every command is bounded, there is no repeating production timer. Keys stay in
container tmpfs and parent-process memory/stdin. TERM/ordinary exceptions enter
label-scoped cleanup; SIGKILL/host failure cannot guarantee it. For interrupted runs,
inspect only objects with label `family-connect.isolated-canary=<receipt.run_id>`;
remove exactly these verified owned objects. Never use global Docker prune. Images
remain for diagnosis. Retain failed receipts and use a new report path for each run.

## Limitations

This proves genuine native protocols and DNS/HTTPS/forwarding inside one isolated
workstation topology. It does not prove Amsterdam1/2 availability, public routing,
provider NAT/firewall behavior, client GTK/Android/Windows lifecycle, MESH, independent
failure domains or automatic recovery. It is never imported as production readiness.
Production per-node canaries need dedicated test-only credentials with bounded
registration/revocation and conservation of all existing users; do not reuse a retired
probe identity, an owner profile or production server private material.
