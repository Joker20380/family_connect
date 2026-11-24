# CONTROL-HA — cache and selected service qualification, 24 November 2026

## Scope and decision

Selected CONTROL-HA-20261123 / HA-02 continuation of the
[profile runtime observation](2026-11-24-control-ha-profile-runtime.md). This closes the
targeted cache-content/permission experiment and the selected NL2 loaded/disk-setting comparison,
not full installed-runtime acceptance. Replication remains PASS; independent current trust/approval,
coherent all-writer capture and independent custody/final combined recovery remain partial.
No HA-03, client version, build, installer/catalog/signature or production deployment changes.

Only existing strict-pinned NL1/NL2 SSH connections were used. Working service files, permissions,
packages, sudo/SSH policies, journals, profiles and product data were not changed. No application
package/helper import, helper execution, service stop/restart or daemon reload occurred.
The native experiment created synthetic files in one owned temporary `/run/fc-ha-cache-*` directory;
its removal and unchanged interpreter pins were verified. SSH/audit and ordinary read-atime effects
are possible. This is deliberately not described as zero host writes.

## NL1 — cache contents and actual permission behavior

At **20:21:21.647341–20:21:21.651181UTC**, the four retained cryptography cache files and
their readable source siblings were bounded-read without importing the package. All four
`__about__`, `__init__`, `exceptions` and `utils` CPython3.14 caches have matching interpreter
magic, timestamp/size headers and compiled source code. No source or cached application code
was executed. The final offline validator also compares recursive code metadata, including
filename, qualified name and stack size: Python code-object equality alone ignores some fields.

The installed pinned **Python3.14.4** then ran the committed synthetic fixture at
**20:32:29.248975–20:32:29.493237UTC**, with exact `-I -S -B`, minimal environment and cwd `/`.
The fixture gives a harmless synthetic cache a different body from its readable source:

- UID979 cannot traverse its root-only0700 cache directory and imports the readable source.
- Root imports the synthetic cached body; therefore root-helper cache bytes must not be ignored.
- Both results are asserted, the cache bytes/file set remain unchanged, the parent removes its
  owned directory and checks the installed interpreter/symlink pins again.

Result: **NATIVE_CACHE_PERMISSION_STAND_PASS**. This demonstrates that inaccessible cache alone
does not break source import in the tested interpreter, not that the full live application works.
The existing strict launcher/site-inventory refusal remains unchanged. Do not chmod/delete live
caches or treat this supplementary proof as approval to bypass that inventory. Native extension,
shared-library/stdlib and actual helper environment/lifecycle qualification remain open.

## NL2 — selected settings match; reload cause remains unknown

At **20:22:57.194783–20:22:57.316968UTC**, the main on-disk unit and typed loaded D-Bus
projection match for all **14 selected Service settings**: Type, User, Group, WorkingDirectory,
EnvironmentFile reference, ExecStart path/argv/ignore-failure, Restart, RestartSec, TimeoutStopSec,
UMask, NoNewPrivileges, ProtectSystem, ReadWritePaths and PrivateTmp. No extra loaded execution
hooks or loaded drop-ins occur in that projection. Environment-file contents were not read.

At **20:24:36.777776UTC**, a separate search of the manager's12 UnitPath entries found zero
applicable existing drop-in directories or `.conf` files for this exact unit, its dash-prefix
hierarchy and `service.d`. This is not a scan of unrelated services. The scoped unit remains
active/running, NRestarts=0 and **NeedDaemonReload=yes**. Its observed ActiveEnterTimestamp is
20:21:50UTC, later than the preceding census; no service action was issued here and no restart
cause is inferred from that timestamp or the restart counter.

Systemd reports255 (255.4-1ubuntu8.18); the unit fragment SHA remains unchanged and its mtime
is4 November20:27:59.760166UTC. Upstream
[v255.4 unit_need_daemon_reload](https://github.com/systemd/systemd-stable/blob/v255.4/src/core/unit.c)
can report a manager-wide outdated-unit flag, fragment/source mtime changes or changed/newer
drop-ins. The exact Ubuntu implementation and manager's cached load-time metadata were not
attested. The observed marker therefore remains **unexplained**, not proof of a command mismatch
and not permission for a global reload. No PID1-memory or whole-manager dump was attempted.

The14-setting comparison is explicitly not full Unit/default/dependency/environment equivalence.
NL1's13 drop-ins and stop-post lifecycle also remain outside this targeted NL2 comparison.
The first NL2 GetUnit read failed, two bounded read-only probes succeeded and one NL2-only retry
completed. The failure is retained; no server repair or cause is invented.

## Source and verification

`scripts/control_ha_runtime_qualification.py` performs offline, bounded cache/header/source
comparisons and narrowly scoped unit parsing. Unknown Service directives, unsupported grammar,
duplicate keys, malformed typed properties and loaded drop-ins fail closed. Setting differences
are reported separately from NeedDaemonReload. Its CLI constrains input size, CPU, address space
and core dumps; retained receipts are evidence inputs, not a general untrusted-marshal sandbox.
Every result keeps capture permission and independent approval false. Neither this utility nor
the synthetic fixture is wired into production admission or the old strict inventory policy.

**190 tests PASS /0 skips**,8.54s, with Python3.14.4:
`tests/test_control_ha_runtime_qualification.py`, `tests/test_control_ha_profile_runtime.py`
and `tests/test_profile_snapshot_launcher.py`. The55 new cases cover source/cache/header and
receipt pins, optimization modes, non-execution, ignored-by-equality metadata, all14 selected
setting differences, extra hooks and malformed/unsupported configuration. The actual NL1 fixture
PASS is additional native evidence, not one of the collected pytest cases. Both retained receipts
also pass the final offline validator. Four changed docs/1056 local-link targets and whitespace
checks pass with zero errors;
external URLs are not claimed as HTTP-verified release artifacts.

## Retained evidence and rollback

Private receipts/source bytes remain outside Git in the owner's0700 evidence store, files0600;
`/tmp/fc-ha-runtime-limits-current` is the local pointer, not a recovery key. Only sanitized bindings
are committed. The final validation outputs keep the same hashes after metadata-check hardening.

| Evidence | SHA-256 |
| --- | --- |
| NL1 retained source/cache receipt | `498fd064304ccd0e4ac9c7382b36c8fcf0cc5f8718273b98ca8a4f7399523162` |
| NL1 final offline qualification | `74cd565c57540ff2382c3c2b1d930d2c2b7b37c7bd99b43f694eb544c48d14f7` |
| NL1 installed interpreter ELF | `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41` |
| NL1 committed synthetic fixture | `dfdfa33dd404a54feb6749e05fb2c7af7795cce8a8111a6db290ead28915fed8` |
| NL1 native stand and cleanup receipt | `bf3e80e92296a58b2e00f30e48ab0dcd37ddf51950ba3c3afff0e8a2dbf77f3b` |
| NL2 selected loaded/disk receipt | `0dfcc78f2b1369abf91d8efe999b47a0a1b02624aaa41fa0459e2f21eb483243` |
| NL2 final offline qualification | `28987647c8f88ac1e193813ce953e770c2959269d8257c137a0396b940065596` |
| NL2 scoped on-disk drop-in search | `8b46b5a2908f0596719f63b622af0ce09c93bec23b67debc3d6a6c8f78fd73c3` |
| NL2 unchanged main unit | `89763069c22df5c9c35be3eb9637e1f4bed6c42cf9e9e2e5b6d77210d70ee06b` |

No live service/data rollback is needed. The owned fixture directory is already removed; the
offline source-only utility can be omitted/reverted without changing existing inventory or
admission behavior. Do not restore databases, delete renewal journals, reload systemd or change
emergency SSH as rollback. Existing receiver/guardian/OWNER candidates remain unapproved/uninstalled.

Next within the existing HA-02 scope: complete actual helper/runtime/environment/stop-post and
AWG/mailbox/support external settlement, with the strict NL1 inventory and unexplained NL2 marker
recorded as limits of any activation proposal; then bounded manual-write coordination, independent
runtime/source/gate approval, real drain/overlap/coherent capture and current independent
approval/custody/final recovery. Do not repeat this cache experiment or the14-setting comparison
as new acceptance work. No automatic working-NL deployment is authorized by this source checkpoint.
