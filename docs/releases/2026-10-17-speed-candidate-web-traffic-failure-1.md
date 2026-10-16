# SPEED-CANDIDATE-WEB-TRAFFIC-FAILURE-1

**RESULT: WEB_TRAFFIC_FAIL_OWNER_REPORTED; ROOT_CAUSE_NOT_FULLY_PROVEN.**
Local date17Oct; the device/server events below are16Oct2026 UTC. The owner reports
that most sites do not open and some load without static assets; Telegram appears
usable. This is a failed practical traffic observation, not device acceptance of the
speed candidate. No captured HTTP response or browser-per-domain receipt is claimed.

Input review `8fbf3115ebca079232e333c0a229aeef631585e9`;
[actual pair installation](2026-10-16-transport-speed-cutover-owner-install-1.md),
[safe evidence](evidence/2026-10-17-speed-candidate-web-traffic-failure-1.json).
One owner-supplied normal export11,98,943bytes, is privately retained:
SHA256 `bcc5a08d4638550c136b7c97243cb18a8a071eac1ff7022a8993c46b48a83c30`.
Raw export, journal, real connection/session/bootstrap identifiers and browsing
destinations are not published. S1/S2 are consistent aliases, not historical A/B.

## Exact unchanged installed pair

- Installed APK: `28543d4690327e29a6eb6a60e52fa50232a407663ed7e610f1434cd56f86193d`;
  version `0.1.18-research84-ui60-4-speed-recovery1`, code84, UID10283, API31/ARM64.
- Embedded native, from verified installation:
  `f25124ba1c94a0c6f4258e8b67488e8febf9a1c9e88cb2073790564c3a1f4729`.
- Client cumulative inventory:
  `211b127d545af5c129acc93bf0ff78cac3af93707aad8def27bb6da830e2ae86`.
- Loaded gateway: `5de40b9ce9c15aac85475df05c449bddf2ecfe61a1928fa3844b4a8446b33047`;
  PID746768, invocation `843cf76698cd472995fbc6024dfa0b6c`, active/running/NRestarts0.

The22:00:52UTC gateway readback matches the installation invocation: no gateway
restart boundary is observed across these attempts. Phone readback22:00:51UTC
confirms the installed APK and VPN OFF. App PID32071 differs from the installation
PID24627; the intervening process transition is not attributed to a cause or claimed
continuous. This investigation does not restart or force-stop either application.

## Two separate recorded attempts

**S1_EARLIER_STARTUP — incident, not the later web session.**
Starts21:42:06.385UTC; startup fails after56.348s at DEDICATED_AUTH/UNKNOWN.
The earlier native first failure is `RELIABLE_HANDSHAKE_TIMEOUT`, close source
RELIABLE_EXHAUSTION;20,000ms ACK/progress ages. Exact dedicated-tag matching finds
42 server trace records, including the same handshake-timeout category. Subsequent
FAMILY_TLS_ERROR/GATEWAY_CLOSE/cleanup do not replace that first failure. The app's
coarse AUTH category is not evidence of a revoked grant or wrong credential:
authorization_denied=false, bootstrap family_authenticated=true, observation context
LIVE/stop NONE, later local_stop CLEANUP. No authentication/security workaround.

**S2_WEB_TRAFFIC — ring, distinct connection/incident and dedicated tag.**
CONNECTING21:54:17.592UTC; native startup SUCCEEDED after21.546s;
SESSION_READY21:54:41.165UTC and app CONNECTED21:54:41.381UTC. Normal owner disconnect
starts22:00:02.884UTC; app DISCONNECTED22:00:03.222UTC. It is restricted, not an
AWG/TCP fallback. Each attempt has one early bootstrap exchange, authenticated=true,
bootstrap_exchanges_dropped=0. Ownership capture remains disabled: no new admission
wait/grant inference is made from an early tag alone.

Final retained S2 counters:

| Surface | Observation |
|---|---|
| Native DNS |288 responses,0 recorded errors |
| Native TCP open |77 successes,0 recorded open errors |
| Packet TCP |76 handled,32 active, peak32 |
| Native bytes |567,399 sent /6,009,776 received |
| Reliable retransmission/timeouts |59 /56 |
| Mux protocol errors |10; individual causes not exported |
| Unsupported-traffic denial counters |UDP435 / IPv6811 |
| Packet quota refusals |`limit_denied` **NOT_EXPORTED**, not zero |

These are last retained aggregates, not proof of every site's DNS/HTTPS, sustained
slot occupancy, or measured available bandwidth. Native open success alone does not
prove page/asset completion; local quota refusal happens before native mux open.
UDP/IPv6 restrictions predate this candidate; they are not changed to improve a test.

Exact S2 dedicated-tag matching yields311 server trace events. The final retained
client/server flow samples agree: client send_next=send_base2649 and receive_next3008;
server send_next=send_base3008 and receive_next2649. Both have pending0/buffered0 at
those samples, not a permanent transport stall. Retained pre-OFF trace has no terminal
reason other than NONE. Client media summary includes16 expired assemblies/37 RTP gaps;
server includes0 expired assemblies/15 RTP gaps. This is not proof of a lossless path.

Server RELIABLE_RETRY_EXHAUSTED is timestamped22:00:12.980UTC, about10.096s after the
client disconnect request in the recorded clocks; then FAMILY_TLS_ERROR/GATEWAY_CLOSE.
No new clock-calibration experiment is performed. That terminal cannot be assigned
as the primary cause of earlier page failures from this evidence, nor is it declared
universally harmless. Native last-session terminal before cleanup remains NONE.

## Concrete source finding and its limit

The retained product `carrier/wholedevice/session.go` allocates32 TCP slots.
`Session.Handle` immediately closes/refuses an additional flow when those slots are
occupied and increments `LimitDenied`; it does not queue that flow for a slot.
`tcpforward.Mux.OpenTCP` separately enforces the mux stream cap. Existing connections
can therefore continue while new connections, including requests for assets on other
origins, are rejected. The code has no wholedevice TCP idle-timeout in this path;
actual long-lived/idle/socket-cleanup behavior needs a bounded targeted investigation,
not arbitrary termination of legitimate long-lived connections.

Go `Session.Snapshot` includes `limit_denied`, but both the `Diagnostics.nativeStats`
packet-field projection and `DiagnosticRing.counter` allowlist omit it. Consequently
export11 cannot count actual quota refusals. **Reaching32 is proven; rejection of the
specific failed site requests is not.** This is the leading source-supported
hypothesis, not a completed root-cause attribution.

Scoped exact-byte comparison confirms the wholedevice handler, mux/mux-stream code,
Diagnostics and DiagnosticRing are identical to retained UI60-4, before this speed
change. Old export10 also retained peak32. Neither observation proves the cap was
the cause then or now. Fast-retransmit causality, a new regression versus the previous
pair, and the detailed causes of the10 mux protocol errors remain NOT_PROVEN.

Two existing local tests on the exact retained candidate source pass, fixed count1:
`TestFlowLimitAndParentCancellation` and `TestFamilyDNSAndNoFallback` (`./wholedevice`).
The first demonstrates refusal of a33rd flow with32 occupied; the second uses
synthetic DNS. These are isolated adapter checks, not a browser/live-site reproduction
or another full transport matrix. One12.005s batch,50%-core quota, peak74°C,
75°C start gate/85°C cutoff; no emulator. No product source or artifact is changed.

## Retention, final state and next decision

S2:192 trace events retained/85 dropped; delivery_dropped152;64 boundary events
retained/70,957 dropped. S1:39 trace events/0 dropped;64 boundary events/84 dropped.
Both export/projection/delivery-projection/boundary-projection drop counters are0.
App ring/incident retain22/17 events with128-event limits; both archive arrays empty.
The primary server query reached its320-row limit and covers21:54:29–22:00:12UTC,
not the entire requested30minutes. S1 uses a separate exact-tag42/80-row query.
Positive retained events remain evidence; missing events in these surfaces are not
zeros or proof that no earlier failure occurred. Per-record cap256KiB, bundle cap
513KiB are unchanged. No additional native statistics reader is introduced.

Final observed phone state is OFF on the installed candidate; gateway remains on the
same running candidate. No new field trial or reconnect is initiated. Do not distribute
or mark this pair device-accepted. Next: decide whether to make an explicitly approved
compatible client/gateway return to remove the new variable, or investigate bounded
TCP admission/lifecycle and export the already-existing refusal counter before another
candidate. A rollback may reduce risk but is **not promised to fix the inherited cap**.
Do not blindly raise stream limits, change DNS/IPv6/security, or restart until green.

Actions: scoped SSH3; one owner-supplied normal export; two targeted local tests;
agent CONNECT/DISCONNECT0; product patch/build/sign/install/rollback0; service restart0;
native-stats polls0; emulator0. At least two distinct attempts are retained; owner
intentional CONNECT count is not reconstructed from truncated ring history. Historical
pair acceptance, causality, chat handoff, supervisor and public release remain unchanged.
