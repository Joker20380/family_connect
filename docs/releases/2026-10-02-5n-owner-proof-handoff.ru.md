# 5N-OWNER-PROOF-HANDOFF — local acceptance boundary, 02.10.2026

## Result and scope

**5N-OWNER-PROOF-HANDOFF = PASS**

Starting HEAD: `a02b82ec70269cd1e5486a26172b7a04d347cb7a`.
Task commit subject: `fix(friends): move real owner proof to product prewarm acceptance`.
The exact final commit is returned in the task handoff; no app version changes.

Attempt12 reached Python/native authority, NL and RU PASS but stopped before HTTP:
its operator contract wrongly required real-owner proof before the actual product
prewarm phase. The fix is a phase boundary correction, not access to identity keys.
Redmi connectivity was not the blocker. No production or device access occurred
during this task. Historical attempt12 remains failed/rolled back, not reclassified.

## Accepted behavior

| Requirement | Implementation / local result |
| --- | --- |
| Operator needs owner's private key | **No**. Direct/external Sessions refuse owner F/G probes; no key-discovery/export/signing interface added |
| Pre-switch candidate | Live B400/C400/D400/E403 plus current authority load and fresh exact-artifact isolated F/G fixture result |
| Controlled F/G | `server_contract_fixture`, **CONTROLLED SERVER CONTRACT FIXTURE**; separate disposable loopback runtime/DB/authority; no production grant or real-owner claim |
| Current material | Pinned `python -I restricted-sync.pyz sync ... --check`; strict expected output/exit,10s bound, durable safe receipt; no publisher/SSH/mutation |
| Post-switch server | External A200/B400/C400/D400/E403 with existing pacing/generation/upstream checks; no operator F/G |
| Actual owner F/G | Friends app only: normal challenge → existing Device Identity signature → normal readiness fetch → native validation → atomic encrypted import |
| States | `SERVER_CANDIDATE_READY` / `SERVER_ACCEPTANCE_PASS` separate from `OWNER_PRODUCT_READY` |
| Commit / retirement | Only after complete actual-product observation; old18084 health checked before product prewarm and before commit;18085 unchanged/forbidden |
| Failure | Receipt first, old ingress restore/readback and worker drain before stopping candidate; no confirmed restoration means candidate retained |

Canonical operator instructions, callback boundaries and future rollout requirements:
[OWNER_PROOF_HANDOFF](../../deploy/friends/restricted/OWNER_PROOF_HANDOFF.md).

The in-process fixture result is fresh≤300s and tied to the tested archive SHA;
it is not a signed attestation or a portable old pytest PASS. Scoped callbacks are
trusted operator code and must use the documented accepted validators. Local
fixture signatures are computed from disposable synthetic identities, not static
owner proofs. They never modify production admission or substitute for device G.

## Product protocol and safe observation

`FriendsAccessAndroid.restrictedReadiness` delegates the same existing protocol to
package-private `FriendsReadinessProtocol` for JVM tests. Audience/TTL/challenge/
device binding, `ControlIdentity.proveTransportKey`, HTTPS transport, native delivery
validation, secure vault and persistent cache policy remain unchanged. The protocol
helper is not an Android component or remotely accessible signing method; it only
implements the normal request/fetch workflow inside the app.

`OwnerPrewarmReceipt` records two fresh random32-hex request IDs and allowlisted
`challenge_result`, `fetch_result`, `import_result`, `revision`, `expires_at`,
`observed_at`; class is `real_owner_product`. Existing readiness diagnostics display
this safe JSON. IDs pass via `X-FC-Probe-ID`; nginx adds a fixed route-step enum to
its existing redacted trace. No raw URI/query, proof, device identity, bundle,
certificate, private key, room URL or arbitrary error text is recorded.

The operator observes diagnostics from the known actual Friends app plus scoped
server receipts. It does not supply the app a challenge or request a signature.
`OwnerProduct.observe` validates exact schema/categories, distinct IDs, corresponding
challenge/readiness200 and upstream200, generation, ordered fresh timestamps and
unexpired revision metadata. Native validation/cache import must have completed.
An F challenge alone does not prove ownership; G authorization and validated app
import do. Observations are consumed once in a bounded300s post-switch window.
Missing, stale, wrong-generation, denied, failed-import or malformed observations
cannot commit. Diagnostic evidence is not itself an authentication capability.

The normal foreground/activation/configuration triggers,300s attempt cooldown,
valid-cache retention, secure storage and response wiping remain. No new manifest
entry, manual refresh bypass, generic signing API, debug identity, key export,
reenrollment, cache injection or ADB path. An already-valid cache is not proof of a
new F/G transaction; absence of fresh observations fails rather than bypassing policy.

## Tests and reproducibility

- **197 Python tests PASS,0 skips,170.23s** with exact accepted HTTP/sync artifacts,
  isolated actual nginx and Go1.26.0. Handoff, candidate, transition/rollback, HTTP
  runtime, restricted producer/delivery, Android source guards, receipt/redaction
  and native authority compatibility suites. Temporary local processes only.
- **38 additional source/acceptance guards PASS,0 skips**; documentation check:
  429 Markdown files,2591 links,0 errors. `git diff --check` PASS.
- Exact HTTP archive SHA256:
  `460e75205eb9baff313dc7dd963cdb7bceddf2d1e13405a71686f9ec6c976d71`.
  Exact sync archive SHA256:
  `9d965b955cbd5375c82adadb3f25736d1cca3fe86ab477ea73269ef1499a5a2d`.
  No artifact replaced or published. Native controlled delivery invokes the
  accepted `wholedevice.ValidateDelivery` consumer with synthetic public identity
  and fixture anchor, not an operator-held production private key.
- **149 JVM tests PASS,0 skips**, JDK17, offline `clients/android/control-tests`:
  actual product challenge/proof/fetch workflow with an independent signature
  verifier, failures for invalid proof/revoked/non-canary/expired/wrong-device,
  app unable to sign, safe receipt state/redaction, existing identity/conformance
  and7 persistent RestrictedCache tests. Synthetic JVM transport is not a live
  Android/server acceptance claim.
- Real local blue/green tests keep the old listener reachable through owner
  observation, exercise explicit owner failure and a callback that returns true
  without product evidence, prove restore→ordinary checks→drain→stop order, and
  preserve the candidate on uncertain restore/drain. Fixture server PASS without
  any real-owner key does not imply product PASS.
- Initial local runs exposed a wrong fixture host for strict sync check, health
  probes aimed at current ingress rather than old listener, a checked Java parse
  exception and a directory/file test environment mismatch. Corrected locally;
  no production retries or hotfixes. Full accepted suites above passed afterward.
- Android resource generation and an independent JDK17 compilation of **112 current
  Java source files PASS** with SDK35 and pinned Gson2.13.2/BC1.85.2. No APK assembly,
  signing, install or release. Full Gradle Java task initially stopped on a
  pre-existing broken generated Python3.10 symlink; the independent compile first
  encountered stale R output/duplicate old Gson on its validation classpath. Fresh
  local resources and the correct dependency versions resolved the source check;
  no production fix or successful full Gradle APK pipeline is claimed.

Local logs/XML and entry snapshots: `/tmp/fc-owner-handoff/`; no production material.
Documentation link/source guards and `git diff --check` are checked before commit.
Local simulated `real_owner_product` observations validate receipt logic only;
**real Redmi F/G, provisioning, restart and VPN behavior are NOT RUN**.

## Git, production and remaining boundary

Task-owned source/harness/tests/docs only are committed. Pre-existing dirty reports,
attempt12 report and earlier STATUS/PLAN/runbook deltas are retained outside that
commit; unrelated index/worktree content is not swept into it. No push.

No production access, authority refresh, system-service action, live Telemost or
Redmi operation. No credentials extracted. No app version, built APK, installed,
publicly distributed or invitation-page artifact changed. Production remains the
last documented rollback; live availability/authority validity was not rechecked.

A later explicitly authorized deployment must stage this harness/trace contract,
build/verify a same-signature canary containing the safe observation hook and
install in place only at the product phase. Existing canary53 is not retroactively
updated. Revalidate every server/device gate; keep old18084 until actual owner
import PASS. Rollback on failed owner acceptance under current policy, never obtain
credentials to diagnose it. This local gate grants no attempt13, DIAG-1, beta or
FIELD-1 authorization. STOP.
