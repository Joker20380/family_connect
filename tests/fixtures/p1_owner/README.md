# Owner P1 acceptance after checkpoint15166ff

New series, not a continuation of the closed speed ledger. Exact installed99
source and gateway ae527cbd are the parents; never rerun older prepare/install
scripts into their existing directories. Private work:
`state-client-build/p1-owner-acceptance-20261021`.

Frozen before traffic: P0/P1/P1/P0; each8MiB bulk plus12×1024B controls.
Single P1/P0≥1.20 in both orders; aggregate≥0.90 in both comparisons. Small
median/max>1.20 requires causal review, not automatic acceptance. All bodies,
both-end completion, no unexplained active failure/reconnect/fallback are required.
P1 additionally requires15min periodic load, drained Disconnect and ordinary
Connect/DNS/HTTPS/TUN smoke. On acceptance leave persistent owner P1 on both ends;
otherwise P0 plus smoke. No other users' profile changes.

64MiB requested-byte cap, never refund failed requests. Reserve32.046875MiB for
the four phases,8.01171875MiB for at most one proven service-interrupted phase,
8MiB targeted diagnostics,12MiB active-session load and3.94140625MiB smoke/close.
At most180s/bulk; stricter existing limits remain. No Q1/packing/FEC/QUIC changes.
No more than two causally supported correction cycles. This is not general release
admission; the old96/newP0 regression remains unresolved.

Observation100 adds only a bounded, payload-free Mux lifecycle snapshot to the
existing USB diagnostic path. It preserves counters and frame handling. The first
unknown-ID event captures the recent stream record, when present; a missing record
is unknown, not proof the ID never existed. A32-event ring and64 removed-stream
records have fixed bounds; exported snapshots are detached. No HTTP schema change.

`classify.py` is post-processing only: proven known retired RESET-stream + valid
incoming RESET/WINDOW_UPDATE/CLOSE before lower failure is labeled separately, without modifying the
raw counter. Other frame kinds, missing history and violations are not waived.
The original request outcome cannot be inferred from a reset label. Snapshots from
different session generations cannot be combined. `control.py` uses ordinary USB
Disconnect/Connect and the existing exact-binary next-session operator policy;
it does not restart services. `traffic.py` reuses the pinned HTTP meter and bounded
resource/journal collector, adds2s USB observations, and keeps failed reservations.
Every phase uses the same diagnostic configuration. No runtime telemetry API is added.

Run outcome:100/f631; four phases60/60 and repeated speed pass.15min35/35 bodies,
but9 Android/3 gateway events are not all classifiable with this history. Not
accepted; owner restored P0 and smoke passes.36.080078125MiB requested,98/98 bodies
including probes. No parameter retry or budget reset. Full original source patches
are frozen separately from the added causal regression tests. See the dated report
for the remaining evidence gap; this fixture is not a product admission switch.
