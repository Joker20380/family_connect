# FIELD export(6): readiness gate, not established-session loss — 2026-10-04

## Scope and input

User supplied `FamilyConnect-diagnostics(6).json`,22263bytes;
SHA256 `7db756a9ac575fc40eda303a30529f89d17d1fcfdc50336e95a044608130d5e5`.
Support ID FC-YHQB-9VJN unchanged; export reports `0.1.18-beta61`/code61.
That version pair alone cannot attest the exact installed APK bytes or distinguish
original61 from accepted r2; no such signer/hash claim is made from this JSON.
Approved r2 delivery remains [verified independently](2026-10-04-beta61-r2-direct-delivery.md).

Initial investigation was read-only: no credential renewal or service restart.
The subsequently authorized prerequisite restoration is recorded separately below;
no admission/catalog/Support change, APK/device mutation or new test attempt performed.

## Client timeline (UTC)

| Time04.10 | Evidence |
|---|---|
| 08:27:59.844 | READINESS `EXPIRED_ON_IMPORT` before connect |
| 08:28:06.614 | CELLULAR Auto connect begins |
| 08:28:10.183 | READINESS refresh `FETCH_FAILED` |
| 08:28:32.184 | AWG `NETWORK`, after repeated DNS probe failures |
| 08:28:54.491 | TCP `NETWORK`, after repeated DNS probe failures |
| 08:28:58.632 | Restricted candidate starts |
| 08:28:58.743 | Restricted readiness `NOT_READY`, directory `NOT_USABLE` |
| 08:28:58.765 | Restricted `BOOTSTRAP_UNAVAILABLE` |
| 08:28:58.859 | Terminal FAILED after52.244s; VPN capture still open |
| 08:29:05.756–05.838 | Explicit cancel/disconnect, VPN released |
| 08:29:16.325 | Later connection begins; latest ring identifies WIFI |
| 08:29:23.552–23.580 | DNS probe OK, AWG CONNECTED after7.244–7.257s |

Failed connection ID `11cea884-22ce-4b90-8e67-e365320539af`;
incident ID `c7594804-0855-4748-becb-6f68cac4c9f9`.
Latest Wi-Fi connection ID `22ee62e1-f540-4edf-b45c-96c6757664ec`.
Both records have an empty restricted_session and empty restricted_history.
No restricted CONNECTED transition, native lifecycle or valid SetupID/tag appears.

The observed `NOT_READY` path in `RestrictedTunnelEngine.up` rejects a null usable
readiness response with BOOTSTRAP_UNAVAILABLE before NativeRestricted.beginReady.
RestrictedCache reports EXPIRED_ON_IMPORT when the saved response expiry is past.
Thus this export cannot provide an end-to-end restricted-session join: the correlator
returns no sessions. Absence of a tag here is not evidence that the32-byte tag fix
regressed; no valid restricted session identifier was produced in the recorded path.
Nor is this a reproduction of the prior15/30-second loss after successful connection.

## Independent read-only server evidence

RU observation08:32:49UTC: exactly2 devices admitted and non-revoked. Existing tester
grant revision1; latest recorded successful fetch/READY/ACK remains03.10 19:42:48–49UTC,
beta60/code60, expired03.10 19:57:16UTC. No fresh usable tester READY/ACK is recorded.
This is not a complete HTTP access-log audit and does not prove no packet/request
reached the server. FETCH_FAILED by itself does not identify the network/HTTP cause.

NL observation08:32:49.711UTC: bootstrap unit active, PID3747690/NRestarts13;
loaded executable SHA256
`b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217`.
Profile and actually served TLS certificate match and both expired
**2026-10-03T21:18:57Z**, before this client attempt. Issuer expiry is04.10 14:13:53UTC.
Directory issued04.10 08:21:50.681849059UTC, expires09:16:48.224598146UTC.
A fresh directory and an active process do not make an expired gateway TLS certificate
valid. The gateway certificate is an independently confirmed blocker for a later
successful restricted session, not an established causal explanation for the earlier
mobile readiness FETCH_FAILED. No attribution is made from the restart count.

## Decision and next gate

Do not repeat the mobile test now. First renew gateway credentials through the existing
protected procedure and verify the actually loaded certificate, current issuer/CRL/
directory and unchanged admission. Then obtain fresh normal tester readiness over
working Wi-Fi and verify server READY/ACK before switching networks. Preserve the
existing enrollment/Support; no uninstall, data clear, new invitation or expiry bypass.
Only then coordinate one mobile attempt with immediate export and bounded server
evidence. No RKN/network-filter attribution, transport change or original-defect fix
claim is supported by this export.

Bounded privacy screen PASS; no prohibited key/token/room fields found. Client
correlator correctly reports no sessions. Safe metadata/timeline and server expiry/
readiness receipts are retained privately under `state-client-build/field61-r2-diag6/`;
raw diagnostics, credentials and database contents are not committed. No product code
changed or rebuilt; rollback is unnecessary for this read-only investigation.

## Authorized prerequisite restoration

After the user authorized continuation, the existing protected credential-only
[gateway renewal procedure](../../deploy/friends/restricted/GATEWAY_RENEWAL.md)
completed04.10 08:39UTC. No runtime rebuild/deployment, Android installation,
new enrollment, admission change or credential-lifetime extension was performed.

- Same issuer/gateway/Family identities; delegation3, unchanged grant revisions
  owner3/tester1, minimum revision1. Exactly2 admitted,26 non-admitted devices denied.
- Python/native positive and negative validation PASS. Atomic gateway publication
  retains discovered service UID/GID979, mode0600; independent service-readable
  readback PASS. Provider token not read; secrets not logged.
- New gateway certificate expires04.10 **09:39:30UTC**, issuer expires**14:13:53UTC**.
  Actual listener certificate matches renewed profile; issuer/hostname validation
  PASS. NL PID3757156/restarts0, stable35-second observation PASS.
- Same loaded diagnostic binary SHA256
  `b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217`.
- New directory issued08:39:34.925582899UTC, expires09:34:32.702517154UTC.
  At08:42 RU/NL directory SHA256 matches
  `541fd9aeabd0ef8a53fd0c4ffed77403c0e43efd45d43c237b3aee9d44dac49a`.
  CRL3527 signature/sequence/expiry agree, expires08:56:49UTC. Existing RU sync timer
  restored/active; subsequent CRL updates remain the ordinary sync's responsibility.
- Before/after DB row digests for devices/invites/grants/audit, Support mapping,
  admission file, HTTP executable and ordinary HTTP/AWG/TCP process/start fingerprints
  match exactly. No production distribution/landing changes; beta60 default retained.
- Public HTTPS readback08:44:27UTC: both signed/discovery Android catalogs and
  `/invite/` return200 with TLS verification and exactly their accepted pre-operation
  hashes (`f042beca…`, `6e5817dc…`, `014ebdbd…`). Catalog/default remains beta60/code60.
- At08:42 server ledger contains tester beta61/code61 normal READY/ACK from08:34:46–47UTC,
  expiry08:49:22UTC. It predates renewal, so is not proof of post-renewal directory
  import. Owner READY remains expired; not substituted for tester acceptance.

Private receipts: `state-client-build/field61-r2-readiness-20261004/`, including
gateway-renewal loaded/validation/invariant receipts and bounded follow-up reads.
An initial follow-up metadata reader incorrectly expected an unwrapped issuer JSON;
it failed read-only before producing a result. The reader was corrected to use the
existing signed-delegation validator; successful RU/NL observations are cited above.
No server retry or mutation was performed for that local reader error.

Protected server backup/receipts on the authorized hosts:
`/opt/apps/family_connect/restricted-materials-stage-20261001/field61-r2-gateway-20261004-diag6`.
Do not restore the expired old certificate as a healthy rollback or lower CRL floors.
On a future failed renewal, stop acceptance, inspect durable publication/readback,
and follow the same protected procedure preserving current monotonic security state.
No runtime binary rollback is needed; binary was unchanged.

Remaining gate: ordinary tester post-renewal READY/ACK over working Wi-Fi, while the
main Family Connect screen remains foreground. Respect normal five-minute backoff
and renewal only when cached expiry is within five minutes; no data clear or forced
cache writes. Then coordinate exactly one mobile attempt within validated leases,
export immediately after failure/disconnect and correlate server/client evidence.
No mobile attempt was initiated here; original restricted-session defect stays open.

Post-renewal observation: tester challenge08:44:55UTC/fetch08:44:56UTC, revision1,
CRL3532, delivery expiry08:59:30UTC. The same device sent an authenticated beta61
failure ACK at08:44:56UTC: `NATIVE_VALIDATION_FAILED`, provisioning/bootstrap
`NOT_READY`, `orchestrator_usable=false`. This is not a successful READY or restricted
session. Client receipt `observed_at` is08:44:55UTC, one second before server fetch;
this cross-clock difference alone does not prove which native validation branch
failed. `DeliveryValidationCode` deliberately returns the same general code1 for
multiple non-directory validation failures; no exact cause or clock repair claimed.
Bounded polling later lost SSH with exit255 (error text withheld); no server write
was retried. A second bounded read-only observation window follows normal app backoff,
not a forced refresh, mobile connection attempt or security bypass.

Final observation08:51:02–03UTC: next ordinary tester challenge08:49:55/fetch08:49:56UTC
again receives an authenticated `NATIVE_VALIDATION_FAILED` ACK, client observed_at
08:49:55UTC, CRL3541, no usable readiness. No mobile test is authorized by this failure.
After a second transient SSH exit255, the final independent read succeeds on both
hosts: PID3757156/restarts0 and loaded binary/certificate unchanged; RU/NL directory
bytes still match and signed CRL3543 matches, valid until09:05:33UTC. Existing sync
service last exit0/success, timer active. No server data/security repair was attempted
in response to the client import failure. All bounded observation processes ended.

Outcome: expired gateway certificate repaired and verified; tester import remains
**BLOCKED**. Next evidence needed is a fresh diagnostic export from the tester while
on working Wi-Fi, followed by native-import/time validation investigation. The one-second
receipt/server difference is a lead requiring verification, not a proven root cause;
do not loosen validity checks, alter TTLs or claim the original transport defect fixed.

Validation: focused repository documentation check3 files/354 links PASS;
`git diff --check` PASS. Bounded JSON receipt/private-key/Bearer screen PASS with
zero findings (not a proof against every possible secret encoding). No product code
changed, so no Android rebuild or product regression suite was run for this operation.
