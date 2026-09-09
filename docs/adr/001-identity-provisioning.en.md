# ADR 001: reference identity and provisioning boundary

Date: 2026-09-09. Status: implemented reference experiment, not a production protocol freeze.

## Decision and implementation

Use the actual `rns==1.5.1` reference package for independent device identities and its public encryption/signature APIs. No network instance is started by these modules. WireGuard uses a separately generated X25519 private key. Existing P-256 laboratory identities, Windows activation trust and all VPN clients remain unchanged.

`device_identity/device.py` creates and reloads keys in a POSIX application directory: 0700 directory, 0600 files, same-user ownership, no symlink/hardlink keys, serialized initialization, fsynced atomic publication. A corrupt existing key or missing permanent identity with an existing transport key fails closed. Parent directories must be trusted. This is permission-protected Linux reference storage, not encrypted OS keychain integration; Android Keystore and Windows DPAPI integration remain required. Do not deploy this file store on other platforms or copy private material into server enrollment.

Ownership proof signs a domain-separated, deterministic JSON message containing the independent public Reticulum identity, public WireGuard key, 32-byte server challenge, fixed enrollment audience, schema and transport. The verifier proves identity ownership and key binding only. A future registration service must look up an unexpired challenge, atomically consume it, enforce membership/entitlement and install a peer. Repeating a cryptographically valid proof is not prevented by this stateless primitive. WireGuard key possession is separately established by WireGuard.

`provisioning/models.py` defines immutable, strict desired state with recipient identity hash, independent schema/revision, authorization lease, entitlement reference/revision, client public WG key, addresses/DNS and ordered gateway candidates with provider/region/optional ASN. Current schema supports WireGuard only. Credentials remain local; unknown fields, including private keys, are rejected. Candidate gateways must all have their peer/address assignment reconciled before publication.

`provisioning/envelope.py` encrypts model JSON through reference `Identity.encrypt`, then signs `family-connect/provisioning-envelope/v1\0` followed by exact ciphertext through the server identity's `sign`. The outer JSON contains only base64 ciphertext and signature. Verification uses an out-of-band pinned server public identity, checks signature before decryption, then checks strict schema, recipient, local public WG key, lease, revision and entitlement revision. Duplicate JSON fields and oversized envelopes are rejected. This is application framing around existing RNS cryptography, not a new cipher. It is independent of RNS links and HTTPS. Static identity encryption does not provide post-compromise protection for archived ciphertext; do not claim forward secrecy for this envelope.

`VerifiedProvisioningState` is the internal typed output, not an authorization boundary against malicious code already executing inside the process. Signer issuance remains an internal function, not a public endpoint. Server entitlement lookup, signing-key custody and authorization remain required before exposing issuance.

## Deliberately deferred

No account database, invitation API, challenge store, real HTTPS/RNS delivery, device UI integration, connectivity apply, runtime configuration builder or automatic failover is introduced by this commit. The verifier's revision floor must later come from protected durable state; it is not persisted here. It rejects revisions at or below the supplied floor. Cache revalidation, explicit rollback and known-good recovery need separate provider state-machine rules; callers must not lower the floor just to bypass replay checks. Expiry currently validates a maximum 24-hour reference lease; it does not control an active VPN.

Production signing keys belong on server infrastructure; clients pin only public anchors. This experiment has one explicit anchor and no trust-on-first-use. Planned bootstrap uses several operator-controlled paths and signed announcements; cached public destinations may aid discovery. Reticulum logical identity does not eliminate underlying Internet IP endpoints. Destination/anchor rotation needs a separate signed versioned manifest, overlap window and recovery policy; unavailable bootstrap must preserve already-authorized connectivity rather than create trust in an arbitrary responding peer. No shared consumer secret or GROUP identity will be used. Actual RNS link delivery and Android/Windows packaging remain unproven.

## Validation

Run `pip install -r control/requirements.lock -r device_identity/requirements.lock`, then `python -m pytest -q`. The complete Python suite passes: 75 tests. New cases include reference RNS key import/encryption interoperability, persistence, independent keys, tampered ownership proofs, unsafe/corrupt storage, concurrent creation, encrypted recipient-bound provisioning, wrong signer/decryption key, schema/private-key rejection, expiry, replay/downgrade and multiple providers. This is not a cross-platform VPN/network test or a live Reticulum delivery test.

## Primary references

* [Reticulum Identity API](https://reticulum.network/manual/reference.html): public identity import, sign/validate and encrypt/decrypt APIs.
* [Reticulum reference implementation](https://github.com/markqvist/Reticulum): interoperability source.

Next reviewable stage: transactional product registration/challenge consumption and entitlement storage, then the durable provisioning provider/HTTPS/cache path. Native integration follows platform storage and protocol fixture validation.
