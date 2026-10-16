# Bootstrap pre-HELLO exchange correlation

Task: BOOTSTRAP-PRE-HELLO-CORRELATION-1. Diagnostic-only, no live actions.
See [report](../../docs/releases/2026-10-16-bootstrap-pre-hello-correlation-1.md)
and [separately authorized trial runbook](RUNBOOK.md).

## Exact inputs and patch

`source-manifest.json`, `exact-bindings.json`, `source.patch`, `before/`, `changed/`
describe the eight-file delta from retained C_NEW (five runtime diagnostic files,
two test files and a generated local-only fixture receipt). The original cumulative
inventory is c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08.
The signed C_NEW and the rolled-back installed APK are different; neither is rebuilt,
overwritten, signed or installed here. All new APKs remain unsigned, local only.

The client stores at most four `bootstrap_exchanges`, each containing
`bootstrap_exchange_tag` and a separate `family_authenticated` boolean. The first
failure's `observation.bootstrap_exchange_tag` identifies its own exchange, even
when the bounded exchange list overflows. `bootstrap_exchanges_dropped` counts
omitted entries. It is not a dedicated `session_tag`, identity or authorization token.

Transformation is exactly `sessiontrace.Tag(hex.EncodeToString(session.server[:]))`:
the existing domain-separated SHA256 over the 32-byte decoded nonce. Server
`WithExchange` uses the same helper and the same lease nonce; no second hash scheme.
The recorder is attempt-local and returns an exchange-specific context handle.
Snapshots deep-copy the list; completion/first failure prevents late mutation.
New attempts cannot inherit an old handle's auth/failure attribution.

## Local replay

Use retained C_NEW and the retained **actual gateway candidate**, never root main.
The original source locations and commands are recorded in results. With cached
Go1.26.1 dependencies and Android tools already present:

```sh
python3 research/bootstrap-pre-hello-20261016/apply.py --source "$C_NEW" --out "$NEW"
python3 research/bootstrap-pre-hello-20261016/prepare.py --client "$NEW" --gateway "$G_CANDIDATE" --out "$WORK"
python3 research/bootstrap-pre-hello-20261016/run.py --work "$WORK" --tools "$TOOLS"
python3 -m unittest discover -s research/bootstrap-pre-hello-20261016 -p test_correlate.py
```

Output directories must not exist. `apply.py` verifies the retained cumulative
inventory and every changed-file before/after hash. `prepare.py` copies both
modules and changes only the gateway import namespace to `fixture.invalid/gateway`.
Its production functions are unchanged. Client tests call real `recoverCarrier`;
gateway calls real `ServeCarrier`, `OpenServer`, Family/TLS and Broker. No provider
API, packet faults, room creation or live credentials are involved. The old local
certificate fixture is reused with an additional independently authenticated device.

The local native-export adapter copies the **actual** `startup_owner.go`, changing
only its package name, and calls `retainStartup`/`startupStats`. It is not included
in the APK or gateway. It asserts native attempt filtering. The resulting B receipt
is the Java test resource: actual `Diagnostics.nativeStartup` (the parsing branch
called by `Diagnostics.nativeStats`) → `DiagnosticRing.startupStats` →
`RestrictedStartup.project` → persisted incident/ring → ordinary
`exportRecord`/`exportBytes`. No alternative diagnostics exporter is introduced.
Android Context/AtomicFile/share UI are not executed on a device in this task.

`run.py` fixes one normal + three race executions, stops on failure, and never
retries until pass. Product timeouts remain120s; fixture deadlines are2s. Cases
cover real ACTIVE holder, cleanup/grant, different identities, two simultaneous
real exchanges, unauthorized TLS, cancel/first failure, completion, capture disabled,
expired, limit and actual file-write failure (isolated child RLIMIT_FSIZE only).
No baseline characterization or burst matrix is rerun.

The final full matrix and supplemental native-export boundary runs are retained
separately in `results/`. The supplemental run selects only
`^TestCorrelationLease$/^B_active_deadline$`, count1 and race count3; it does not
repeat the matrix. Local B can preserve IO_DEADLINE or CLOSED_PIPE with DEADLINE
context, depending on the pre-existing close race; no error is relabelled.

Native/JNI build uses the unchanged
`../chat-vpn-handoff-20261015/build_check.py` with the new client source. The exact
commands/toolchain/return codes are in `results/native-build.json`. Full Gradle
assemble uses `build_gradle.py`, normal native, and the real B receipt copied to
`clients/android/app/src/test/resources/bootstrap-deadline-native.json` before
building. Final commands/checksums are in `results/gradle-build.json` and
`results/artifact-checks.json`. Four targeted JVM classes run,12 tests total.
`resume_gradle.py` is solely recovery of the recorded local sandbox socket denial.

## Capture completeness

`correlate.py` is an offline bounded JSON/JSONL reader, not a collector or endpoint.
It joins client tags to actual server Exchange values and keeps holder role UNKNOWN.
Disabled/unavailable, missing footer/output gap, limit, and expired/outside-window
are explicit. Even a complete file without matching events says NOT_OBSERVED, never
"no holder". In-memory `OwnershipSnapshot` alone cannot distinguish disabled from
expired/empty; startup/header/footer and time coverage must also be supplied.

Safe results contain generated fixture tags only. No owner export, private journal,
room URL from a real provider, identity, key, APK or production capture is published.
