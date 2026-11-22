# 22 November 2026 — RU outage and independent NL availability check

## Request and boundary

The owner reports RU unavailable again and asks whether NL still works, then asks
to continue the interrupted check. This follow-up reads current state and existing
traffic counters; it does not restart, recover, deploy or migrate any server.
RU remains NOT_RECOVERED. All times are UTC; add3hours for MSK.
No relevant interrupted diagnostic/recovery process is found at entry.

## Fresh evidence, not the preceding recovery result

- **13:46:** initial RU SSH connection times out; a bounded second attempt at
  **13:48:44** succeeds. This is not proof the whole host was offline. Direct
  readback shows RU AWG `failed/timeout`, TCP `inactive/success`, watcher active
  with955 retries and paid reconcile failed. Ordinary transport attempt is `error`.
- TCP exits **04:20:59**, AWG **04:21:00**, after the earlier verified recovery.
  Retained first failure is **04:20:49.271314**, `COMMAND_FAILED`, `engine_query`,
  `tcp-query`, `CalledProcessError`, returncode1, elapsed3.583976s, budget8s,
  `timeout:false`. It is NOT the previous lock deadline or a new demonstrated
  fsync timeout. Underlying native command failure is not diagnosed by this check.
  SHA256: `e87d97c99c3edce9031c4ceb36afa837077cc689ec00d3212d715d9b3e044779`.
- Shared RU HTTP remains active. All three public challenges return200; RU
  configuration returns503/`service_unavailable`, while both NL configurations
  return200 and verify against the client anchor. Existing test identity keys
  remain unchanged. The all-node configuration probe correctly exits nonzero
  because RU fails; do not report an overall configuration PASS.
- **13:46:33–35:** both NL watcher/AWG/TCP/MESH units are active, NRestarts0 and
  transport state freshly `applied`. Their starts differ from older snapshots;
  this is current availability, not a claim of overnight process continuity.
- **13:48:33–38, NL1:** four AWG handshakes within180s, newest about16s old at
  sample entry. Over5s, aggregate received bytes increase11,264 and sent bytes
  increase458,862. This proves live AWG peer activity, not every user's application
  performance, TCP/MESH traffic or a new synthetic DNS/HTTPS acceptance test.
- **13:48:38–43, NL2:** no AWG handshakes within180s, newest about20.6hours old;
  RX/TX counters do not increase during5s. An idle sample is neither failure nor
  proof of forwarding. Service/control-plane checks PASS; real data-plane test
  remains NOT_RUN. No keys, peer identifiers or client addresses are printed.
- Fresh panel imports agree: RU13:48:45 reports AWG failed/TCP inactive, HTTP
  active and transport unavailable; NL1/2 imports13:47:34/36 show active services
  and transport `ok`. These are not stale pre-outage green statuses.
- Current renewal transaction is `COMMITTED`, first cause null. Latest renewal
  and directory-sync executions succeed; their timers remain active. The current
  stopped RU transports do not imply that these shared control functions stopped.

## Result and remaining work

NL1 demonstrably exchanges AWG traffic while RU transports are down. NL2 currently
passes service and signed-configuration checks but has no newly observed AWG use.
Both still depend on RU for shared configuration/authorization; this observation
does not establish permanent independence or guarantee all reconnects/protocols.

RU restoration and the initiating TCP command error remain OPEN. No host-provider
fault, memory exhaustion or recurrence of the preceding lock/fsync mechanism is
inferred from this receipt. No timeout relaxation, automatic recovery schedule or
queued product implementation is started. Client/runtime versions, public catalogs,
server policy and live databases are unchanged; no rollback is required for this
read-only check. Raw evidence stays ignored under
`state-client-build/ops-incident-20261122-r1/`, outside Git.

Only new documentation is committed; pre-existing dirty work is preserved. The
branch already diverges from remote `main`; ordinary push is attempted and its
outcome reported separately, without force, reset or an unrelated merge.
