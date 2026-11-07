# Cold test harness: one-frame guards and consistent budgets

Source-only continuation of `bd0fbe7db7bc80b1846e26b4c3984e2661f3a3f0`.
This repairs the test runner, not Family Connect provisioning. It does not establish
that the historical94°C was false. Hardware investigation and cold runtime stay stopped.

## Scope and preserved evidence

- `tests/android_emulator_guard.py`: existing helper updated, no telemetry service,
  external collector, system configuration or temperature-threshold change.
- `tests/android_cold_runtime.py`: versioned copy of the existing local runner, with
  guard/lifecycle integration only. An explicit existing isolated work directory is
  required with unused output paths; reused evidence is refused before monitoring or
  cleanup. Importing it does not start the stand. Private fixture, locator, OAuth
  helpers and binaries are not copied into Git or produced by this change.
- The frozen `reduced-load-runtime/local-auth/run_android.py` SHA256 remains
  `d705a82285cfef1269c01840ba0cd77fe51a72c7e6197bed7b5e9cb38cfb68b6`; its guard remains
  `e4beb91db4305e9635d1a2c23ae17d7d5efa79d0e228e97416597260d8b29340`.
- Product source `6eb61a9faa659b6b07ac16bf9f4bac46a41cd2a7` is unchanged in carrier,
  Android and native source. JNI SHA256 remains
  `17119f000407ec1d7ccdf8d33acabe423f3cf20e32b6f8af839d209aa3360c59`.
  Accepted provider-free Android JNI PASS artifacts retain their recorded hashes.

## Decision and evidence

Watcher and stage audit call the same serialized sampling path. Each frame contains
CPU raw millidegree inputs, path/driver/label, converted values, GPU raw degrees/label,
per-read wall/monotonic timestamps, frame acquisition interval and computed maxima.
This records sequential acquisition; it does not claim simultaneous physical readings.
The decision, saved frame and stop callback receive copies of that same frame. Resource
CPU/memory profiling no longer reads temperatures. Later reads/cleanup cannot replace
the first stop's evidence. Audit checks its associated resource snapshot under the same
sampling lock. Optional missing labels are UNKNOWN; missing or failed sensor input is
not0°C and fails closed.

Stop reasons are `CPU_TEMPERATURE_LIMIT`, `GPU_TEMPERATURE_LIMIT`, `SENSOR_UNAVAILABLE`,
`MONITOR_ERROR` and `TEST_LIFETIME_EXCEEDED`. CPU85°C/GPU80°C remain the boundaries.
Stop events are persisted before owned-process termination, separately from resource
profiling, so a profiling lock cannot block the deadline watchdog. Lifetime evidence
records its exact deadline, decision time and limit name; its temperature frame is
explicitly the last completed frame (or absent if no read completed), not a new reading.
The independent clock watchdog does not wait for the sensor-reader lock.

## Finite test budgets

| Boundary | Limit and origin |
| --- | --- |
| Preparation | 180s from monitor creation, including Android boot and pre-Connect setup; existing boot sub-limit120s retained |
| Attempt | Existing390s instrumentation envelope, from immediately before its launch; includes the unchanged200s MESH candidate and non-candidate harness work |
| Cleanup | 120s from first entry; repeated entry cannot reset it |
| Overall watchdog | 705s from monitor creation:180 +390 +120 +15s termination reserve |
| Monitor join | At most6s within the overall reserve; failure is MONITOR_ERROR, not PASS |
| Forced exit | Own process groups are killed; exact owned authority stop has a5s maximum allowance, then own runner exits124; final ceiling710s |

An attempt can start only before the preparation deadline, once. Therefore even a
latest-admitted attempt's full390s envelope ends before overall expiry; a200s candidate
is no longer cut off by a180s-from-boot guard. These are host test envelopes, not new
product candidate/readiness budgets. Readiness30s, ConnectivityOrchestrator, TLS,
certificates, network timeouts and provider/locator lifetimes are untouched. No retries
or deadline extension is added. Temperature monitoring continues through preparation,
attempt and cleanup independently of the remaining time. Close interrupts waits, joins
both helper threads and retains the last completed frame without polling again.

## Verification and remaining limits

`python3 -B -m pytest -q tests/test_android_emulator_guard.py`: **34 PASS**. Controlled
time and mocked inputs/processes cover66→94 evidence identity, raw-unit conversion,
absent/malformed/unreadable sensors, separate GPU/CPU/monitor/lifetime reasons, concurrent
audit/watcher serialization, immutable first-stop evidence, cleanup/join, full attempt
window near preparation expiry, hung-reader watchdog, runner forced-exit integration
and refusal to overwrite preserved evidence before starting monitoring or cleanup.
An owned child created concurrently with a guard stop is registered and terminated;
subsequent child creation is refused.
Unwritable stop/evidence files do not prevent owned-process signals or forced exit.
No test starts a real child process, emulator, authority or provider connection. AST,
whitespace and retained artifact/source checks also pass.

No60s poll, host/JNI/race/MESH suites, AVD, OAuth, rooms, APK/native build or Connect was
performed. No runtime acceptance of this repair is claimed. Production/G4, other
branches, phones, public artifacts, cooling/power and foreign processes are untouched.
No deployment/rollback or version/catalog change is involved. Future runtime requires
a separate owner decision; the unused Connect is not consumed or automatically resumed.

## Subsequent authorized single runtime — 7 November11:06UTC

The owner separately authorized one run of this exact4854f96 harness. It ends
**STOPPED_BEFORE_CONNECT**, without retries. [Sanitized receipt and exact local hashes](2026-11-07-cold-guarded-runtime.json).
Actual Python import logging confirms the versioned guard, not a local-auth copy:
`tests/android_emulator_guard.py` SHA256
`1a93d8e19a19a375c6a6a7b5a3a6717d6e477867ff745a5a3b2dccc230258e0b`.
One preflight (CPU69°C/GPU53°C) and one API27 NVIDIA/KVM AVD pass. Android is ready with
no test package/readiness/VPN before protected local OAuth access. Two own test rooms,
registered synthetic identity and a verified fresh locator (415s remaining) are created.
The post-worker audit is61°C/GPU56°C; no native rebuild or old suites run.

At FINAL_ASSET_PACKAGING, the exact saved WATCH frame (18.698ms acquisition interval)
reports Core4 `temp6_input=91000`, Package `temp1_input=90000`, GPU56°C. The unchanged
85°C CPU threshold yields **CPU_TEMPERATURE_LIMIT**,58.199s after monitor start with
121.801s preparation remaining: not lifetime expiry. Frame equality between stop and
resource evidence is verified. The later ASSET_PACKAGING_FAILED follows owned-process
termination; no independent packager defect is established. Only an unsigned partial
APK remains; no completed final APK/install, guest rules, instrumentation or Connect.

Associated2.631s CPU averages (100%=one core): emulator3.42%, Telemost workers1.52%,
other38.38%, available RAM14892780KiB. The new packager PID has no prior sample; its
recorded0 is UNKNOWN, not proof of idle. These data do not identify the heat source or
independently establish physical sensor accuracy. No fan audit or old94°C reinvestigation.
No Android JNI/native-operation snapshot exists because the client was never launched;
server Go workers/room creation are not Android Go/carrier/TLS/challenge or traffic proof.
READY, bundle, DNS, verified HTTPS and Android egress remain NOT_RUN.

Runner/monitor/owned process groups and exact authority container are stopped; shared
lock is released. Two provider room objects remain deletion NOT_VERIFIED. Product6eb61a9,
JNI17119f00…60c59, accepted Android JNI PASS and both prior FAILs/all19 artifact hashes
remain unchanged. No public artifacts, production/G4, phones, admission/subscriptions,
cooling/power or foreign processes change. No deployment/rollback applies. This local
attempt is terminal; a separate owner environment decision is required before any
further execution, not another same-host retry or provisioning change.

## Owner override after that stop

The owner explicitly cancels the CPU-temperature stop and asks to continue. A narrowly
scoped `--observe-cpu-temperature-only` switch selects one new run: CPU frames and85°C
crossings remain recorded, but do not cause CPU termination. The default is unchanged.
GPU80°C and unavailable/failed sensors, monitor errors, memory/lock and finite deadlines
still stop the stand. No BIOS/power/cooling, product or native change. This does not
establish sensor accuracy or safe physical temperature.38 targeted harness tests pass,
including observed94°C without CPU stop and retained GPU/sensor/monitor/watchdog stops.
The next runtime outcome remains pending; this source checkpoint is not runtime PASS.

## CPU-observation attempt and offline packager correction

One19877fd run reaches fresh identity/two own rooms/verified locator without a guard
stop. CPU readings remain recorded (two above85°C frames, reported maximum99°C), not
used as thermal diagnosis. It ends before final install/Connect on apksigner exit2.
Exact offline replay identifies password-file EOF: both `--ks-pass` and `--key-pass`
consume successive lines of the same one-line file. No independent native issue is
established. The existing asset packager is versioned under tests, invoked explicitly
by the existing runner, and omits redundant key-pass for the same-password PKCS12 key.
39 targeted tests pass; both real APKs sign, verify and align successfully offline,
with manifest/dex/JNI unchanged and only intended asset substitutions. Expired reused
offline materials are not installed or approved for a new cold runtime. No new rooms
or AVD were used for the correction. Cleanup is verified; room deletion NOT_VERIFIED.
Connect/native snapshot/READY/traffic remain NOT_RUN. An additional AVD/preparation
launch requires owner approval; there is no automatic retry series.
[Safe receipt, source/artifact identities and limits](2026-11-07-cold-cpu-observed-runtime.json).
