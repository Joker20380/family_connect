# AUTHORITY-RENEWAL-1 — PASS

2026-10-06. Authority restoration only, following the credential STOP in
[PINNED-EVIDENCE-DEPLOY-1](2026-10-06-pinned-evidence-deploy-1.md).
Beta66 APK/gateway remain installed/loaded; sealed beta67 remains untouched.
Final readback: **2026-10-06T14:50:38.273020Z**.

## Accepted procedure and renewal order

The [gateway publication runbook](../../deploy/friends/restricted/GATEWAY_RENEWAL.md)
routes authority policy to the accepted [four-hour rollout](2026-10-04-beta62-four-hour-rollout.md).
The precise expired-parent precedent is [clock-skew issuer4→5 restoration](2026-10-05-readiness-clock-skew.md).
Retained operators: `state-client-build/readiness-clock-skew-20261005/operate.py`
and `/tmp/fc-beta62-window-operate.py`; this task reuses their authority preparation,
issue and gateway-publication operations without their old runtime/archive deployment.

Order: verify old signed provenance and retained issuer key → construct new same-key
CA certificate/delegation payload → offline control-root signature and current-time
delegation validation → renew existing grant expiries → publish monotonic signed CRL
→ issue gateway/canary leaves under the valid renewed parent → native validation and
ownership-aware profile publication → bounded bootstrap reload/new directory → normal
RU/NL sync → actual TLS-chain verification → ordinary beta66 client import/READY/ACK.
Directory generation occurs after gateway reload, as required by the actual code,
not before the new seed is available. Client fetch waits for verified propagation.

The expired delegation is verified at its last valid instant **only to authenticate
historical renewal provenance**, exactly as in the accepted issuer4→5 procedure.
It is never accepted for live child issuance. New issuer6 is independently signed by
the existing offline control root and validated at current time before publication
and child issuance. No verifier, clock, validity check or signed timestamp is patched.

Required authorities verified before runtime changes: existing local control-root
key `state-client-build/update-signing/ed25519.key` (matches pinned control anchor),
and RU `friends-restricted/issuer.key` (matches existing delegated CA public key).
Offline root stays local; delegated key stays on RU; existing gateway/device identity
keys remain unchanged. No keys, DB or credential secrets printed, committed or sent to CI.

## Preflight and changes

| Item | Before | After |
| --- | --- | --- |
| Issuer sequence | 5 | 6 |
| Issuer expiry | 06.10 13:51:23UTC, expired | 07.10 14:45:31UTC |
| Issuer notBefore | prior signed issuer5 | 06.10 14:45:26UTC |
| Minimum revision | 1 | 1, unchanged |
| Owner grant | revision3, non-revoked, expired06.10 13:51:23UTC | revision3, non-revoked, expires07.10 14:45:31UTC |
| Tester grant | revision1, non-revoked, same expired bound | revision1, non-revoked, same new issuer bound |
| CRL | sequence9323, expired06.10 13:51:23UTC | initial9324; final9330, valid14:50:22→18:50:22UTC |
| Gateway profile leaf | expired06.10 11:03:25UTC | valid06.10 14:47:25→18:47:30UTC |
| Owner admission | FC-4D8Q-REEG admitted/non-revoked | unchanged |
| Gateway process | PID1124728/NRestarts1 | PID1231405/NRestarts0 |

Policy unchanged: issuer/grants24h from issuance; existing5-second notBefore allowance;
gateway/CRL14400s. All subject/issuer names, CA extensions, public key, family/gateway
bindings and minimum revision compare equal between issuer5 and issuer6. Existing
grants retain device/family/revision/revocation tuples; only expiry changes.
The native authority checker passes positive and negative cases before publication.
No authority/revision/CRL failure occurs in the accepted post-renewal flow.

## Hashes and RU/NL propagation

| Artifact | SHA256 |
| --- | --- |
| Old issuer envelope | `18c024beaaf1a3555c14ae8d56dc61a02cf1c84ab20538f3bd40e0a1f8c8bac3` |
| New root-signed issuer6 envelope | `0828a74797f99a3edfe3b98ece285ef3a224bcea687fabb0815663a751f29571` |
| New CA DER, equal RU/NL | `e56da05eab6fa5b7ea210a5cd09f55123cbb1eeb3f68d74f2f6ba43f3eafcb81` |
| Admission, unchanged | `e63b6438ef5a9e575681c0e1b84a1e070cf4d2164d5ee153f038cab9e6b50ac2` |
| Old directory | `e5a04bfbeffaef4c5a0062b5d00949b8b43b55bf007cab8329e55fa6ba4d627e` |
| Fresh directory, equal RU/NL | `303ac42212e6c1c0bc61bb1a7f9f73f05ae239de6be1b2ba782eef531e7d3aa1` |
| Final CRL9330 DER, equal RU/NL | `1e7e386a0ded205efa9743bfa68790ce405887831de5a6e93a2f19dad35326c1` |
| Actually served leaf DER | `a2c4324401fbfb2374a61c1404caa0d264305533496394a17c641c4549940ff4` |
| Initially published gateway profile | `834f2e6fe4d50ea6092259d2dd954fd31a1e0261ad5cea0aab1edf4be69bb8e0` |
| Final profile after normal CRL sync | `d0847725bafa1ea22978accc301b0e9cf097e4613b140d237f0210840151b731` |
| Unchanged loaded beta66 gateway | `6af92aa99af36f8837f6741203cb0805e32c138ac25d93e0e78a607f4003a7ec` |

Fresh directory version1, generation/issued_at **06.10 14:47:36.916634343UTC**,
expires **06.10 18:47:33.235417698UTC**. Exact hash/authority/CRL equality verified
before owner launch and again after READY/ACK. No stale RU snapshot or split-brain.
The old seed export was retired through the existing bootstrap acceptance procedure.
RU sync timer restored to its prior active state in `finally`; sync exit0 at closeout.
CRL sequence naturally advances after restoration; these hashes are timestamped evidence,
not a promise that regularly refreshed CRL/profile bytes remain fixed forever.

## Actually served chain and headroom

TLS1.3 probe to the real127.0.0.1:18444 listener, SNI `gateway.family-connect.test`,
ALPN `http/1.1`, returns one leaf matching the profile exactly. Signature verifies
against the root-delegated profile authority; hostname SAN, notBefore/notAfter and
CRL signature/validity pass. The profile CA is verified separately, not falsely
counted as an additional certificate served by the listener.

Effective minimum across issuer/grants, CRL, gateway leaf, directory and owner receipt
is **06.10 18:47:30UTC**, limited by the actual served gateway leaf. Headroom at final
14:50:38UTC readback: **14211seconds =3h56m51s**. The three-second-later directory/
receipt expiry does not extend that bound. Recheck current headroom before deployment.

Publication PASS at14:47:32.441423UTC: UID/GID979,0600, actual service-readable,
atomic publication and final readback. Bounded authoritative bootstrap acceptance
passes; subsequent readbacks retain PID1231405, NRestarts0 and the beta66 executable.
Service config hash remains `b9012b159073ddedc2fcad12a31f4a4bc9175ff860c0ac15a9d5ec3ab9386199`.
HTTP/sync archives, ordinary HTTP/AWG/TCP PIDs and states remain unchanged on both hosts.

## Owner beta66 ordinary readiness

Before normal foreground launch at14:49:36UTC: exact installed beta66/code66 APK
`e1882552dd3510dd232a2bd0cdafbf86160f924190197544925d4e046329ee81`, package
com.familyconnect.app.friends, UID10283, CE inode601521, non-debuggable.
No APK installation, test helper, data clear, clock/radio changes or identity reset.

Fresh authenticated challenge/fetch **14:49:38UTC** → native validation/import
**READY14:49:38UTC** → **ACK14:49:39UTC**, beta66, Support FC-4D8Q-REEG,
owner revision3/minimum CRL9328, admission non-revoked. Receipt reports
provisioning/bootstrap PRESENT_VALID, orchestrator_usable=true, failure_reason=NONE.
Receipt expires18:47:33UTC, capped operationally by gateway18:47:30UTC.
This is not reused cached READY. The later gateway CRL9330 is monotonic and compatible.

Authority sanity consists of native positive/negative validation, authoritative
bootstrap/directory acceptance, actual served TLS and ordinary native owner READY/ACK.
No app data-plane VPN/Telemost DNS/HTTPS/TCP baseline was run: it is not required for
this authority-only gate and remains part of the separate beta67 deploy acceptance.
No fault/prearm, intentional drop, selected-retry capture, tuning, soak or impairment.

## Backups, provenance and remaining work

Protected server staging on both authorized hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/authority-renewal-1-20261006/`.
RU retains before issuer/CRL/directory/admission, SQLite backup and grant snapshot;
NL retains before profile, gateway binary, wrapper and unit snapshot, plus native/
publication/bootstrap receipts. Backups remain server-local. Do not restore expired
credentials or lower issuer/CRL floors; if new credentials fail, stop only restricted
bootstrap and diagnose/forward-repair under valid authority. No binary rollback needed.

Protected local evidence: `state-client-build/field65-export16/authority-renewal-1/`.
Includes preflight, root-key availability receipt, prepared receipts, signed delegation,
issued receipt, gateway publication/native result, timer restoration, two verification
snapshots, owner fetch/ACK and `local-chain-verification.json` with exact operator hashes.
Minor local checker argument/SQL/path errors were corrected during preflight; no live
security contract was altered and no mutation phase was retried after an uncertain save.

Sealed beta67 manifest and all7 members freshly rechecked unchanged. No beta67 install,
gateway replacement, build, publication or catalog/default/invitation change. Existing
dirty work and HEAD8d046321 preserved. Product source was not changed.

**PINNED-EVIDENCE-DEPLOY-1 may now resume with fresh preflight; it is not yet PASS.**
An owner physical evidence/impairment task still may NOT begin until that separate
deployment acceptance is complete. Exactly one recommended next step: resume
PINNED-EVIDENCE-DEPLOY-1 with fresh owner/headroom/control checks and its remaining gates.
