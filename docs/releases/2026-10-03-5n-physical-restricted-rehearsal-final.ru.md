# 5N-PHYSICAL-RESTRICTED-REHEARSAL — FAIL

Execution 03.10.2026, 00:25–00:42 UTC. Stage5N remains OPEN. Failure is in the
private acceptance hook's Activity navigation, **not proven restricted transport
failure**. No restricted CONNECT attempt, automatic retry, transport hotfix, new
Stage5N gate, push or FIELD-1/DIAG-1/OPS-1/beta start.

## Source and artifact provenance

- Starting HEAD: `061595376fa65ae38725ed75baac769d71623d92`.
- Final HEAD / task-only provenance commit: `911fea59e08e5ee8844852ae1e2834812632fbde`.
- Commit contains gateway publisher/tests/runbook/report and private57 packaging
  overlay/source inventory. Unrelated dirty/untracked files and unrelated hunks
  were excluded; all pre-commit worktree bytes were preserved exactly.
- APK source is the exact clean0615953 export plus the recorded private Gradle
  packaging overlay, not a claim that57 was built from911fea5. Every source input
  and overlay was reverified against the accepted inventory; no rebuild.
- Inventory: [canary57 provenance](2026-10-03-canary57-provenance.json).
- Private APK: `0.1.18-canary57-physical`, versionCode57, arm64,
  package `com.familyconnect.app.friends`.
- SHA256: `dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- `adb install -r` succeeded; pulled installed APK and signer matched exactly.
  UID10283, firstInstallTime `2026-09-19 17:30:26`, ceDataInode601521 unchanged.
  No uninstall, clear, identity replacement, activation or enrollment reset.
- Previously accepted218 unit tests/lint/APK checks and gateway regression results
  were reused with unchanged source pins, not represented as newly rerun tests.
  This task added actual installed-package, readiness and diagnostic-entry checks.

## One accepted credential renewal

Initial directory expiry00:49:51 and gateway00:54:48 did not provide the reserved
25-minute rehearsal plus10-minute cleanup window. One normal renewal was performed
through the hardened publisher, without server binary/artifact deployment.

Python/native validation PASS; same gateway key, issuer, Family and sole owner,
27 non-canaries denied, no additional admission. Delegation2/grant2 unchanged;
security floors advanced, never reset. Gateway issued00:27:17, expires
**2026-10-03T01:27:17Z**. Directory expires **2026-10-03T01:22:20.767877784Z**.
Credential `family-restricted:family-restricted` (979:979),0600; parent
`root:family-restricted`,01770. Service-user read-open and independent final
credential/native readback PASS. No root:root publication regression.

Only the deployed NL bootstrap was reloaded: READY, PID2788718, zero restarts,
stable35-second observation, served certificate exact-match and gateway binding PASS.
Unit remains active/**disabled**, as at entry. Minimum accepted RU synchronization
gave authority/directory/CRL/floor236 consistency00:28UTC; timer restored and advances
normally. No full acceptance/redeployment, schema migration or artifact restaging.

## Real device persistence before diagnostic entry

Exactly intended Redmi Note9Pro, Android12/arm64, ADB device, Wi-Fi OFF/cellular ON.
Only Friends owned the initial VPN; no ADB reverse/forward or SSH product forwarding.
Canary55 actual installed APK/signature/data verified before update.

Normal55 restart authoritatively returned READY from the existing encrypted bundle.
The observation helper's desired600-second remaining-lifetime threshold was not met:
the product correctly reused its still-valid cache. This was an observer margin,
not a failed product receipt. The update began with more than180 seconds remaining
for update verification; no forced refresh or manual readiness injection was used.

After57 installation, a new process recomputed **restart READY**, same existing
correlation as55, version57, Family TLS PRESENT_VALID, BootstrapDirectory PRESENT_VALID,
Orchestrator usable YES. Immediate delivery was ACK_PENDING; a later fresh57 restart
receipt was READY/**ACK_RECEIVED**. Ordinary product prewarming remained automatic.
The authenticated owner receipt, unchanged UID/install/data inode, and absence of
reset/reenrollment establish identity continuity; private identity bytes were not read.

## Exact failing layer and stop boundary

At **00:36:15.548 UTC**, `OrchestratorDiagnosticActivity` processed `prepare` with
`deny_normal=true`. No synthetic `auto-*.profile` files existed. It wrote
`orchestrator-prepared.json` with `ready=true`, then crashed:

`android.content.ActivityNotFoundException: Unable to find explicit activity class
{com.familyconnect.app.friends/com.familyconnect.app.MainActivity}`.

Exact source operation: `OrchestratorDiagnosticActivity.java:36` calls
`startActivity(new Intent(this,MainActivity.class))`. Compiled57 manifest declares
FriendsActivity and both diagnostic Activities, but **not MainActivity**. The Friends
build substitutes FriendsActivity for the launcher placeholder. This existing hook
navigation assumption was not exercised by the earlier build/unit/lint checks.

The crash occurred after SharedPreferences `apply()` and before durable diagnostic
preferences were observed. The prepared receipt alone was therefore rejected as
proof of an active override. No direct preference injection, manifest rebuild,
second hook attempt, normal CONNECT, restricted session or server hotfix followed.

Friends was reopened normally in a different process (29988→31090). Diagnostic
preferences were absent on repeated readback, so all three deny flags default false;
Auto and activation settings remain intact. **Override OFF**, no remote policy or
test-only server state. Normal Auto connection was not retested; final app is
disconnected, no Android VPN active. Historical AWG CONNECTED events in the retained
file were explicitly excluded from this attempt's acceptance. A UI dump produced no
readable XML; no UI appearance was used as proof or basis for an injected tap.

## Acceptance results

| Requirement | Result |
|---|---|
| In-place57 / identity continuity | PASS |
| Encrypted readiness after update / fresh restart | READY; both PRESENT_VALID; usable YES |
| ACK | ACK_RECEIVED on later authoritative57 restart |
| Diagnostic exhaustion active | NOT ESTABLISHED; hook navigation crashed |
| Orchestrator restricted path / BOOT-1 / Family auth / Room Broker | NOT RUN |
| Dedicated session / restricted Android VPN / actual traffic path | NOT RUN |
| Chrome2+ sites, repeated loads / end-site TLS | NOT RUN |
| Family DNS / concurrent TCP | NOT RUN |
| Direct DNS leak / protected TCP bypass | NOT MEASURED; no zero claim |
| UDP/QUIC / IPv6 fail-closed / underlay protection | NOT MEASURED |
| Controlled restricted-session failure | NOT RUN |
| Diagnostic override afterward | OFF; fresh process/default false, Auto retained |
| Stage5N closed | NO |

## Final production and evidence

00:39UTC readback: NL same2788718/restarts0; RU sync healthy; HTTP generation
`attempt17-0615953`, nginx bytes and HTTP artifact unchanged. RU AWG1515959,
TCP1908885; NL AWG2729703,TCP2420425 unchanged and active. HTTP PID3917121 unchanged.
Final serialized ordinary checks200/400/400/400 PASS. One restricted owner only.
Credential renewal and minimum sync were the only server changes; no HTTP/AWG/TCP
deployment or restart. Fresh security history retained, no credential rollback needed.

Durable sanitized local evidence is under ignored `state-client-build/physical-final/`:
`provenance-commit.json`, `renew-{ru,nl}.json`, `loaded.json`, `consistency.json`,
`installed57.json`, `post-update-readiness.json`, `after-hook-readiness.json`,
`failure.json`, `manifest-failure-proof.json`, `override-cleanup.json`,
`normal-policy-final.json`, `server-owner-ack-final.json`, `after-hook-*.json`,
and `ordinary-after-hook/`. Credential/profile/private identity bytes are not reports.

Canary57 remains **privately installed**, not public or invitation-distributed. Existing
public/invitation/update links were neither changed nor newly verified. Do not
distribute this debuggable acceptance build. Current report/status/guide updates remain
uncommitted after the provenance commit. Physical work stops at the exact hook failure;
the same uncompleted physical acceptance remains, with no replacement Stage5N gate.
