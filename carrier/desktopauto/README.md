# Accepted106 automatic connection policy

This package ports the accepted `ConnectivityOrchestrator` policy to one shared
Go implementation. Its reference/parameters and platform obligations are pinned
in `clients/shared/android106-auto.json`. It does not implement a VPN, grant
access, or activate the desktop Auto selector. Native workers now contain this
package through `clients/mesh/automatic` and its bounded private-pipe host protocol.
The Linux parent/guard and single-attempt normal/MESH adapters are implemented.
`auto_platform.Platform` supplies protected configuration, installed capability
filtering and actual helper/packet attempts. `auto_runtime.Coordinator` drives the
native controller, bounded health/loss and physical-network observation. Product
service/GUI authorization, durable lifecycle integration and Windows broker remain
open; this is not an activated desktop Auto mode.

`Connect` takes the **service lifetime** context and a strictly increasing nonzero
generation. Transition calls are serialized; duplicate connect/health/retry calls
return `ErrBusy` rather than accumulating jobs. `Snapshot` is detached and safe
for concurrent readers. `Interrupt` only cancels the matching generation.
`Disconnect` interrupts first, then waits for the current bounded operation and
cleans up. Old generation callbacks return `ErrStale` without touching a newer
session. Reuse after failure requires successful explicit Disconnect, preserving
fail-closed ownership in the meantime. Inspect the snapshot for connection outcome:
an operational failure is a state/category, not an unredacted returned host error.

The host must own the system path. `Configure` opens/verifies a blocking guard
before fetching or reusing authorized configurations and filters actual normal
capabilities. A transient configuration refresh may yield no normal candidates,
as in Android, but authorization/configuration failures are terminal. `Open`
validates current material and returns only after authenticated transport, TUN,
routing/DNS and health are ready. A missing capability is not a successful path.
The restricted candidate is always last, or the sole candidate in restricted-only
mode. It must never silently run another transport.

`CloseCandidate` blocks before teardown and keeps the guard even on failure.
`Release` removes only owned resources after explicit disconnect. Every operation
must honor its context/deadline, including cancellation of network/setup calls.
Cleanup has the existing platform's finite watchdog, supplied to `New` and capped
at60 seconds; it is separate from accepted20/200/300-second connection budgets and
30/60/120-second retry backoff. The library cannot force a misbehaving host to
return; service process supervision is still required.

After readiness the host reports verified health/loss using the original
generation. During RESTORING it calls `Retry` at its ordinary bounded poll cadence;
polling before the recorded deadline does no work. Healthy transport is not
migrated just because an earlier candidate becomes available. Normal success may
update the normal hint, but restricted success never does. Cancellation, trust,
configuration and internal/cleanup failures never fall through to a weaker path.
Go TLS certificate-validation and invalid-TLS-record errors remain terminal even
inside `url.Error`/network wrappers; they must not masquerade as transient network
failures. Host-specific entitlement/signature/revocation failures must use the
typed AUTH/CONFIGURATION categories rather than an opaque transport error.

Events contain enums, elapsed times and counters only, never addresses, raw errors,
credentials or payloads. The128-entry bound preserves a separate first reason and
dropped counter. The parent diagnostics collector still owns schema106 export.

The checked-in trace fixture was generated from the unchanged accepted Java
controller/Transport, then compared with this implementation:17 scenarios and160
event/final-state records. `scripts/check_desktop_auto_reference.py` reproduces
that comparison with the local accepted capsule, a JDK and Go; it compiles pure
Java classes, not an Android APK. Ordinary Go tests compare against that fixture
without needing the private capsule or JDK. Dedicated CI runs the policy tests
on Linux/Windows and Linux race checks; a prepared workflow is not a CI result.

Tests use a monotonic synthetic host with guard/readiness invariants, not actual
networking. Race tests and Windows cross-compilation do not prove platform TUN,
capability checks, crash recovery, underlying routing or installed Auto acceptance.

The Linux traffic containment component now exists in `clients/linux/auto_guard.py`.
Its separate isolated-kernel check exercises real nftables and TUN packets. It is
called through the native policy's Linux guarded-host adapter. See
[`docs/clients/DESKTOP_AUTO_GUARD.md`](../../docs/clients/DESKTOP_AUTO_GUARD.md) for
the ownership/transaction contract and remaining host responsibilities. Do not
substitute that component's policy readiness for authenticated VPN readiness.
