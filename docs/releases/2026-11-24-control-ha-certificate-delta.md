# 24 November 2026 — post-renewal certificate-content diagnostic

Scope: continuation of the selected **HA-02 journal/current-operation gate**, not a
new letter/stage, production cutover or recovery acceptance. Previous
[installed-current observation](2026-11-24-control-ha-installed-current.md) found three
expired baseline certificate rows replaced by one later-issued row. This slice checks
that bounded content difference cryptographically without rewriting the baseline.

## Actual read-only observation

Final probe: **24 November00:34:17–00:34:20UTC** (01:34 Brussels), sequential pinned SSH
to RU185.251.89.19, NL1 185.10.158.212 and NL2 185.10.158.196. Existing
[NL2 authorization/pin](2026-11-02-second-nl-ordinary.md#authorization-and-trust) retained.
No retired/excluded host or MicroTrader service accessed. Three exact source modules
were streamed in memory into existing interpreters with `-I -B`, not installed.
Only the existing bounded no-follow file reader, read-only SQL and fixed Family Connect
`systemctl show` observations ran; no runtime node/controller entrypoint was imported.

| Check | Result |
| --- | --- |
| Fleet | Same current COMMITTED plan; all three config hashes/unit orders match the transaction; issuer/CRL/gateway material and both directory publications agree |
| Four non-certificate tables | Exact target match:69 devices,125 invites,2 persisted grants,1 CRL-sequence row |
| Certificate rows |0 retained,3 expired removals,1 signed addition; baseline still differs from current DB |
| Added certificate | Signature, canonical PEM, serial/DB expiry, device hash/public key, family/role/revision, exact native extensions, validity bounds and CRL non-revocation check pass |
| Admission | Observed all_activated document hash and mode match transaction/config; missing persisted grant is native activated-membership behavior, not an override |
| RU API / NL bootstrap | RU API and both NL services active/running, Result=success, NRestarts=0 |
| RU timers | Credential-renewal/directory-sync timers active/waiting; their one-shot services inactive/dead with success |
| Legacy timer | Restricted-sync remains intentionally inactive; not enabled or restarted |

The result is **CERTIFICATE_CONTENT_COMPATIBLE_NOT_AUTHORIZED**. It confirms the
observed certificate bytes are compatible with current signed material and membership,
not who requested issuance, their consumed challenge/proof, historical paid entitlement,
or original schedule approval. Existing historical records are neither repaired nor
replayed. No end-to-end HTTP/VPN/WebRTC/client failover claim follows from service state.

## Contract and safeguards

[Diagnostic](../../scripts/control_ha_certificate_delta.py) is independent of the
recovery/import code. It verifies the signed delegation against the observed installed
anchor, self-signed Ed25519 CA role/time, signed current CRL/sequence/window, and bounded
native device certificate contents. All old certificate rows must also be structurally
and cryptographically valid; retained rows must be identical, and removed rows must
have expired by capture time. Retaining an expired or revoked historical row does not
authorize its use. Other four table projections must still match the immutable plan.

The [collector](../../scripts/control_ha_installed_current.py) obtains delta records
from the **same read-only SQLite transaction** as its existing comparison, not a second
DB read. Existing5s SQL deadline,4096 rows/table,16MiB aggregate, WAL-sidecar safeguards,
metadata/data-version rechecks and refusal/redaction rules remain. The anchor is bound
to config and recorded policy hashes; admission bytes/mode are bound to the recorded
policy and config. These are observed local bindings, not independent off-host root
custody or a coherent cross-host/store writer barrier.

Two native admission modes are explicit. Legacy mode requires the persisted active
grant and its expiry. In all_activated mode the native
[activated_grant](../../control/friends/restricted.py) uses active device/invite rows,
rejects a revoked or wrong-family/below-floor persisted grant if present, and otherwise
uses the delegation revision floor. Legacy grant expiry is not an expiry source in
that mode; historical paid entitlement is a separate, **unchecked** boundary here.
No missing row silently selects this mode: malformed/unbound policy refuses.

The first live diagnostic refused because it incorrectly required a persisted grant
in all_activated mode. A bounded on-host diagnostic exposed only exception class/frame
numbers, no row values. The correction uses the native mode contract and independently
observed policy bindings, with native issuance/negative tests. The refusal receipts
are retained privately, not overwritten or represented as successful qualification.

`control_ha_current_audit.py`, `control_ha_online_capsule.bind_current` and import
acceptance were **not changed**. Their strict five-table equality still refuses later
certificate rows. Never feed the compatibility result as an import override. Every
diagnostic result retains `recovery=BLOCKED`, `activation=FORBIDDEN`; successful content
checks also report `challenge_proof=NOT_RECONSTRUCTED`,
`entitlement_history=NOT_VERIFIED`, `snapshot_barrier=false`.

## Qualification and source identity

**175 PASS /0 skips in19.04s**:59 delta tests,34 collector tests,26 inventory tests and
56 strict current-audit regressions, using the existing control/identity-lockfile venv.
Native fixtures actually issue, prune and issue again with purpose-bound proofs;
legacy and activated-without-grant/expired-legacy-grant cases are exercised. Negative
tests cover signatures, authority/CRL/time, public key/identity/serial/revision/role,
extensions, membership/revocation, policy shape/binding, missing invite, premature
deletion, retained-row replacement, duplicates/bounds and private error redaction.
Collector regressions retain read-only/WAL/race/privacy checks; strict audit drift
refusals pass unchanged. No PostgreSQL, full-system DR or platform release gate rerun.
Six changed documentation files/966 local links and whitespace checks pass; external
URLs are listed by the checker, not freshly network-validated.

```sh
python -m pytest -q tests/test_control_ha_certificate_delta.py \
  tests/test_control_ha_installed_current.py tests/test_control_ha_installed_inventory.py \
  tests/test_control_ha_current_audit.py
```

Final probe receipts bind these exact source hashes:

| Source | SHA256 |
| --- | --- |
| control_ha_certificate_delta.py |99588af29ff0d99f7ccfbede29e15bfc5590da82b58fa2422f91f1783ebae441 |
| control_ha_installed_current.py |d1d868c2483722c40592f6848672c646d98b5df16c77b79777b52efd7335a9cf |
| control_ha_installed_inventory.py (unchanged) |323035f48bc156215085a0dcc28eb5b5fc1b85747b6ae7d0d51f3d5208ef40fe |

Private evidence: `/tmp/fc-control-ha-20261124/certificate-delta-final/`, host JSON/meta
receipts and reconciliation; JUnit `certificate-delta-qualified.xml` in the parent.
Initial refusal and bounded diagnosis remain in `certificate-delta-installed/` and
`certificate-delta-diagnostic/`. Directories0700/files0600 and umask077 are retained;
no device/invite/serial/profile/key payload or DB was exported or committed. Temporary
local evidence is **not** off-host disaster-recovery custody. Early test fixture failure
(900s CRL expired before the second issuance) and two exception-type test expectations
were corrected before the final gate; only the final175-test run is acceptance evidence.

## Remaining selected gate, rollout and rollback

Content compatibility for this observed certificate delta is established. Still open:
original schedule/controller approval custody, consumed-proof/paid history boundaries,
and a coherent post-renewal current-state snapshot bound to issuer/publications and
recovery. Preserve the immutable renewal baseline and capture current state separately;
do not restore old certificate rows or re-sign old journals. If original provenance
cannot be recovered from trusted custody, propose an explicit forward-only provenance
design; never invent historical approval or install it under this diagnostic scope.

The same four [stage2 exit blocks](../control-ha.md#когда-заканчивается-этап-2) remain:
journals partial; installed schemas/writer barrier, full off-host/current-state recovery,
strict PostgreSQL/Patroni quorum/RPO0 unqualified. No credible calendar ETA or completion
percentage follows from these test counts. HA-03..05 follow; RU dependence remains.

No deployment, DB/config/policy write, service action, public asset/catalog/version
change or host resume. Installed console image
`sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`, RU HTTP archive
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`, NL GeoIP22 November,
Android126/catalog9,8/12/120s and all-three-node ACK remain unchanged. Built/source-pushed
is not installed/publicly distributed; no new public-artifact verification is claimed.

Rollback: stop using the diagnostic; no installed change exists to undo. Keep current
production data and private evidence. Any source reversal is a new ordinary commit,
not a reset/force push or restoration of a stale SQLite copy.
