# FIELD-1-VOLGOGRAD-EXPORT17 — authorization blocks transport startup

**RESULT=TESTER_NOT_AUTHORIZED / PRE_TRANSPORT_AUTH_FAILURE.**
The owner supplied an ordinary export from the already selected tester, alias **T1**,
reporting inability to connect in Volgograd. This is a new tester observation, not
owner export13, historical A/B, or a completed controlled single-CONNECT field trial.
Input review: `af872ebe0dcc4beda244905ee4a06d9a6c06c9a9`.

## Evidence and artifact boundary

Raw export retained privately, unchanged,49,491 bytes, SHA256
`af1e8d8804337dcc9607376e8a1d7a57481aa75532ee7c858a0e8c0fe61ccac8`.
Private acquisition receipt separates collection time from exported event timestamps.
Both surfaces match the selected recipient; no real identifiers are published.

- Export reports `0.1.18-research84-ui60-4-batch1`, code84, Android14/API34.
  Thus the former beta60/not-transferred preparation state is no longer current.
- Prepared signed APK remains
  `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f`;
  expected native
  `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23`;
  retained source inventory
  `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790`.
  These are preparation identities, **not a fresh installed-byte verification**.
  The export does not establish installed checksum, signer, model or ABI.
- Both saved surfaces have network_class=WIFI. That is a snapshot, not a per-attempt
  underlay history. Cellular operation, operator and actual whitelist restrictions
  are not established by this file. Location is owner-reported.

## Separate connection lifecycles

All times are17October2026 UTC from the client wall clock. Failure duration is the
exported elapsed duration, not wall-clock subtraction (occasionally differs by1ms).
Aliases E1–E8 are local to this report and distinct from tester T1 and prior episodes.

| Attempt | CONNECT | First FAILED | Code / elapsed | Final app OFF |
|---|---|---|---|---|
| E1 |10:36:55.888|10:36:56.147|AUTH /260ms|10:37:19.844|
| E2 |10:37:22.015|10:37:22.123|AUTH /107ms|10:38:05.889|
| E3 |10:38:14.907|10:38:15.026|AUTH /119ms|10:38:57.196|
| E4 |10:44:16.117|10:44:16.200|AUTH /82ms|10:47:20.076|
| E5 |10:47:28.208|10:47:28.332|AUTH /124ms|10:49:08.235|
| E6 |11:42:42.502|11:42:42.615|AUTH /112ms|12:19:53.655|
| E7 |12:21:16.303|12:21:16.313|CONFIGURATION /11ms|12:22:31.103|
| E8 |12:23:08.652|12:23:08.665|CONFIGURATION /13ms|12:23:33.055|

E1–E6 select restricted and create a local VPN capture, then reject authorization.
VPN_CAPTURE_READY is not a working restricted connection. All retained retry_count
values are0; eight distinct connection lifecycles are observed, not eight independently
verified human button presses. Assistant-directed CONNECT actions in this task:0.
Long periods spent in FAILED, especially E6, are not successful tunnel lifetimes.
Later CANCELLED/disconnect events do not replace the first AUTH failures.

The readiness stream records AUTHORIZATION_REJECTED eight times, starting10:31:01.407,
before E1, and ending12:19:49.986. A separate FETCH_FAILED at10:44:07.715 does not
erase the earlier rejection or prove a specific mobile-network fault.
No native startup, session, early bootstrap exchange, dedicated tag, traffic or DNS
counters are saved. No HELLO wait, broker holder or server challenge is assigned
by temporal proximity. HTTPS and throughput are NOT_EXERCISED by this evidence.

## Fresh recipient-only server readback

One read-only SSH call,12:28:06.746–12:28:09.085UTC, reuses the existing configured
`support_ids.lookup` through SQLite `mode=ro` and `query_only=ON`. No Access constructor,
schema migration, other-recipient enumeration, credentials or personal correspondence.
The supplied export's recipient is checked against the previously selected T1.

- Active registration, not revoked.
- `family_state=NOT_PROVISIONED`, `field_admission=false`, readiness UNKNOWN.
- Latest server-reported version is also batch1/code84. Its support observation is
 10:46:09UTC, not the12:28UTC collection time and not independent APK attestation.

This confirms an actual outstanding restricted entitlement/provisioning blocker,
consistent with the client's authorization failures. It does not turn every AUTH
event into a separately matched HTTP request: no per-request HTTP status/receipt
or server exchange correlation is available. Gateway loaded identity, TLS/security
windows and scheduling were not re-audited; old readiness is not asserted current.

Owner permission to issue T1 access is already retained. The earlier
[installed admission-tool incompatibility](2026-10-17-field-1-volgograd-grant-preflight.md)
remains unresolved by this task: legacy validation accepts at most1h CRL duration,
while current4h uses4h; the old publisher hardcodes15min. No incompatible grant writer
was run, validator bypassed, policy shortened or manual SQL/profile edit performed.

## Exact client source interpretation

Read only the relevant retained batch1 Java sources, not the dirty root Android tree:

- `FriendsAccessAndroid` / `FriendsReadinessProtocol`: authorization failures from
  readiness/challenge401/403 are distinct from unavailable/fetch failures.
- `RestrictedBootstrap.refresh`: maps authorization rejection to
  AUTHORIZATION_REJECTED and rejects cached authorization rather than using it.
- `FriendsRestricted`: records the denial; `check()` throws AUTH before
  `RestrictedTunnelEngine` can call `NativeRestricted.beginReady` on that path.
  Only successful READY clears the denial. Repeated CONNECT is not an entitlement fix.
- `AutomaticConnection.configure` opens the local VPN before selecting a candidate;
  this explains local capture events without native restricted readiness.

E7/E8 are separate pre-candidate CONFIGURATION failures, without new capture-ready
events. `AutomaticVpnOwner.open` rejects an already active VPN at this boundary;
`ConnectivityOrchestrator.classify` also maps IllegalArgumentException to the same
code. The export has no stack/specific exception or active-VPN roster. Another VPN
is a possibility, **not established fact**, and does not explain away E1–E6.

## Retention and final state

- Ring71 events, incident69; incident events are exactly a prefix of ring, not a
  second independent episode. Incident ends at E8 failure; ring includes its OFF.
- Exact source retains128 ring events; no ring drop scalar is exported.71 retained
  events does not establish absence of an earlier process/session history.
- Restricted startup/session objects and counters are empty; history array empty.
  Session archive cap4 exists in source, but absent counters are NOT_RECORDED, not0.
- Record bound256KiB per surface; bundle bound2×256KiB+1024. Raw49,491-byte bundle
  is within bounds. This is not evidence that all prior observations were retained.
- Last observed app state DISCONNECTED, vpn_capture_open=false at12:23:33.055UTC.
  No ADB/current OS VPN inventory: do not claim every third-party VPN is OFF.

## Next step and action counts

No reinstall, identity replacement, cache/data clearing, forced reconnect or transport
tuning is indicated by this rejection. Next is a separately scoped compatible
admission workflow, preserving current policy, keys, floors and revocations, followed
by the already authorized recipient grant. Do not ask again for grant permission;
do not silently expand it into management-code deployment under this diagnosis.

After authorized provisioning succeeds, refresh own delivery/ACK on a working network,
resolve any remaining configuration conflict, then perform fresh field prerequisites.
No further tester CONNECT is requested now. No whitelist or performance verdict;
FIELD_WARM_START remains blocked, not a demonstrated carrier failure.

Actions: supplied export analyzed1, private immutable copy1, read-only SSH1,
targeted retained-source inspection and deterministic evidence checks. New export
requests/ADB/install/build/sign/grant writes/CONNECT/service changes0. Product/native/
gateway bytes and settings untouched by this task; no rollback or release. Historical
causality, handoff, supervisor and existing acceptance scopes remain unchanged.
