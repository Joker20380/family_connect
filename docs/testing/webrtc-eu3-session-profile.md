# 5N.3 isolated session selection (not production provisioning)

The frozen gate is authenticated Family E2E, not a third plaintext echo. The
5N.2 CLI cannot meet it. The smallest implementation candidate is Go's existing
standard `crypto/tls` TLS 1.3 over the carrier byte contract, with mutual X.509
certificates and explicit Family admission. No new signaling/crypto handshake,
library, transport manager, mux, TCP destination or TUN is selected here.

## Pre-implementation reuse/security review

TLS 1.3 (RFC8446) supplies fresh transcript challenges, CertificateVerify proof,
ephemeral session keys, record integrity and replay/order rejection. Go1.27.1
`crypto/tls` supports `RequireAndVerifyClientCert`, normal chain verification
followed by `VerifyConnection`, and disabling tickets. Use TLS1.3 only, an
explicit versioned ALPN, no resumption/0-RTT, no insecure verification callback,
and no plaintext fallback. A malformed/reordered/lost record terminates or times
out the session; there is no application retransmission or auto-replay.

The existing carrier is message-oriented and lossy. A bounded pipe adapter can
present its ordered successful messages as a stream; it cannot add reliability.
TLS is therefore suitable for this fail-closed correctness experiment, not yet a
decision that lossy VP8 supports a production reliable mux. Carrier frames,
pacing, fragment limits and signaling stay unchanged. Network fault tests must
show termination and an explicitly new session, never reuse of an old TLS state.

Device Identity is the existing RNS-compatible public X25519+Ed25519 pair, with
SHA256(public pair)[:16] reference. TLS uses its existing Ed25519 signing key;
the independent WireGuard key is not a TLS key. Both identity halves and role/
family/revision must be covered by an authority signature and the TLS transcript.
The client pins the gateway identity in addition to normal certificate validation.

Do not confuse an arbitrary test CA/allowlist with existing FAMILY authority.
An isolated acceptance issuer must enroll disposable DeviceIdentity instances
through **existing ProductStore challenge/enroll/authorization/revoke** against a
new private temporary DB, derive family/expiry/revision from that DB, and refuse
revoked/unknown identities. No production DB, enrollment, signing key or schema
may be read or changed. This tests those existing authority semantics but does
not establish production credential distribution, secure-store migration,
instant offline revocation or Device Core integration.

Required before claiming PASS: verified issuer-to-runtime binding, current signed
revocation/expiry/revision enforcement, valid and negative live auth cases, replay
tests, same canonical echo matrix and >=300s sustained on physical Android through
Telemost VP8 to Amsterdam, plus lifecycle/network/static checks. Local mocks or
a newly invented credential database do not close the gate.

## Dependencies / limitations

`crypto/tls`, `crypto/x509`, Ed25519 and the pipe adapter use the already pinned Go
toolchain (BSD-3-Clause notice already retained). The acceptance issuer uses the
existing identity/control lockfiles and cryptography X.509 APIs. No module pin
change or borrowed implementation is necessary. This is a focused source/API and
trust-boundary review, **not an independent cryptographic/security audit** or a
claim of Telemost privacy/security. Platform/live checks remain necessary.
