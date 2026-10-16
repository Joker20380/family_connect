# Browser-shaped admission investigation (local only)

Scope: explain whether existing search/HTTPS can continue while new HTTPS fails;
exercise cleanup rather than assuming a leak. No product change or rollout.
[Report](../../docs/releases/2026-10-17-browser-admission-local-1.md).

## Real code and bounded substitutions

`admission_export_test.go` reuses the retained `testCredentials` and packet endpoint
fixtures. It runs real Family TLS and ReliableStream with default parameters;
the existing endpoint's loss/duplication switch remains off. Both muxes enforce32.
Only the existing test-only loopback destination allowance and synthetic DNS exchange
are used. The control callback is synthetic: it proves entry/rejection, not lease
renewal authorization. Ephemeral synthetic credentials never leave the test process.

`browser_admission_test.go` connects real local TCP sockets through unchanged
`wholedevice.Session.Handle`, real mux, and a trusted local TLS/HTTP1.1 origin.
Each response body is checked exactly. TLS trust uses only the fixture certificate;
no verification bypass. Distinct synthetic Host values are NOT real sites: all use
one local TLS origin/IP. This is not a browser, Android/gVisor, WebRTC, QUIC or field
test, and does not measure phone bandwidth. Synthetic DNS has a matched NOERROR
response with no address answers: no public resolver or site reachability claim.

Five leaf cases, fixed normal2/race1 on each source:

1. Keep32 established TLS connections open; reuse search and an asset successfully;
   reject new TLS before origin HTTP, allow synthetic UDP DNS, refuse TCP DNS and
   control open. Close one socket; a new HTTPS request succeeds without reconnect.
2.40 sequential HTTPS requests closed by application TLS close: all slots return.
3.40 sequential HTTPS requests with origin Connection:close: all slots return.
4.40 sequential HTTPS requests followed by application TCP RST: all slots return.
5.31 data streams plus one held control stream: new data fails at mux, despite free
   wholedevice capacity and neither exported-counter increment; control close restores
   new HTTPS. Existing search continues. No claim about a real ten-minute lease failure.

The cap cases deliberately hold valid idle sockets. They do not fabricate a leak.
Standard close/RST cases are not exhaustive gVisor/loss/half-close coverage.
Race origin-close fixtures retain server protocol-error counts26/current and30/previous
with all responses and cleanup successful; client counters0. These are not the owner's
client-side10 errors. The first summary's all-zero assertion was incorrect and is
corrected without rerunning tests; nonzero counts are preserved in the evidence.

## Reproduce without modifying retained source

From repository root, with the recorded retained sources and Go1.26.1/cache present:

```sh
systemd-run --user --scope -p CPUQuota=50% -p MemoryMax=3G -p TasksMax=160 \
  python3 research/browser-admission-20261017/run.py \
  --repo /absolute/repository --output /absolute/private/new-run-directory
python3 research/browser-admission-20261017/summarize.py \
  --repo /absolute/repository --run /absolute/private/new-run-directory
```

Adjust script location for the isolated publication worktree. The repository argument
points to the tree containing retained `state-client-build`, NOT root main as source.
Sources are `transport-speed-cutover-1/source/carrier` (current211b127d inventory)
and `ui60-layout-current-style-1/source/carrier` (previous e90893ae inventory).
Go `-overlay` adds only two `_test.go` files; it never edits either source or product
artifact.11 selected source/build-input hashes per tree are checked before/after.
Relevant mux/lease files also match the independently retained deployed gateway
derivative. Both test peers compile client-derived code; this is not an exact-gateway
executable or full independent gateway-source acceptance.

One runner; GOMAXPROCS1, serial offline builds, CPU50%, start below75°C, stop at85°C,
240s per command/700s batch ceiling. No emulator. Exclusive output directory, fixed
counts, fail-fast; no automatic retry. Build only test binaries, not APK/native/gateway.
Public logs contain only synthetic fixtures. Raw owner evidence remains private.

## Next diagnostic/fix boundary

Do not raise32 blindly, evict legitimate long-lived sockets or relax security/expiry.
First preserve the existing packet `limit_denied` through Java projection and account
for mux-local admission refusal separately: the existing `OpenErrors` does not include
that path. Such a diagnostic product delta is not made here. Any admission fix needs
bounded resource/fairness behavior, control capacity, cancellation and lifecycle tests;
an unlimited waiting queue or arbitrary idle cutoff is not an acceptable substitute.
No live CONNECT, rollback, reinstall or maintenance is triggered by these findings.
