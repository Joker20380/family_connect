# GATEWAY-CREDENTIAL-RENEWAL-2 — PASS

## Scope and decision

Credentials only; no continuation of beta68 deployment. Fresh read-only preflight
confirmed expired served/profile leaf18:47:30UTC, issuer6 and grants valid to
07.10 14:45:31UTC, valid signed CRL9868 and matching RU/NL directory. Parent renewal
was not needed: almost19h remained, beyond the accepted four-hour gateway window.
Issuer bytes/key/sequence/minimum revision and grants were preserved. Existing issuer
machinery issued a fresh gateway leaf and CRL9878; ordinary sync then advanced CRLs.
No manual timestamp patch, new root signing, altered validation or lifetime policy.

## Accepted procedure and publication

Used the accepted credential-only renewal operator, with current beta67 hash,
issuer6 and unique protected receipt paths. Native positive/negative authority checks
PASS before publication. Serialized existing RU sync, restored timer in finally.
Publisher applied service UID/GID979,0600, service read-open, atomic rename, fsync and
final readback; publication PASS19:49:10.520354UTC. Same gateway key/service identity,
Family/hostname binding and all other profile fields except certificate/CRL/floor
were verified unchanged. Existing bounded bootstrap acceptance retired the old seed
export and reloaded the unchanged executable.35-second stability check PASS.

Server-local backups/receipts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/gateway-credential-renewal-2-20261006/`.
Do not roll back to expired certificates or lower monotonic CRL/revision state.

## Final authority, consistency and live chain

- Issuer sequence6/minimum revision1; expiry 2026-10-07T14:45:31+00:00; unchanged.
- Grants: owner revision3, tester revision1; both unrevoked, expiry07.10 14:45:31UTC.
- CRL at final snapshot: 9891, expires 2026-10-06T23:55:55+00:00; signed,
  valid, byte-identical RU/NL; NL minimumCRL equals sequence. Routine sync may advance it.
- Directory schema1, generation 2026-10-06T19:49:15.595849272Z, expiry 2026-10-06T23:49:11.128162054Z.
- Directory SHA256 `005662ad02a22d0133acd38a6bd61a716bf137222a92c8ab291849309ea1cbca` on both hosts.
- Authority DER SHA256 `e56da05eab6fa5b7ea210a5cd09f55123cbb1eeb3f68d74f2f6ba43f3eafcb81` on both hosts.
- Actual served TLS leaf SHA256 `c3d14878ec96eed69eb0f27a52e467ec495ba4a28ce9bb0d20b3b8904794dd3f`.
- Served leaf/profile expiry **2026-10-06T23:48:47+00:00**; exact match,
  issuer signature, SAN hostname, validity and non-revocation verified.
- Effective limiting expiry **2026-10-06T23:48:47+00:00**, from actual leaf; headroom
  **13943seconds** measured at 2026-10-06T19:56:23.678871+00:00, including grants/directory/owner receipt.

One leaf is actually served; profile delegated authority is validated separately.
TLS1.3 control listener probe uses SNI gateway.family-connect.test/ALPN http/1.1,
not a new application admission. No split-brain at the checked snapshots.

## Fresh owner beta67 sanity

Foregrounded existing beta67 only; no helper install, app update, force-stop, data clear,
identity reset or radio changes. Fresh authenticated fetch **2026-10-06T19:55:09+00:00**,
native receipt READY **2026-10-06T19:55:09+00:00**, ACK **2026-10-06T19:55:10+00:00**.
Support FC-4D8Q-REEG, owner revision3, minimumCRL9889; admitted/non-revoked.
PRESENT_VALID provisioning/bootstrap, orchestrator_usable=true, failure_reason=NONE.
Receipt expiry 2026-10-06T23:49:11+00:00; operationally capped by served leaf.
This is not cached pre-renewal READY. No data-plane/physical selected-retry test.

## Preservation and security

Installed APK remains beta67/code67, UID10283, CE inode601521, non-debuggable,
SHA256 `8ef45ca26917227e64079cdd49d35f133a03617300b8446f1a476a5d7a69822f`.
Loaded gateway remains beta67 revision `ffd27988468fba427aaba6213b862dca01020972`,
SHA256 `c1370f58dead852efeb21d7b1d8c20e5eabcf333c7df7ec8dd258d5c26bc4143`,
PID1387868, NRestarts0. Service unit/config bytes unchanged,
including FC_DIAGNOSTIC_CONTROL_DIR; dedicated0700 UID/GID979 directory empty.
Android status unarmed/count0. No fault/prearm. Ordinary HTTP/AWG/TCP states/PIDs
unchanged on both hosts. DB grants/devices/invitations/support mapping/admission
fingerprints unchanged; no security floors, revocation or identity binding weakened.
All sealed beta67 and beta68 files/manifest hashes reverified unchanged. No artifact
rebuild, beta68 installation/deployment, public publication, tuning, impairment or soak.

Local evidence: `state-client-build/field65-export16/gateway-credential-renewal-2/`.
Contains authority/served preflight, invariants, native/publication/bootstrap receipts,
timer restoration, actual TLS readbacks, RU/NL comparisons, fresh READY/ACK and
runtime/seal preservation. No private keys, profile contents or identity bytes exported.
One local closeout path-variable collision was corrected; only the read-only checker
was repeated, not credential issuance/publication or gateway reload.
Reports are timestamped evidence, not a promise of future credential headroom.

PINNED-EVIDENCE-DEPLOY-2 may now resume with fresh preflight; it remains PARTIAL until
its installation, full baseline and control gates pass. No physical task is authorized.

**Exactly one recommended next step:** resume PINNED-EVIDENCE-DEPLOY-2 with fresh
headroom/preflight checks in a separate task.
