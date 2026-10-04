# Four-hour restricted readiness — local candidate, 2026-10-04

Follow-up: [beta62 source candidate](2026-10-04-beta62-recovery-candidate.md) now has
distinct62 version metadata and the connected owner's61 r2 baseline. Historical
no-version-change/no-attached-device notes below describe the previous checkpoint;
no new APK or four-hour deployment has occurred.

## Scope and status

User explicitly requests that validity limits stop obstructing testing, after the
four-hour gateway-only renewal left the phone with minutes of directory validity.
This change extends the **whole validation contract**, not transport/retry behavior.
Source HEAD64849e828add45407625d31df61413ac98e9a2cc plus uncommitted scoped changes.
No version change, APK build/sign/install, CI run, commit or deployment in this task.
Accepted beta61 r2/code61 remains installed evidence/public diagnostic artifact;
beta60/code60 remains production/default/update-discovery. No download changed.

## Implemented locally

- Go directory/seed and delivery/CRL validation ceiling14400s; Python directory,
  CRL trust and gateway synchronization match. Strict timestamp ordering, signatures,
  exclusive expiry, revocation, revision/CRL floors, identity and admission remain.
- Long delivery is explicitly configured by
  `FC_FRIENDS_RESTRICTED_DELIVERY_LIFETIME=14400`; absent configuration remains3600.
  Invalid configuration fails closed. Sync supports --crl-lifetime14400; default900
  and existing3600 policy remain available. No live environment/unit edits made.
- Long-mode device certificate selection replaces a cached short certificate when
  it cannot cover the new bounded delivery, without changing device identity or grant
  revision. Identical refresh reuses the longer certificate rather than issuing again.
  Existing revoked certificates are still checked before reuse or replacement.
- Long-mode issuance is capped by actual directory/CRL/issuer/grant validity; no
  arithmetic promise overrides expiring material. Android summary displays remaining
  values through14400 instead of treating them as invalid metadata.

The source change alone does **not** provide four hours from every fetch. A room
and its directory have real lifetimes. A proper testing handoff requires a newly
established long-lived seed and sufficiently fresh credentials across the entire
chain. Do not edit a directory expiry independently of the running seed or continue
calling a short remaining lease a four-hour window.

## Validation

- Python168 PASS: friends issuance, new test-window regressions, native compatibility,
  isolated runtime/sync CLI and diagnostic correlation. Uses existing locked Python
  environment and pinned Go toolchain; no skipped Python native compatibility tests.
- Cross-language synthetic signed four-hour delivery is accepted initially, at2h
  and immediately before expiry; rejected at expiry and for future issuance, an
  overlong envelope or a correctly signed overlong CRL. Real native profile checker
  and DeliveryMaterial also accept valid four-hour fixtures.
- Short-directory, short-CRL, short-grant and short-issuer caps; default1h delivery;
  old short certificate replacement/idempotent reuse; malformed policy and4h+1s
  rejection; existing revocation tests extended to14400s.
- Go bootstrap, wholedevice and bootstrap-broker package suites PASS; Go directory
  lifetime boundary tested at4h and4h+1ns. Optional cross-process Go fixture coverage
  is not claimed by this run; Python native compatibility runs independently.
- Focused Android ReadinessSummary JVM suite4 PASS. This is not Android instrumentation,
  a full APK build, platform CI or physical acceptance. Gofmt check clean.

## Required rollout, not yet performed

1. Build an immutable next diagnostic candidate with these client/native changes;
   do not overwrite/reuse the published r2 asset or claim old CI covers new source.
   Complete platform release checks, sign with the existing Android signer and record
   new version/source/APK/signer hashes through the existing release process.
2. Owner Redmi was absent from ADB on04.10. Connect it for an in-place update preserving
   UID, identity, enrollment, activation and Support ID. Verify AWG, export/privacy,
   real restricted correlation and long readiness import before tester delivery.
3. Stage compatible RU API/issuance and RU/NL sync runtimes plus gateway binary.
   Old installed sync1bfa085b and old beta61 r2 do not accept four-hour CRLs: do not
   enable14400 piecemeal and strand active clients. Exact two-device FIELD unchanged.
4. Through protected existing material procedures, ensure issuer and unchanged-revision
   grants cover the planned window, renew gateway/device certificates and CRL, create
   a fresh4h seed, sync the actual directory, then fetch/ACK on working Wi-Fi. Verify
   actual remaining lifetime, aiming for at least3h45 at handoff. If not available,
   report the limiting material and refresh it rather than pretending readiness is long.
5. Only after owner acceptance, supply the new targeted APK to FC-YHQB-9VJN and verify
   normal fresh READY/ACK before one coordinated mobile reproduction. Long CRLs can
   increase accepted revocation staleness to four hours; never disable revocation.

Nothing was deployed, so no runtime rollback is needed now. After eventual activation,
restore short issuance/CRL policy and use compatible validators; do not downgrade a
client still holding long material, restore expired certificates or reduce sequence
floors. Existing production beta60/catalog/landing/Windows/Linux/FIELD remain untouched.

## Independent new evidence

[Export(10)](2026-10-04-field-export10-reliable.md) now proves two real restricted
session disconnects **before** the old readiness expired. Their ReliableStream
recovery exhaustion is separate from this lifetime work. Four-hour support is not
a fix for those disconnects and must not be presented as one.
