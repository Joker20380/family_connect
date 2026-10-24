# Lifecycle101 continuation — no new speed candidate

Exact parents100/f631. P1 remains RS32/32+CREDIT128/Q0. No wire, stream
dispatch, retry, credit, scheduling, encryption or session-close change.
The existing retired-ID return is already idempotent;101 adds **observational**
validation of its narrow contract. Raw `protocol_errors` and `unknown_stream`
still increment exactly as before. `expected_crossings`, `actual_violations`
and `unclassified` are disjoint new incident counts, not replacements for raw
protocol errors (DNS/decode failures must still be checked separately).

| State | Incoming / operation | Contract |
|---|---|---|
| opening | OPEN_OK / OPEN_ERROR | admit or reject; cancel may cross result |
| open | DATA / WINDOW_UPDATE | opened, finite credit, no DATA after remote FIN |
| one-direction FIN | Read / Write | FIN is ordered EOF for that direction; drain buffered tail; opposite direction remains usable |
| both FIN, receive drained | client CLOSE | request final confirmation, wait up to existing10s; timeout aborts |
| server workers done + CLOSE seen | server CLOSE | both copy workers finished; acknowledge and retire after local send |
| local abort | RESET | discard local queued/unread data intentionally, cancel workers; retire after send |
| peer RESET | retire immediately | terminal for this ordered peer direction; later frame is not a crossing |
| locally aborted retired | bounded in-flight DATA/credit/FIN, terminal crossing | only known generation/stream, compatible state and remaining credit; no delivery, resurrection or returned credit |
| graceful retired | crossing RESET | both FIN and no unread tail; not permission for DATA |
| unknown/expired history | any | unclassified, raw error retained; cannot infer never existed |

CLOSE is not TCP FIN: FIN separately closes a direction. The client initiates
the final CLOSE handshake; the server completes target copy workers first.
RESET after a sent CLOSE is possible if the client cancels before confirmation.
Ordered TLS/RS prevents explanation by RTP reordering of the same direction.

Session-scoped64 retired records expire for classification after60s;32 incident
records retain their own stream state and per-kind last enqueue/write/receive
timestamps. Later ordinary bulk cannot evict them. Additional incidents still
increment class totals and `incident_dropped`; overflow fails fresh acceptance.
No payload, address, credentials or room identifiers. JSON projection is bounded,
and exposes projection overflow. No change to public/online support schema.

Historical eight incomplete episodes remain HISTORICAL_UNRESOLVED. In session189…
Android/gateway stream51 are the same crossing sequence, not two independent
failures. stream47 WU, stream115 FIN and stream51 RESET/CLOSE are known frame types;
no extrapolation to other sessions or beta87–94.

Budget is the existing64MiB ledger,36.080078125MiB already spent. At most24MiB
additional:16.0234375MiB short P0/P1 controls, ≤2MiB periodic15min observations,
≤2MiB short/cancel/smoke, remainder reserved (not automatically consumed).
No full four-phase speed rerun. Prior2.3× speed evidence remains valid; fresh
controls check observer cost, bodies and lifecycle. Acceptance requires complete
both-end incident context, no unexplained fresh violation, bounded cleanup,
ordinary persistent P1 reconnect and P0 rollback; other users stay unchanged.
No claim of continuous saturated load, overnight recovery or general release.
