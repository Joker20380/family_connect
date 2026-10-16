# Separate observed bootstrap trial — not authorization to execute

This task only prepares diagnostics. No SSH/ADB, signing, installation, export,
CONNECT, credential maintenance, gateway restart/deployment or configuration change
is performed or authorized by this runbook alone. Historical A cause remains
NOT_PROVEN. New diagnostics do not fix its startup failure or accept the new pair.

## Before deciding on a trial

1. Retain the original failure report and available pre-change runtime/directory,
   executable/invocation and broker/session evidence through already permitted
   bounded sources. Do not read private databases/identity, invent unavailable
   state, or repeat old journal/rootcause audits. Record what cannot be recovered.
2. Identify the diagnostic unsigned APK/native/inventory by the new report, not
   C_NEW's old signed hash and not the rolled-back phone version. Any signing,
   compatible install and device use require separate permission and ordinary
   verification. No versionCode bypass, data deletion or new signing key.
3. Recheck actual executable, invocation, served chain/seed, current directory
   binding, material validity, maintenance/recovery and owner availability only
   within the next task's allowed bounds. Do not assume renewal happened.

## Collector activation is a new-process boundary

The **existing** `--research-admission-evidence` flag starts the collector during
gateway startup. It accepts an absolute, new output path (exclusive creation0600).
Bounds: **15 minutes,512 events**,250ms flush; there is no dynamic public activation
endpoint. Do not assume the current production process has it enabled.

If activating it requires a new process, stop here until that operation is separately
authorized. A new process destroys the old in-memory Broker/holder state. Record
old and new invocations and new conditions. This is a **new observed experiment**,
not a continuation of historical A. Do not rebuild the gateway merely to enable
the already present flag. Do not stop schedulers or force-release holders.

Before any future CONNECT, require readable startup header: schema,
enabled=true, until_ms, event_limit512, expected invocation and PID. Confirm
remaining capture/material/security time covers preparation plus the separately
bounded trial and cleanup; do not stretch capture or the120s bootstrap budget.
If capture cannot be activated/written/read or time is insufficient, record
CAPTURE_NOT_READY/ENVIRONMENT_BLOCKED, not permission to repair the server.

## Observed premise and interpretation

For a chat/holder hypothesis, require evidence of that original premise in the new
process: a dedicated generation/tag, its authenticated exchange, actual mailbox/chat
operation and ownership observations. ChatDeliveryService or "online" alone is not
that premise. Do not arbitrarily block DIRECT, create another identity, add native
pollers, inject bursts or alter retries/admission/queues/timeouts to obtain it.

If the premise is not observed, an otherwise successful connection means
NOT_REPRODUCED, **not** "restart fixed it" or "root cause proven". ACTIVE is a local
Broker state, not proof of remote-client health. Holder role is CHAT/VPN only with
additional corroboration; otherwise UNKNOWN, even when same_identity=true.

Use only owner actions explicitly authorized for the new episode. Prepare normal
OFF cleanup and ordinary one-time support export beforehand. Stop additional
intentional CONNECTs on first unexpected failure; do not retry for a better trace.
Do not mix prior A, historical B, new attempts or concurrent chat records.

## Exact join

- Client: installed/native identities, connection/incident/attempt, directory,
  `restricted_startup.bootstrap_exchanges[]`, each tag and Family auth boolean,
  omitted count, first observation tag, cause/context/stop ordering.
- Server: same invocation/window; `OwnershipEvent.Exchange` equals client
  bootstrap_exchange_tag. Match authenticated/busy/wait/wait_end/grant/hello_sent/
  exchange_end only where present, by exchange, not nearest timestamp.
- Busy/wait: generation + holder_exchange + holder_state + same_identity identify
  the specific holder. `generation` is the existing dedicated trace session tag;
  cross-check that trace, not a new generated label. Unknown role does not weaken
  proven waiting on this holder.
- Worker transitions/release can have **empty Exchange**: join their generation
  and holder_exchange. Do not assign them to the requester. `wait_end` is not
  automatically a successful grant; require subsequent grant/HELLO. Local cleanup
  completion is not server slot removal. Late exchange_end/cancellation is not
  automatically the first cause.

## Completeness and safe output

Capture header/footer are required alongside events. `OwnershipSnapshot.Limited`
is a retained-capacity signal; disabled/expired captures can be empty with
Limited=false. There is no dropped-event count. Missing/truncated footer or sequence
gap makes output incomplete; the existing collector does not propagate every async
flush error to admission. Check written count, limit, time range and process binding.
Do not infer absence of a holder from missing events, expired capture or a write
failure. `correlate.py` makes these limitations explicit, never outputs NO_HOLDER.

One ordinary support export after the authorized episode; raw files remain private.
Projection retains at most4 bootstrap entries, counts omitted entries, and preserves
the first failure's exchange independently. Ring/incident history is bounded;
preserve available short observations before rotation without a second native reader.
Old schema records lacking tags remain uncorrelated; never backfill historical tags.
Publish only safe hashes/timeline/tag joins and explicit coverage limits. Leave VPN
OFF. No public release, main merge, supervisor promotion or historical-A/B attribution.
