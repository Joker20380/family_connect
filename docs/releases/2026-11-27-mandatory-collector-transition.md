# Mandatory collector / support maintenance transition — 27 November 2026

## Installed component, not all-writer acceptance

At01:53UTC current accepted service remains `ha02-forward-20261127-panel01`, support
archive621009b8, unchanged PID/authority/generation. The collector source/binding is
now the installed successor below. Panel/dependencies normal baseline is preserved.
The separate MESH incident and subsequent automatic NL1 restart remain separate;
see [operational evidence and limits](2026-11-27-mesh-recovery.md).

The new explicit baseline name is `owner-collectors-b7f4cbd2`. Its exact source
binding is collector commit `b7f4cbd2b96750cb9c97eee61f27a9881d5b4bdb`:

| Path | SHA256 |
| --- | --- |
| control/capture_gate.py | da28d940e2e17e2dbb1fbbde8cc04c59d29cffc8762ada717135504e2ffa4906 |
| provisioning/owner_capture.py | b7b1fb3ffe69d9428cb419a30d2473a2bb73a6ffb2e7c6390b6878afc953a45d |
| provisioning/support_bindings.py | afba534e17ec3a57f5431bd611d66b94a56f7e5f969e167ca5afe2834d430bc2 |
| provisioning/subscription_collector.py | 3bb9954c8edfba64f4b2aeb63fb174669fa2fc8e37f71c193c9a18da895193cb |

The original192343eb variant/pins and original19-file baseline manifest remain
unchanged. Old panel01 plan, authority, source capsule and receipts are not rewritten.
New tooling selects only an explicitly reviewed source variant for observation,
stopped capture or absent-predecessor preparation; it never silently upgrades a plan.

## Compatibility qualification

The new observer checks current source closure before cursor IPC/SSH, exact live
PID/boot/start/argv/cgroup, unchanged archive/authority/accepted history, retained
runtime attestation and the independently observed NL1 consumed request/open fence.
Its production mandatory mode checks the independent binding in a fresh isolated
Python process with no unit environment. It does not call Resume.run, terminal
reconciliation, attestation injection or recovery record writers. Failure is read-only.

The isolated native transition starts from a genuinely accepted192343eb forward
operation with nonempty queue/cursor/history, switches exact collector source only,
observes twice without changing history bytes/mtimes or live binding, and proves
unknown/changed/missing/extra sources refuse before IPC/SSH. Live prepare refuses.
Stopped support captures and independently verifies/repeats with the successor
selection, preserving data/markers and strict unsettled drain. Forward recovery
uses a new operation/authority and retains queue/cursor/predecessor bytes. Both clean
exit and simulated prior-boot accepted evidence are covered; the latter qualifies
the BOOT_CHANGED branch with real systemd stop/new-process startup, not a physical
reboot of the owner's live host.

Exact companion source: `8b9355db6a114e13f53d3d7298060057acb06da8`.
All four workflows PASS: native45922859518, phase045922859519, Linux45922859600,
Android wire45922859551. Independently downloaded native artifact15165334024 SHA256
`02f041855f15648b5dd8ef3000f69e5903d3ae3eb0eae0cc4ec3cc3f0f8b439f`
contains360 passing testcases, no failures/errors/skips, and5 native sandbox cases.
Initial targeted16 PASS and broader local111 PASS are retained. An exact-source
local repeat produced15 PASS/1 prerequisite JSONDecodeError: the unchanged notice
snapshot fixture exposed its empty, not-yet-published output before transition.
That failure is retained, not counted as PASS. Three subsequent bounded exact-source
runs of both new native transition cases each pass2/2; no product retry or relaxed
guard was introduced. Immutable exact-source CI is the acceptance test gate.

New375-file capsules on OWNER `ha02-tools-8b9355db` and NL1 `tools-8b9355db` have
independent closed-set/hash verification. Source archive SHA256:
`c343015e1bd39661b7cd1587104c69f94546dfdd8daa1e8cb5e1ea2819680a72`.
The old capsules/plan/authority/receipts are unchanged. No old completed Resume.run
or live resume.prepare was used as observation or tooling-update mechanism.

## Installation and recovery boundary

The new collector operation starts from a fresh panel01 observation, not
the interrupted pre-boot plan. Preserve original units, projections, gate inode pins
and private source rollback bytes. Hold only the two root collector timers, wait for
their existing invocations to finish, and keep strict collector admission/operations
barriers during the bounded source/binding transition. Do not stop support, replace
its archive/authority or change the NL1 generation. Qualify installed refusal before
I/O, normal service/timer cycles and read-only compatible observation before acceptance.

Retain a prestate/source rollback path; never restore projection/database/cursor
contents or clear historical markers. After any partial install, reconcile recorded
phases and exact bytes before another mutation; do not blindly replay preparation.
Keep the new qualified maintenance capsule alongside the old immutable capsules.
Console/publisher12-file installation, manual/external-dispatch closure, fresh common
capture/independent verification/normal resume remain subsequent work in the same NEXT.
Separate inventory3+12, probe14 and support33 markers remain unresolved history.

## Installed readback and preserved uncertainty

Private operation/evidence is under `/mnt/data/fc-ha02-mandatory-20261127`, new
`collector-panel01-operation`, not the pre-boot operation. Source rollback bytes,
effective unit/prestate, phase receipts and negative dispatch results are retained.
Only the pinned owner_capture wrapper changes; the other three collector files,
unit configuration and projection state are not replaced. Canonical root0600
independent binding pins the existing gate/admission/operations/pending inodes.

Fresh prestate discovers119 root-collector pending markers. Their exact bodies,
mtime, inode and permissions are retained independently. Strict Gate.drain explicitly
refuses UNSETTLED_OPERATION before installation. A separately qualified source-only
maintenance hold excludes admissions and waits for active local operations under
the same exclusive locks while retaining all historical markers. It is NOT a drain,
does not prove external dispatch completion, and never permits capture/data restore.
Five disposable maintenance checks cover strict refusal, cross-process closed
admission, normal release, active-writer timeout and historical mutation refusal.
Gate.drain implementation and its strict historical-marker rule remain unchanged.

- Both actual root collector services refuse75 under closed admission; fresh direct
  collect refuses before I/O. Both projection bytes/metadata remain unchanged.
- Twelve installed-source fresh-process checks, without unit/environment gate hints,
  cover direct collect and both main entrypoints against missing/replaced/invalid
  gate and invalid binding. Disposable mount namespaces preserve real gate paths;
  IPC/SSH/write traps remain untouched, synthetic projections unchanged.
- Compatible observer independently reports mandatory binding without environment;
  supportPID240065/NRestarts0, archive621009b8, authorityb0c470dc and NL1 generation
  b75ef2a2 remain unchanged. Old panel01/predecessor immutable checksums still pass.
  Separate independent IPC/NL1/encrypted-store reader verifies21 records,19 immutable,
  cursor4, queue0 and72 retained predecessor/history files; NL1 mailboxPID3705 unchanged.
- Both normal collector invocations complete success0; subsequent automatic starts
  at01:52:50/53UTC also complete success0. Only own root collector holds are removed;
  timers enabled/active/waiting. No console/publisher/PostgreSQL recreation.
- Real browser login, overview/subscriptions/payments/two existing cards and normal
  logout pass with no synthetic sessions/messages or manual business-data mutation.
- Original inventory15 (3 UNKNOWN plus12), probe14 are byte/mtime-identical. Six
  additional inventory markers date00:43–01:10UTC, before this collector install;
  they are separately retained, not erased or merged into the original UNKNOWN3.
  Root collectors119 and support33 remain distinct unresolved partitions.

This accepts installed mandatory binding plus its qualified maintenance paths only.
Exact12-file console/publisher activation, manual/ORM/CLI admission, external/Docker
dispatch settlement and fresh common capture/independent verify/normal resume remain
the same active NEXT. Historical e4eace1a is not promoted to a new capture.
