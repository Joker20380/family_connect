# GATEWAY-FATAL-CAUSE-1 — gateway-only observability

## Result and scope

**GATEWAY-FATAL-CAUSE-1=PARTIAL. OBSERVER_ARMED_NOT_TRIGGERED.** Observation-only
candidate loaded; finite900.025s passive window completed without a fatal exit.
PROCESS_EXIT_CAUSE=UNKNOWN; historical missing causes are not reconstructed.
No owner CONNECT/startup/prewarm/native beginReady, phone provisioning refresh,
cache import, APK build/update, FIELD or synthetic production failure.
OWNER_CONNECTS=0; FULL_PHASE_REQUESTS=0; ATTEMPT_CONSUMED=NO.
READY_FOR_CLEAN_RETRY remains NO; a separate cache/runtime preflight is required.

Evidence root: `state-client-build/field65-export16/gateway-fatal-cause-1/`.
`RESULT.json`, research manifest, full source diff/thin source bundle, exact binary
and local/live receipts are sealed by **65 SHA256 entries**. The bundle requires
the preserved baseline f5240994; it is not advertised as a standalone full clone.
Previous sealed157+2+168+21 entries verified unchanged. Main dirty product tree was
preserved; changes live in a separate local clone/validation commit, not a transport
patch in the working tree. Existing egress/lease acceptance is not re-run.

## Exact subject and pre-change evidence

Fresh read-only owner check19:04:20–21UTC: package `com.familyconnect.app.friends`,
research83 `0.1.18-research83-bootstrap`, code83, UID10283, non-debuggable; APK
`7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`.
Identical APK binds the previously verified signer
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`, source
`f5240994869826c6a28f59e58e38256c688cf6eb`, embedded schema2/restricted metadata,
and native SHA `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
No signer/key extraction or change; no owner Activity/instrumentation/helper.

Fresh NL19:04:09UTC: PID768197, invocation78333d45f8cc450a85fc8473db811485,
start18:45:56UTC, NRestarts2. Loaded/next baseline
`5e877eb1355ed4a65bda31be0594299c70002c7a3e96f9d7a528e9e1bb6fe81f`.
Directorya20c2622…820cd, issued18:45:59, nominal expiry22:45:56UTC; RU/NL equal.
Leaf3ac25859…0274 expired17:49:16UTC. Strict server-only TLS rejected expiry;
actual verified DER equality was not reached. Authority/grants expire21:37:28UTC.
Exact unit/drop-in hashes/argv/public validity/CRL/floors are in `receipts/nl.json`
and `ru.json`; provider environment values and raw profiles were not exported.

During preparation, **before observer activation**, another autonomous restart
occurred: predeploy19:17:29UTC sees PID786763, invocation
648e0c28374b40bca6a36ef2e99d556c, start19:17:07UTC, NRestarts3; same baseline
binary, directory81998feb…1e068. This predecessor's exact exit time/cause is not
captured. Do not infer it from the next start, expiry, or nearby renewal operation.
No broad unit/kernel query was repeated; historical TIMEOUTs remain limitations.

## Later evidence, captured 12.10 — separate follow-up

The original900s ARMED_NOT_TRIGGERED result below is retained as historical.
[WHITELIST-EXACT-SELECTION-1](2026-10-12-whitelist-exact-selection-1.md) later copied
13 exact observer/systemd receipts: dd70…3384a completed normal4h deadline exit0
at11.10 23:19:05UTC; five subsequent automatic startups failed PROFILE /
CREDENTIALS_REJECTED with expired credentials, first23:19:36UTC. New typed cause
PROVEN for those startups; pre-observer historical causes still UNKNOWN. No manual
restart or artificial exit. Current failed/MainPID0/NRestarts6; readiness remainsNO.

## OBSERVABILITY_SOURCE_AND_BINARY

- Isolated source commit `abc604b0f8ce431174f260ff41ef9b3b6455ba0c`, tree
  `687b25443956e47cb1317227d8cb9c881a79e3aa`, clean; base f5240994/research83.
- Gateway-only binary SHA256
  `0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`.
- Same Go1.26.1/amd64 build, `-trimpath`, embedded VCS revision and modified=false;
  `receipts/build-info-final.txt`, full minimal `receipts/source.diff` retained.
- No Android, Telemost implementation, Family TLS, Reliable/Mux, admission,
  lease renewal, retries/limits/timing constants, directory generation or restart
  policy changes. No dependency or framing change.

## Error path and limits

`main → run → SeedManager.Run/runOverlap → ServeCarrier/provider → seedDone/httpDone
→ main` previously discarded the returned error and printed only
`bootstrap broker stopped` before exit1. Seed creation/receive/send/publication
also collapsed lower errors into existing broker codes.

New optional in-memory observation captures the pre-cleanup cause/stage without
changing the original return object/code. The overlap manager forwards only the
selected terminal generation; retiring old seed/failed optional rotation cannot
become the process's first fatal cause. Main records its selected return before
cancel/close, finalizes the receipt after its ordinary defers, then retains exit1.
Parent cancellation/deadline is recorded distinctly, not blindly called fatal.
The old shutdown select race is **not fixed** by observation.

Classification reuses startupdiag and bounded roombroker codes; function-boundary
stages identify seed create/connect/read/admission, publication, broker/listener
or HTTP Serve. Unknown raw errors stay UNKNOWN. Lower errors already discarded
inside TelemostSeed/provider are not reconstructed. The observer does not claim
to reveal every signaling failure or every library goroutine's first-close source.

Panic capture covers main and the directly owned seed/HTTP goroutines; category
is redacted, exit2 retained, no panic value/stack exported. Uncaught library/child
goroutine panics, early flag-parser exit, SIGKILL or OOM may have only the manager
receipt. Exit2 alone is not a panic diagnosis. These limits remain explicit.

## RECEIPT_SCHEMA_AND_PRIVACY

Application schema1: UTC timestamp, monotonic elapsed, invocation/PID, executable
hash/source revision, exit path, last confirmed/first stage, first safe cause/class,
seed generation, parent-context state, fatal flag, signal, directory SHA,
credential startup limiting expiry/headroom, lifecycle, cleanup started/completed.
Directory generation is ABSENT_V1, separate from seed generation. Credential
snapshot is labelled STARTUP_NOT_AUTHORIZATION: it does not substitute current
CRL/profile checks or extend credentials when directory lifetime is longer.

Application directory `friends-restricted/fatal-application` is service-owned979,
0700. Manager directory `friends-restricted/fatal-systemd` is root-owned0700.
Each layer retains at most32 completed0600 JSON files, ≤4096 bytes each. Temp files
are cleaned on the next write. Atomic exclusive hard-link publication refuses to
overwrite an invocation; first cause stays sealed against cleanup/stale callbacks.
App writes outside broker/session/observer locks, on terminal path only, with no
network/SSH/journal. Write failure does not change the exit cause/code.

Root `ExecStopPost` uses installed systemd259's actual INVOCATION_ID, SERVICE_RESULT,
EXIT_CODE and EXIT_STATUS. A bounded2s local `systemctl show` adds only matching-
invocation PID/NRestarts/start/end/status fields. Supported variables were tested
on local systemd259 before loading. Manager failure is ignored, not a new restart
decision. No public endpoint, profiles, keys, identity, tokens, room URLs, SDP,
payloads or arbitrary error text in either receipt.

Fresh ancestor-DAC audit confirms root helper cannot be replaced by the service:
Family root is root0755; live directory is root:979 **1770/sticky**; `bin` is
root:9790750, helper root0644; root manager directory0700. The sticky parent protects
root-owned entries despite service group write access needed by the existing cache.
No permission or sandbox relaxation was required.

## LOCAL_BEFORE_AFTER

- Actual baseline and candidate run with `--duration=0`: same exit1 and exact
  generic stderr; candidate additionally records typed invalid_options. No network.
- Typed/wrapped/unknown errors, provider and broker failures; deadline versus parent
  lifetime/cancellation; normal stop, SIGTERM and redacted panic/exit2 checked.
- Write failure, immutable first cause despite late cleanup/stale callbacks,
  sequential invocations, exclusive writes, modes/retention and privacy scan PASS.
- Existing real Family overlap/admission test now also proves expired old generation
  does not report process fatal; prior directory/admission assertions unchanged.
- `go test -race ./cmd/bootstrap-broker ./bootstrap ./roombroker -count=3` PASS.
- Real local systemd normal/exit7/SIGTERM fixtures confirm result/status/InvocationID
  and monotonic boundaries. Initial fixture quoting issue and test-directory mode
  mismatch were fixed locally before deployment; original failed logs preserved.
- Full product suite/UI marathon not run. Six historical negative-auth diagnostic
  assertions remain a separate known issue, not weakened or relabelled green.

## DEPLOYMENT and CHAIN_AND_PUBLICATION

Expired-chain evidence preserved first. One accepted AKI-corrected same-key gateway
renewal published19:16:40UTC, native positive/negative checker PASS. Existing root,
authority keys, issuer sequence10, admission, grants/revocation bindings and revision
floors preserved. Normal gateway4h policy capped by existing authority expiry:
new leaf06c2c41e…d1a17 valid19:16:08–21:37:28UTC; no arbitrary TTL extension.
RU sync timer paused only for serialized publication and restored; no owner refresh.

Exactly one controlled restart19:19:05UTC. New invocation
dd70fcd8467847bea72b7aba20d3384a, PID788144, NRestarts0 after the manual counter reset
(previous invocation had3). Loaded=next observer0ccaaf81…2667a; argv retains
`--duration 4h --chat-services --seed-rotate-after 3h` and all existing bindings.
Only executable path, receipt environment and ExecStopPost added via
`99-zzzzzz-fatal-observer.conf`; full drop-in preserved in reconciliation receipt.

Deployment command returned an unlocated post-restart AssertionError. It was **not
replayed**. Independent bounded readback established matching loaded/next/argv,
observer env/InvocationID, correct permissions and unchanged ordinary service PIDs.
The exact failed immediate postcondition was not retained; do not invent a cause.
No second restart/rollback occurred. Strict postdeploy server chain/SNI/served DER
PASS; client mTLS/application admission NOT_ATTEMPTED.

New directorybb5c8eb0…d8959 issued19:19:09.966146309UTC, nominal expiry
23:19:05.956440503UTC. It does not outlive security authorization21:37:28UTC.
Normal RU directory sync completed; no directory copied/imported to the owner.
Runtime seed publication is ordinary server startup, not an owner/dedicated test.

## PASSIVE_OBSERVATION / PROCESS_EXIT_CAUSE

Fifteen-minute window selected after verified load/chain: **19:22:09.911–19:37:09.925
UTC**,900.025s/31 read-only state samples. Same invocationdd70fcd8…3384a/PID788144,
active/running, NRestarts0 throughout. No production fault injection, manual restart,
owner CONNECT or synthetic carrier. This is a bounded observation, not proof of
long-term stability or of the cause of earlier failures.

APPLICATION_FATAL_RECEIPT=NOT_TRIGGERED for the observation invocation: it did not
end. SYSTEMD_EXIT_RECEIPT for that invocation also NOT_TRIGGERED. The root manager
receipt **does** capture the controlled baseline stop at19:19:05.812UTC, invocation
648e0c28…556c: service_result=success, exit_code=exited, exit_status=0, exact
start/end monotonic boundaries/PID/NRestarts3, matching InvocationID. This validates
the installed manager layer, **not** a naturally triggered fatal or old crash cause.
It is copied into protected local evidence and retained under bounded server policy.

OBSERVATION_CLASSIFICATION=ARMED_NOT_TRIGGERED; PROCESS_EXIT_CAUSE=UNKNOWN.
No DPI/provider/credential-expiry/caller attribution is inferred. Observer remains
installed for future natural exits, without an ongoing agent poll/collector.

## Final state and cleanup

Final strict probe19:37:43UTC: chain/SNI/actual DER match PASS, unchanged renewed
leaf06c2c41e…d1a17 and authorityd5a0d0db…9dc18. Limiting expiry21:37:28UTC,
headroom7184s at that probe. RU/NL pair19:37:55–57UTC: directorybb5c8eb0…d8959
and signed CRL22209/DER4c8ed092…a2857 equal; NL minimum CRL22209. Normal CRL
advancement from initial22147 is not an unreported credential/identity change.
Client mTLS and owner application admission remain NOT_ATTEMPTED.

Loaded/next0ccaaf81…2667a, same observation invocation/PID/NRestarts0, listeners
present. Final phone19:37:57UTC: same research83 APK/UID10283/PID19925; **VPN OFF,
app ON, ChatDeliveryService ON**, no Activity or networking lifecycle invoked.
Cache/enrollment/publisher/history/AWG were not modified by this task; client cache
compatibility remains unverified, no new publication was imported to the owner.

OBSERVABILITY_SOURCE_AND_BINARY=VERIFIED; RECEIPT_SCHEMA_AND_PRIVACY=PASS;
LOCAL_BEFORE_AFTER=PASS_TARGETED; DEPLOYMENT=LOADED_RECONCILED;
CHAIN_AND_PUBLICATION=PASS_AT_OBSERVED_TIME; OBSERVER_EFFECT=OBSERVATION_ONLY;
ROLLBACK_STATE=PREPARED_NOT_USED. No APK build/distribution or public release.

Cleanup receipts confirm unchanged AWG/TCP/API/mailbox state and restored ordinary
sync timer. Only SHA-verified created upload/native-checker/validation-runtime/
publisher-helper copies and the task's local Go build cache were removed. Installed
observer/helper, root/service receipts, source/binary/test evidence and protected
rollback remain. No operational fatal receipt was deleted; no phone state change.

## Rollback and next gate

Baseline executable and protected server backups remain. Root-only
`gateway-fatal-cause-20261011/rollback-observer.sh` removes only the observer drop-in,
daemon-reloads and restarts baseline if separately authorized/needed; do not restore
expired credentials or monotonic floors. Rollback NOT_USED. Operational bounded
receipts remain installed. No cosmetic cleanup restart, AWG/TCP/API/mailbox restart,
cache clear, re-enrollment, user/publisher/history modification or APK distribution.

Exactly one next operation: **separate readiness preflight in an agreed window,
including current client cache/current directory compatibility**. Do not proceed
automatically to CONNECT. READY_FOR_CLEAN_RETRY=NO; ATTEMPT_CONSUMED=NO;
OWNER_CONNECTS=0; FULL_PHASE_REQUESTS=0; REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN.
