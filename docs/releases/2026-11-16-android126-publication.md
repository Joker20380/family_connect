# Android126 technical metadata — public delivery, 16 November 2026

**PUBLIC / optional catalog9.** At20:42:19UTC the actual signed discovery, legacy
descriptor, `/i/` and `/invite/` advertise the same accepted APK. Complete trusted-HTTPS
download, signature/package/ABI verification,206/416 and resume checks pass. There is
no new build/signing, vault access, server-image deployment, RU recovery or HMAC
rotation in this publication. Separate RU restoration is accepted; its initiating
watchdog stall remains **CAUSE_OPEN**, not a claimed fix in this release.

**22:47UTC update:** PR38 is merged with qualified source588e793a. A later health
readback discovers a **new22:07UTC RU outage**, detailed below and in the
[incident report](2026-11-16-ru-recurrence.md#new-recurrence--16-november2207utc).
HTTP/public delivery and protected support/HMAC2 state remain available; RU AWG/TCP
are not healthy. No recovery or transport restart is part of this publication.

## Immutable public files

| File | Bytes | SHA256 |
| --- | ---: | --- |
| [APK](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta126.apk) |50478496|`4f288cbb107ac46c8c99ec0e274f57a5e1e8164796796781c4a2c275b57e2134`|
| [Exact Android source](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta126-source.tar.gz) |17011109|`3bcf9a6ff44e8d65b80cf8f3c6436c873040bbebaec4cbfe016d78b4079d764e`|
| [Audio corresponding source](https://185.251.89.19:8443/downloads/FamilyConnect-Android-0.1.18-beta126-audio-source.tar.gz) |7602082|`780c7717faad7a21fcd894324a1e350cc525e2719573835cf72abe40d0cd9039`|

Package `com.familyconnect.app.friends`, version `0.1.18-beta126`, code126, ARM64,
minimum Android8.1/API27,16KiB alignment. Signer SHA256:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Android source is `ba3e93703d407c945350c1187e3738d25a3c9eab`; its qualified merge
`0a2863b3b182ce8ec7a03e91c11749dac2d87c89` has the same tree. Retired97513e3f remains
unchanged/test-only. Neither unsigned hash nor a later CI build replaces these bytes.

Update using **Settings → Check for updates → Install beta126**, or the APK link.
Android asks for installation confirmation. Do not uninstall, clear data or downgrade.
Catalog9 is optional (`minimum_supported_version=1`, `mandatory_after=0`); it grants
no VPN entitlement. Existing125 and older immutable downloads are retained. No user
broadcast or test payment/message accompanies publication.

## Accepted user and operator result

The installed corrected126 has passed the real path: explicit consent → authenticated
API → canonical latest-only storage → generation2 collector → original device card
in the working panel. Manufacturer/model, Android/API, app/versionCode, available
underlay/mobile information, distinct preference/attempt/session, gateway and bounded
errors carry their source/time/unavailability. The panel supports corresponding
filters and1440/390px compact/details/freshness/navigation views. Open the existing
authenticated panel at `http://127.0.0.1:8765/inventory/`; no new account/password or
direct registry/SSH access is added to its web container.

Physical preservation is **original125 → first signed126 → corrected126**, not a
direct125→corrected126 test. The recorded checks retain identity/activation, UID and
first-install time, bounded settings, both saved split-tunnel applications, support
fingerprint, four observed history rows and subscription/access. Keystore keys are
not exported. Restart, Wi-Fi/cellular transitions and real online/offline revoke are
accepted in the [installed-device receipt](2026-11-15-device-technical-metadata.md).

Consent is separate, OFF by default and never inherited from seven-day diagnostics.
It lasts until disabled; hardware and dynamic groups each expire independently within
seven days. Off immediately stops local collection; offline revoke is pending until
server delivery. Revoke/restart/online cleanup and delayed-report rejection pass;
TTL/clock/replay coverage remains isolated, without changing production clocks.
At20:19:39UTC canonical and panel are still revoked, epoch6/sequence116, zero groups
and no geographic projection. No support ACK refreshes the age of old observations.

Real RU/AWG geography joins the authenticated canonical AWG key to a recent peer
endpoint and local DB-IP Lite2026-11. It matches the real panel, not a synthetic
city. This proves database attribution, **not physical location**. NL/TCP/MESH lack
a qualified direct-IP source; show unavailable or an independently aged suitable
observation. No raw IP, coordinates, phone number, IMEI, contacts or traffic content
is added to telemetry. Radio/dual-SIM detail depends on public Android APIs and the
actual data SIM; physical5G/dual-SIM remain NOT_OBSERVED. Missing/stale GeoIP does
not block VPN, subscription or support. DB-IP attribution remains visible.

Final observed phone state remains consent OFF, original NL1, VPN disconnected,
Wi-Fi/mobile ON, airplane OFF. Later ADB is absent: this publication performs no
phone operation and does not claim removal of the temporary probe or restoration
of USB debugging. A new physical125 updater-button installation is NOT_OBSERVED;
protocol/HTTPS checks do not substitute for it or repeat the already completed
two-step in-place device preservation.

## Compatible production foundation

Exact paid policy remains `android-paid-108-119-123-125-126-v2`, source
`408fb282421ce180a8e28803a1857c7d4adb5d99`: exact108/119/123/125 retained, only the
signed4f288cbb descriptor accepted for126; existing access is version-independent.
The accepted153 focused/501 locked paid and7 overlay checks are not rerun as real
operations. Loaded HTTP4e2df679, operator19efd0b4 and reconcilerff4601aa are unchanged.
Panel image5ae92f8c and readonly HMAC2 manifest8602e652 remain. No old key is reactivated.

At20:02UTC watcher/AWG/TCP retain the accepted recovered PIDs with NRestarts0. HTTP's
19:54:54→19:55:34 stop/start is a successful scheduled credential renewal COMMITTED
at19:55:39, with unchanged HTTP archive; it is not a new transport outage. The bounded
selected-journal diagnostic exits and its unit is not-found/inactive/PID0. Original
failed continuity evidence is retained; only proven recovery/renewal PID anchors are
refreshed, without removing archive/service/manifest assertions.

Fresh ordinary imports at20:20UTC are healthy for all three transport sources, RU
inventory, subscriptions on the accepted HTTP pin and metadata. Support IPC and the
original baseline/cursor position4, baseline time1794660500, matching anchor and four
excluded events pass at20:19UTC. No selected-device jobs/source error or observed new
real notification delivery. No historical baseline is recreated.

## Guarded publication and recovery

-20:32:38UTC: all ten applicable workflows on pre-publication head
  `43da3339252bf2a2d2d1b6489af74ffc35eeb006` are SUCCESS, including Android133562778411
  in Client builds43942290805, Linux, Windows and Windows compatibility. Artifact
  source, later test-only source, this head and final documentation/merge checks stay
  separate. No parallel manual rerun or weakened IPv6/timeout assertion.
-20:32:51UTC: fresh four-file ownership/hash backup and isolated restore PASS; intent
  journal initialized without public changes. Four isolated publication scenarios
  also pass: normal two-phase/restore, concurrent change, interrupted reload/replay
  rejection and invalid syntax. Initial local harness setup errors (wrong entrypoint
  and undersized tmpfs) are not product PASS; the corrected isolated run retains the
  original free-space assertion and memory/CPU/no-network limits.
-20:36:21UTC: all three exact assets staged.20:36:37UTC: route-only exposure and first
  nginx reload, catalog/invitations unchanged.20:39:47UTC: all three complete HTTPS
  sizes/hashes PASS; three byte ranges206, unsatisfiable range416 and If-Range resume
  reconstruct the exact full APK hash.20:41:29UTC: downloaded APK signer/package/code,
  ARM64/API27 and16KiB alignment PASS.
-20:42:17UTC: invitation/CSP configuration and second nginx reload, matching legacy
  descriptor, then signed catalog9 last.20:42:19UTC: both invitation paths/CSP,
  signed catalog signature/sequence and exact legacy equality PASS;20:42:22UTC
  completion receipt. No HTTP/VPN/watcher/support restart or database migration.

The exact original125 `AppUpdate.java` and `AndroidUpdateManifest.java` also pass a
separate JVM check against **actual public HTTPS**: original signed8 → public signed9,
legacy equality, optional/API31 policy, then the original downloader reads and verifies
all50,478,496 public bytes. Its pre-publication negative check correctly rejects125 as
not yet126. Dependencies remain Gson2.13.2/Bouncy Castle1.85.2. This is not Android
instrumentation or a new physical updater UI installation. After publication the full
service/archive/HMAC/image/consent guard passes; support IPC/original baseline/cursor,
anchor/excluded history and absence of selected-device jobs pass again20:43:52UTC.

Recovery retains published immutable assets, generation2 and all new user data.
Use the journal and compatible ingress configuration; never erase an uncertain intent,
replace a published binary, lower signed sequence9, restore an old DB or reactivate
the old HMAC key. A catalog correction needs a higher signed sequence. The qualified
[two-phase runbook](../operators/technical-metadata-release.md#guarded-public-delivery)
defines reconciliation before retrying any incomplete step.

## Source integration

[PR38](https://github.com/Joker20380/family_connect/pull/38) carries the signed public
catalog, invitation source, exact126 regression pins and preserved signed125 fixture,
plus RU/EN/privacy/release documentation. Reviews are **self-review**, not independent
approval. The final delivery delta passes146 focused public-release/paid-policy and
29 invitation checks in the existing locked paid environment; dependency consistency
passes. Documentation18files/1253links and whitespace pass. The preserved125 catalog
still verifies its exact original signature/size/hash; no old admission pin is removed.
Ordinary integration requires the final head's applicable checks; its exact
head/merge/main result belongs to the PR check and merge receipts, not to the older
artifact-source qualification. Publication does not install the complete PR on RU.

## Final-head CI failure and evidence repair

Head `a1d5f63230d19f7d47196bb3d8740b46b78ea61d` is published to the feature branch,
not merged. Its two Client builds runs fail independently:

- Push43953914583 / Android133603441862: API35 lifecycle step fails. The main
  debug73/Friends26 XML contains zero failures/errors (41/4 conditional skips).
  The independent per-app artifact is absent; this neither proves its success nor
  identifies a failing assertion. Retained runner logs stop before usable per-app
  evidence. The connector's full console result is truncated, not a complete trace.
- PR43953925878 / Android133603450734: separate per-app API35/27/28 each reports
  `OK (10 tests)`. API31 executes10 with one failure:
  `serviceConnectPendingAndResumeUseDifferentSnapshots`, line227, then `route`,
  line49: DNS absent/empty after service resume. IPv4 and TLS assertions immediately
  before that assertion pass for the same probe. The missing service receipt prevents
  identifying which UID in the pair and the DNS error. Do not infer a TCP/IPv6 fault,
  an infrastructure-only cause or a product fix from these incomplete observations.

All other nine applicable PR workflows, including phase0/failover, pass. Main runtime
and independent routing results remain separate. These failures do not replace the
prior accepted artifact/source/device receipts, but block a claim of full final-head
CI success and ordinary PR integration. No new APK is built, signed or selected here.

Downloaded evidence is hash-verified; no device/private production data is included:

| Artifact | SHA256 |
| --- | --- |
| Push runtime14272594793 | `113decfce8d0afc6e5c8bbb01c9d4ed4064eb474d9fb8538cc53b7b948b9e120` |
| Push debug14273550930 | `8a836369c9f61cefabf686b406f05e3b9bf989beb9760468586eab8dd31e5d96` |
| PR routing14274916972 | `5b7639e579b1f3152bfea38e73473f58d11d1065ac47a9d05ac6a81b258c46a6` |
| PR runtime14274861885 | `c4afa7bebb152bab5698313f53285a5ba7c5b284345fe4d822962849e46d6c26` |

The minimal diagnostics correction keeps all existing conditions and timeouts:
include the already-collected `service.json`, retain outer harness output with
`pipefail`, explicitly include fixture/peer logs and synthetic traffic receipts,
and attach the synthetic probe observation to assertion messages. Do not upload
the whole fixture directory, its generated key/certificate or arbitrary runtime
files. This is evidence repair, not an assertion failure/root-cause fix. The next
actual run must supply its own result; no automatic repeated rerun until green.
Local evidence-retention/fixture/public-release regression checks pass28 tests in
the existing locked environment; whitespace passes. They are not instrumentation.

## Qualified source and ordinary merge

At22:43:46UTC source `588e793a5833bc50397a44f2c41d82e802c37a0f` has **all ten
applicable PR workflows and four push workflows SUCCESS**. Android PR job133637121094
(run43963581094) and push job133637065919 (run43963566707) both pass. The test-only
evidence repair changes no installed Android/native executable or assertion budget.
Earlier a1d5f632 failures remain retained and unexplained; success is not an
infrastructure attribution or proof that a routing implementation bug was fixed.

Routing artifact14278048563 is65,849bytes, SHA256
`7809c923ebc99cfd2a8fad1463d6ea22780f724a30a4be746de0208bf445c96f`.
Each API35/27/28/31 reports10 passed independent tests and ten service observations
without DNS errors. Harness/fixture/service receipts are actually present; no PEM/key
is uploaded. These results are distinct from the main99-case enumeration and from
physical Redmi acceptance. Current source differs from artifact sourceba3e9370 in
later server/docs/test work, not the installed Android executable.

The author's review5929226637 is explicitly **self-review**, not independent approval.
PR38 moves from draft and merges normally with expected-head588e793a as
`7123b95e83e1d5dc592492ba6104d04ebcf8178d`. Remote main matches. Merge parents are
main53a780d9 and qualified588e793a; the merge/source trees both equal
`7a264ca6a3fdb8381992bc0aacce8bf7658fbb17`. No full main/PR deployment follows merge.
Merge-head workflow results remain separate; tree equality is not a new CI execution.

The new RU incident is disclosed before integration. At22:30UTC the selected metadata
is still revoked, epoch6/sequence116, zero canonical/panel groups/no geography;
HMAC2/manifest and support IPC/original baseline/cursor/excluded history pass.
At22:31 HTTP2394053/peer3967036 remain active, but AWG is failed and TCP inactive after
the22:07:37 watchdog cascade. Accepted node/gateway/effective unit hashes are unchanged.
No user message/payment, transport restart, DB restore or old-key reactivation occurs.
Source integration and the publicly downloadable release do not close this separate
availability incident. Final receipt updates are documentation-only, not another
Android candidate or permission to start an unrelated queued task.
The documentation-only closure checks six files/509 links without errors and passes
whitespace review. No private identifiers, mapping, raw endpoints or keys are included.
