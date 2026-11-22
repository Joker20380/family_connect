# NL/AWG GeoIP rollout handoff — 22 November 2026

## Installed result

The owner accepted extending IP geography to both NL AWG gateways and explaining
missing metadata fields. Implementation and qualification use the existing clean
`feature/device-technical-metadata-20261115` worktree (`dad9`), whose metadata sources
match the deployed runtime. This older main checkout lacks those sources and remains
divergent; it is not merged/reset or deployed wholesale. Its pre-existing dirty work
is preserved.

Source commit `2d880be1d2cd0534465f9838c93c30f4fca7b0ad` is pushed and remote-verified.
Final rollout documentation `33b9cbdcfa6490ed30cf6eb25740b1b92098fcef` is also pushed
and remote-verified in that branch.
The full receipt and operator runbook are in that branch at
`docs/releases/2026-11-22-nl-geoip.md` and
`docs/operators/technical-metadata-release.md`.

At20:53:48UTC two external collector files and console image
`sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`
replace the prior collector pair and console
`sha256:5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da`.
Exactly three presentation files differ;243 other application files and inherited
image configuration are unchanged. No client binary/version/catalog change occurs:
public Android126/catalog9 remains as before.

## Privacy and acceptance

- Fresh consenting NL/AWG sessions are bound to full canonical keys and pinned node
  state. A second canonical read rechecks consent epoch/sequence/session before the
  central DB-IP lookup. Raw IPs stay transient and are not saved/exported/logged.
- 69 focused GeoIP/fleet/overlay tests and92 isolated panel regressions pass.
  Three normal cycles at20:54:16,20:55:45 and20:57:07UTC import all inventory sources
  and report metadata source `ok`. Two enabled/one revoked rows remain; revoked
  payload and geography are empty. NL2 has city/ASN; final location age214s is
  explicitly last-known, not a newly observed endpoint.
- Authenticated real list/cards for known location, revoked and absent reports pass
  at1440/390px. Temporary owner session is deleted; no messages, password/account
  changes or consent actions are performed. Redacted layouts are inspected.
- Fresh encrypted47,767,570-byte PostgreSQL backup restores39 tables in isolation,
  excluding both metadata payload tables. All36 protected table preimages and six
  configuration/key file hashes are preserved. Three concurrent network-probe/audit
  append pairs are separately validated, not ignored.
- PostgreSQL, publisher and support process/container continuity are verified. Only
  console is recreated; no gateway runtime/service/policy or HTTP/nginx is changed.

## Recovery and limits

A first installation automatically restored the previous image and collectors when
independent network-probe/audit appends tripped a whole-table equality check. The
corrected guard verifies every old row plus only legitimate new probe/audit pairs.
Rollback is therefore exercised without restoring any database, key or consent state.

Ignored private evidence under `state-client-build/nlgeo-20261122/` includes the exact
original Compose chain/environment in `rollback.private.json`, both `*.before`
collector files, encrypted backup, preservation, normal-cycle and browser receipts.
The backup key is stored separately under ignored private storage. Recovery restores
only these collector preimages and baseline5ae92f8c image with the existing monitor
drained, then resumes the unchanged timer. Never use a bare base Compose file or
restore an old HMAC key/database/support cursor.

NL1's controlled path passes, but no consenting physical client is moved to NL1 for
this task. Desktop OS senders, TCP/MESH geography and enabling collection on more
devices remain unimplemented/outside scope. The separate RU transport outage is not
recovered. Other devices still need a supported Android version and their own
voluntary support-information consent to report an OS; absence is not denial.
