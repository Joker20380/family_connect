# 5N-PHYSICAL-RESTRICTED-REHEARSAL — BLOCKED

Date03.10.2026 Europe/Brussels; execution02.10 23:12–23:29UTC.
Source HEAD `061595376fa65ae38725ed75baac769d71623d92`, unchanged and not pushed.
[Allowlisted machine evidence](2026-10-03-5n-physical-restricted-rehearsal-evidence.json).

## Scope and final boundary

The authorized final physical gate was **not reached**. Previous attempt17 owner
challenge/fetch200, READY/ACK and encrypted restart persistence remain accepted
historical evidence, not newly measured results. No production schema migration,
artifact staging, server rebuild, ingress rollout or owner re-enrollment occurred.
No post-use runtime staging directory was reused for activation. The existing exact
pinned native authority operator was used only for credential validation.
Historical attempt15/16 causes were not investigated or reattributed.

## Private acceptance build — built/signed, not installed

| Item | Result |
|---|---|
| Version / code | `0.1.18-canary57-physical` / `57` |
| Package / ABI | `com.familyconnect.app.friends` / arm64-v8a |
| APK bytes | 52,727,109 |
| APK SHA256 | `dd3c1b1bd9031f189ef7fc606969eb7da05e44f470478c8457f9097119b9c975` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Signing | Existing protected local production-compatible signing identity; v2 verified |
| Source | Clean git archive; every tracked blob verified against full HEAD |
| Tests | 218 unit tests PASS,0 failures/errors/skips; lint/assemble PASS |
| APK checks | Package/version/signer/arm64/native provenance PASS; recursive scan1079 entries, no unreviewed findings |
| In-place update | NOT RUN; Redmi remains canary55 |
| Distribution | Private artifact only; public/invitation/catalog unchanged |

Artifact: `state-client-build/physical-rehearsal-0615953/artifacts/FamilyConnect-canary57-physical-0615953-arm64.apk`.
Normal native SHA256 `1910ccac238884dd55120917c509571117f2aa2e95d10e9255ea00a069738517`;
restricted native SHA256 `0307df7e41bd2a002ee9cde37002862d5c6a445e319c9ea297829975b7e6da21`.
Go normal1.26.1, NDK27.2.12479018; accepted Xray revision
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`. No dependency/source reuse change.

Minimal mechanism: private isolated `packaging.gradle` sets version57, Friends
debuggable and includes the existing committed debug Activities/manifest. No tracked
public Gradle/runtime changes, second connectivity stack, restricted/BOOT-1/FamilyTLS/
TUN modifications or server owner exception. Existing `OrchestratorDiagnosticActivity`
sets `deny_awg`, `deny_wg`, `deny_tcp`; existing `AutomaticConnection` rejects only those
normal candidates and records structured events. The mechanism was **never installed
or enabled**. Exported diagnostic Activities/debuggable packaging are private-only;
this APK must not become a public release. Signing secrets never left local protected
storage/memory and are excluded from evidence.

## Fresh production and credential-only failure

Initial ordinary API stream200/400/400/400 PASS at≤1request/sec. Accepted HTTP18086
generation`attempt17-0615953`, NL bootstrap, RU sync, AWG/TCP active and pins unchanged.
Gateway expiry23:37:09UTC and old directory expiry23:32:17UTC did not provide a safe
build/rehearsal window. Delegation/issuer and owner grant remained valid until
03.10 11:54:56UTC; no delegation/grant renewal or identity/admission change needed.

23:24:27UTC: accepted issuance machinery renewed gateway certificate until
03.10 00:24:27UTC; Python and exact native checker PASS (including negative checks).
Same Family, sole owner, gateway/issuer keys; delegation2, grant2, minimum revision1,
27 non-canaries denied. CRL114→115 and later sync increments retained. RU timer was
briefly paused to serialize publication, then restored; HTTP/AWG/TCP untouched.

**This session's renewal adapter made an operational publication error:** it used
root's generic atomic writer for live `gateway.json`, producing root:root0600 rather
than retaining `family-restricted` ownership required by the deployed service. The
already accepted create/write/fchown/fsync/rename publication step was omitted. Native
validation ran as root and passed, but that does not prove service-user readability.
Observed mode/owner and unit User establish the access defect. The broker's underlying
error text is not exposed by its generic exit message; no claim about transport/provider
failure is inferred from it.

Committed authoritative reload acceptance: start succeeded, PID2755730 appeared,
then at23:24:35UTC `activating/auto-restart`, `ExecMainStatus=1`, no directory published;
verdict `service_unhealthy`. Receipts were fsynced before rollback. Failing unit was
stopped to suppress further systemd restarts; no operator acceptance retry/hotfix.
This is not evidence that the phone's restricted transport failed.

## Rollback and final production state

Protected remote evidence/rollback path on both authorized hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/physical-rehearsal-0615953`.
No private profile, key, DB or provider token is in this report/Git/output.

Previous gateway certificate restored on NL, with current signed CRL/minimum floor
retained, not restored backward. Service-owned secure atomic publication restored
UID979 and0600; same Family/key/authority. One restoration start of the existing binary
produced a fresh directory and stable PID2757605/restarts0. This was rollback to the
previous certificate, not another acceptance attempt with the renewed certificate.

Final readback23:29:46–51UTC:

- HTTP candidate PID3917121, nginx SHA256
  `19c04fb97209bf5d88695f97da39fd4d930dc8f69d8e3a71f2ee964cc592af69`, same18086 routing;
  old18084 remains retired. No ingress change or18085 modification.
- RU AWG1515959/TCP1908885; NL AWG2729703/TCP2420425: unchanged PIDs/start times/restarts.
- RU sync timer active, last oneshot success; RU DB/signedCRL and NL floor125.
- NL bootstrap active/running PID2757605/restarts0; **UnitFileState=disabled** as at entry.
- Fresh directory issued23:28:02.987835691Z, expiry03.10 00:22:59.954609523Z.
- **Restored gateway certificate expires02.10 23:37:09UTC.** Later directory expiry or
  active PID does not extend credential validity. No promise of readiness after expiry.
- Final ordinary/restricted-malformed serialized stream200/400/400/400 PASS; no429/502.
- Deployed HTTP pin `ad71cadba79a8fbbe4e60d8d2a1c581304e263a30fdf71fd69b002001d01dd63`;
  sync pin `f6aa8859ab716383bf207b2ff7b302687692832b2ccb410f1aef0ada0793a9c9`, unchanged.

## Physical acceptance matrix

| Requirement | Actual result |
|---|---|
| Physical device | Exactly intended Redmi Note9Pro/device, Android12/arm64 |
| Installed version | Canary55 retained; no57 install/uninstall/data clear |
| Device Identity | Untouched; no replacement, extraction or new challenge in this task |
| Readiness after APK update / restart | NOT RUN: no APK update; historical attempt17 PASS not reused as fresh evidence |
| Radio state | Wi-Fi OFF, cellular ON at entry/final |
| Forwarding | No adb reverse/forward; no SSH product forwarding, manual room or fixture |
| Friends restricted VPN / no-other-VPN acceptance | NOT ESTABLISHED for this rehearsal |
| Diagnostic exhaustion | Existing hook packaged privately, never enabled |
| Orchestrator path / BOOT-1 / restricted session | NOT RUN |
| Chrome2sites/repeated loads/end-siteTLS | NOT RUN |
| Family DNS / concurrent TCP / path proof | NOT RUN |
| Direct DNS leak / protected TCP bypass | NOT MEASURED; no zero claim |
| UDP/QUIC / IPv6 fail-closed | NOT RUN |
| Underlay protection / controlled failure | NOT RUN |
| Override cleanup | No override was enabled; no server transport override |

Stop at this failed current prerequisite, before modifying Android. Future separately
authorized continuation can use the existing private57 artifact after fresh pin checks
and the accepted ownership-preserving credential publication; it does not require a
new architecture, gate, full deployment, schema migration or owner re-enrollment.
Preserve monotonic security history and ordinary production. All remaining physical
requirements stay within the same final gate.

**Stage5N closed: no. Push: no. FIELD-1/DIAG-1/OPS-1/beta started: no.**
After eventual physical PASS only:2–3trusted field canaries and DIAG-1A, not started here.
