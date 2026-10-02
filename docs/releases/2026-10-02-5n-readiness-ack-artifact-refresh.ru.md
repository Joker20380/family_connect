# 5N-READINESS-ACK-ARTIFACT-REFRESH — local provenance, 02.10.2026

**5N-READINESS-ACK-ARTIFACT-REFRESH = PASS.** Local artifact/provenance gate only.
Clean build source: `a24f090d7468dce6183122616117a4e1edaadd3f`.
Immediately preceding product gate: 5N-DEVICE-READINESS-RECEIPT PASS.
No runtime implementation, builder, manifest, authority/admission/TTL policy change.
Only tests, safe pin metadata and documentation change in this task.

Production/RU/NL/Redmi were not accessed. No SSH, system-service operation, authority
refresh, installation, git push, PROV-1 retry, FIELD-1, DIAG-1 or OPS-1. Ephemeral
loopback HTTP/nginx and synthetic sync gateway processes are local test fixtures,
not a deployment or live restricted stack. Production remains last documented
attempt14 rollback state, **not reverified here**. No production rollback needed.

## Audit: all three artifacts affected

Original archive SHA256 values, adjacent inventories and embedded source bytes
were verified before comparing with Git. No source-pin exception:

| Artifact | Classification | Changed bundled inputs / required additions |
| --- | --- | --- |
| HTTP | A — MUST rebuild | `restricted.py`, HTTP entrypoint, HTTP manifest, nginx location; new `readiness_receipts.py` and read-only `read_readiness_ack.py` |
| Candidate readiness | A — MUST rebuild | `restricted.py`, `friends_http_transition.py`, native `wholedevice/provisioning.go`; new receipt module in explicit manifest |
| RU/NL sync | A — MUST rebuild | `restricted.py`, runtime manifest; new required receipt module imported by restricted module |

Sync cannot retain its old pin merely because its CLI is unchanged: the real
entrypoint imports changed restricted code and now requires the receipt module.
No category-B artifact remains. Existing old bytes are retained unchanged.

## Exact pins

[Machine-readable full pins/inventories](2026-10-02-5n-readiness-ack-artifact-pins.json).
All paths below are repository-relative, private local artifacts, **not URLs**.

| Artifact | Old SHA256 | New SHA256 |
| --- | --- | --- |
| `friends-http.pyz` | `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71` | `7ef821a824914b35490d3d371ae4b1722a8900d99cf7b16dbacdd3c5c0af105a` |
| `candidate-readiness.pyz` | `f7827aeed45cb508bc3499bf9f7b31a4d5dfcd99ba9a0eab1e613150c717d929` | `45d35703edeea3cbb1cedcd472ad3b009f15888a6a94c83453e06fce1bd57c96` |
| `restricted-sync.pyz` | `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d` | `0237527cc0fbe6ea5498b0f1d2025894ae3f347c4bb26b4da9f702bfc25f4f1c` |

- HTTP: `state-client-build/readiness-ack-artifact-refresh/http/friends-http.pyz`;
  adjacent `sha256.json`:26 tracked inputs + archive pin;20 Python archive members
  including builder-generated `__main__.py`.
- Adapter: `state-client-build/readiness-ack-artifact-refresh/readiness/candidate-readiness.pyz`;
  adjacent `provenance.json`, embedded `adapter-inventory.json`:14 Python runtime
  sources, locked dependencies and36 native source/module-file fingerprints.
  Deployable bundle also requires adjacent `readiness-delivery-check` and `readiness.lock`.
- Native checker SHA256: `9178b48e5f81085a0428ed11f2b2c33dd99fc27721680a2647e702bd633bdec6`;
  pinned Go1.26.0 linux/amd64, offline readonly module graph, trimpath/buildvcs=false.
- Sync: `state-client-build/readiness-ack-artifact-refresh/sync/restricted-sync.pyz`;
  adjacent `sha256.json`:17 tracked inputs + archive pin;12 Python archive members
  including generated entrypoint. Exact retained bytes pinned; unchanged zipapp
  builder metadata means no promise of byte-reproducible future sync rebuilds.

`git archive` exported all1627 tracked files at accepted HEAD. Every blob/mode was
checked before packaging; no dirty overlay or untracked source entered the build.
All packaged tracked Python/config/template/lock/helper inputs and native sources
equal accepted HEAD. Later task commits contain no bundled inputs, so equality
also holds at final task HEAD. Exact archive member sets reject extra files.
HTTP and adapter were independently rebuilt from the same export: every bundle
file identical (HTTP28 files including sidecars; adapter4 files). Old pins were
rechecked unchanged. No generated binary is committed.

## HTTP / ACK contract results

| Check | Result |
| --- | --- |
| `python -I` closed HTTP startup | PASS; archive-only first-party runtime, no checkout/PYTHONPATH dependency |
| Status ownership | PASS: nginx static GET200; bare handler does not take over status |
| Ordinary malformed challenge | HTTP400 unchanged |
| Safe ordinary behavior | Accepted bounded C fixture400 unchanged; valid activated ordinary challenge200 |
| Restricted malformed / disabled | HTTP400 when enabled;404 when disabled |
| Real-contract non-canary fixture | HTTP403; synthetic identity, not real owner evidence |
| Controlled F/G | HTTP200/200, native crypto validation PASS; `server_contract_fixture` only |
| Valid ACK challenge / READY ACK | HTTP200 /200, ACK_RECEIVED |
| Unauthorized, missing fetch, wrong correlation/fetch/revision/expiry, revoked | HTTP403 access-rejected; no accepted READY ACK |
| Altered signed payload, replay, expired ACK nonce, stale correlation | HTTP403; fail closed |
| Malformed ACK envelope / forbidden schema fields | HTTP503 with bounded `{"error":"unavailable"}` under the existing accepted wrapper |
| Body larger than8192 bytes | HTTP400; no reflection of request data |
| Read-only owner inspection | PASS; correlated allowlisted READY, DB bytes unchanged |

The HTTP503 schema-rejection envelope is current accepted behavior, not a newly
introduced status convention or a waived source mismatch. Tests initially assumed
400/403, then were corrected to assert exact existing behavior plus absence of ACK
or challenge writes. No runtime hotfix or status-policy redesign was performed.
ACK paths reject unknown/oversized fields, identity/public identity, proof, join_url,
credentials/certificate material, invalid enums/types/revisions/expiry and versions.
Valid ACK response contains only version/correlation/status; inspection only safe
receipt metadata. ACK does not issue or modify certificate rows. A signed ACK
without successful correlated fetch or with altered metadata cannot manufacture
readiness. This is authenticated product evidence, **not hardware remote attestation**.

Correlation cleanup is verified:≤16 recent records per device, older-than24h
records pruned on new attempts. One-use ACK nonce follows existing `CHALLENGE_TTL`
**100 seconds**. Earlier product documentation's120s description was corrected;
the implementation/TTL itself is unchanged.

## Cross-component fixture

One test uses these exact new artifacts:

synthetic restricted authority → isolated sync publisher → local forced-command
gateway simulation → CRL1→2 / DB floor2 / validated directory → HTTP owner-contract
challenge/fetch → native delivery validation → simulated valid schema-v1 device
result → proof-bound ACK → packaged read-only owner inspection.

Result: **PASS, `server_contract_fixture`; owner_product_ready=false**. The SSH call
is intercepted in the synthetic test process and replaced with isolated local gateway
CLI; no network SSH, actual issuer, production owner or Device Identity private key
is used. Simulated import result is not Android atomic-import/physical evidence.
Candidate adapter B–G receipts retain `server_contract_fixture` and do not emit a
real-owner acceptance claim. Both normal fixture mode and owned local candidate mode
pass with the refreshed HTTP/sync/native pins.

## Next production acceptance contract — no authorization to run

1. SERVER: generation-bound real Friends challenge PASS + fetch PASS.
2. DEVICE: real app `READINESS_IMPORT_RESULT` v1 READY only after native credential/
   BootstrapDirectory validation, encrypted atomic replacement/readback and usable
   Orchestrator state; durable private local receipt recorded.
3. SERVER: authenticated ACK_RECEIVED and safe owner-bound inspection correlate
   those IDs to the result. ACK delivery failure after local READY leaves local
   READY intact and server ACK_PENDING/UNKNOWN, **not device readiness failure**.
4. Authoritative acceptance needs device-originated READY evidence. HTTP200 alone,
   a server fixture, old receipt or UI gesture cannot supply it. If ACK is pending
   and safe device evidence is not available, owner acceptance remains UNKNOWN;
   do not invent PASS or retire the old generation. Existing `OwnerProduct.observe`
   consumes authenticated ACK evidence, not an app private-state dump.
5. UI/ADB collection is supplemental only, never a readiness gate. No exported
   diagnostic/signing API is added. Existing transaction/rollback, port18085
   prohibition, sole owner/admission and monotonic authority policy remain intact.

These pins are prepared for a **separately authorized** deployment, not installed
server state. No automatic PROV-1 retry is authorized by this report.

## Canary55 unchanged

Existing APK only, no rebuild/install/device access:
`state-client-build/android-canary55-receipt-e817380/artifacts/FamilyConnect-canary55-receipt-e817380-arm64.apk`.

- SHA256 `680a21f60e69cb62d2c7a70be07234b34196e178f0207ed69cb4b422b7bc6247`.
- `com.familyconnect.app.friends`, versionCode55, `0.1.18-canary55-receipt`.
- Signing SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`;
  apksigner verification/v2 PASS; nondebuggable.
- Compiled Android/native input paths unchanged between APK build source
  `e81738083457912da5b1032c45cfbe92bad112cc` and accepted current source. Provenance
  therefore does not require a rebuild. Installed54/public51 remain unchanged.

## Validation and retained evidence

- Focused suite:366 tests PASS,2 historical cases deselected and run separately
  against their original HTTP pin:2 PASS. Includes HTTP packaging/isolated startup,
  ordinary/restricted/nginx routes, ACK negatives, strict schema, bounded cleanup,
  read-only inspection, full isolated sync/negative/monotonic acceptance regressions,
  directory validation, native fixtures and31 candidate packaging/compatibility tests.
- Go/native delivery checker runs from the exact new bundle in the cross-component
  fixture and adapter controlled F/G. All three dependency locks match26 installed
  validation packages (including cryptography46.0.7/RNS1.5.1), Python3.14.4.
- Source/secret guards, explicit archive closure, inventory/hash equality,
  deterministic HTTP/adapter rebuild and `git diff --check`:PASS.
- First full run:363 passed,3 failed during `/tmp` quota exhaustion. Existing Go
  cache was relocated intact to the ignored task directory, preserving its old path
  by symlink; no cache/source/evidence deleted. Adapter suite then31/31 PASS and final
  full suite rerun. Original failure receipts/logs retained, no runtime repair.
- Test-only changes allow explicit caller-pinned artifact inputs instead of silently
  rebuilding or hardcoding old pins; historical attempt9/13 reproductions retain
  their original hashes. New tests exercise exact packaged ACK negatives and the
  offline full sync→native→ACK chain. No source-pin waiver.
- Evidence: `state-client-build/readiness-ack-artifact-refresh/evidence/` contains
  entry snapshot/hash ledger, affected audit, source/artifact inventories, environment
  pins, deterministic repeat result, canary pin and JUnit/logs. Runtime materials
  generated by tests are synthetic and are not committed.
- All17 pre-existing dirty/untracked files preserved; concurrent unrelated updates
  to STATUS/PLAN and the new02.10 VPN-health report are also retained and excluded
  from this task's commits. Only task additions staged in overlapping docs.
  No unrelated work or generated pyz/APK/native binaries in this task's commits.

**STOP.** Push:no. Production changed:no. Authority refreshed:no. Redmi touched:no.
Canary installed:no. Services deployed:no. PROV-1/FIELD-1/DIAG-1/OPS-1 not started.
