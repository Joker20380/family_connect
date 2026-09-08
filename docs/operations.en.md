# Operations

[Русский](operations.ru.md) · [Guide](../README.en.md)

## Deployment

The server is `185.251.89.19`; the working deployment directory is
`/opt/apps/family_connect`. Run commands from this directory. Existing MicroTrader services
are a different project and must not be restarted or removed by these commands.

```sh
docker compose build
sudo ./scripts/provision.sh
docker compose up -d control gateway relay-a relay-b
docker compose ps
curl -fsS http://127.0.0.1:18080/healthz
```

Provisioning uses `state-v2/`, preserving older `state/` keys. Keys are generated once; repeat
provisioning reuses them and does not silently re-enroll revoked devices. The lab CSR issuer
currently provisions gateway-lab, relay-a, relay-b, client and an unlisted outsider test device.
The host administrator simulates their separate storage; real device-side key generation and
public enrollment are not yet integrated into mobile applications.

Gateway and relay endpoint IPs are signed lab configuration on `172.29.92.0/24`.
The control plane is `172.29.92.2:8080` inside that network and also has a management network
for its host-loopback port. Data-plane ports are not published to the Internet.

Remote API inspection:

```sh
ssh -L 18080:127.0.0.1:18080 root@185.251.89.19
curl http://127.0.0.1:18080/v1/network-state
```

Do not expose this lab publicly. It has neither public enrollment nor production abuse handling.

## Files and trust

| Directory | Contents / allowed reader |
|---|---|
| `state-v2/authority` | CA private key; provisioning administrator only |
| `state-v2/control` | Ed25519 signer and membership catalog; control service/operator |
| `state-v2/trust` | Public CA and pinned Ed25519 root; all nodes |
| `state-v2/<role>` | Role's own private key, public CSR, certificate, stable identity |
| `state-v2/cache-<role>` | Signed cache and rollback high-water mark; owning role |

Runtime core UID is 65532. Each core service mounts only its own identity directory, public
trust and own writable cache. The control service does not mount device or gateway private
keys. Keep all `state*` directories out of Git, container build context and support attachments.
Public CSR/certificates may be transferred for issuance; private device keys must not be sent.

## Membership changes

An administrator runs the local tool with narrowly scoped mounts. Example from the server:

```sh
docker run --rm --network none \
  -v "$PWD/state-v2/control:/state:rw" \
  -v "$PWD/state-v2/client/cert.der:/device.der:ro" \
  -v "$PWD/state-v2/trust/ca.der:/ca.der:ro" \
  family-connect-control:auth2 python scripts/admin.py revoke \
  --certificate /device.der --ca /ca.der
```

Use `enroll` in place of `revoke` to restore this lab device. Each change creates a new epoch;
do not restore an older network.json to reverse a revocation. Do not manually edit membership
without incrementing epoch. There is no remote administrative HTTP endpoint.

## Failure behavior

- Backend outage: verified cached state remains usable until signed expiry, normally 15 minutes.
- Expired state: no new connections; active sessions close.
- Wrong root, tampered or rolled-back update: reject it; retain a still-valid trusted cache.
- Corrupted on-disk cache: startup fails closed. Investigate; do not automatically delete the
  rollback floor to make the error disappear.
- Certificate expiry: mTLS connections fail; rotation is not automated in this increment.
- Gateway failure: test transfer fails; existing Internet-flow migration is not implemented.

Bootstrap URLs are configured with `BOOTSTRAP_URLS` as a comma-separated list. Each delivery
source must return the same signed envelope format. The signing public key comes only from
trusted provisioning. Multiple URLs on one server are not independent failure domains.

## Routine inspection

```sh
docker compose logs --tail 50 control gateway relay-a relay-b
./scripts/test_auth.sh
```

Logs contain operational events, not payloads or browsing history. Test artifacts contain
synthetic transfer checksums and timing; do not interpret them as anonymized production telemetry.
[Full fault tests](testing.en.md) deliberately stop services/revoke the synthetic client and
restore them afterward. Run them only on this lab.
