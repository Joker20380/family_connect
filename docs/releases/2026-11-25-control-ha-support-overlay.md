# HA-02 — authenticated OWNER support candidate, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02, continuing the
[support lifecycle](2026-11-25-control-ha-support-lifecycle.md) and
[manual operator boundaries](2026-11-25-control-ha-operator-capture.md).
The user explicitly requested a local password window and continuation. This checkpoint restores
technical access and qualifies the exact installed-shape candidate; **it does not install support,
close all runtime writers or complete stage2**.

## Authentication and actual prestate

A private temporary askpass helper invoked Zenity's password field and passed its stdout directly
to `sudo -A -v`. The password did not pass through chat, model-visible output, command arguments,
an environment variable or a file. The authenticated retained terminal then returned UID0 from
`sudo -n id -u` and successfully executed the scoped privileged checks below. No sudoers, polkit,
password, account or permanent access policy was changed. This is the ordinary temporary sudo
timestamp in that terminal, not globally passwordless access; later expiry requires another UI
authentication rather than an alternate escalation route.

Root readback at15:50:30UTC: working `family-connect-support.service` remains active/running,
PID2022541,0 restarts, no capture gate and the old control-group/SIGKILL/40s policy. Its actual
`/proc/PID/exe` is now readable; SHA256
`52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`.
The configured installed environment reports Python3.14.4 and RNS1.5.1. All17 provisioning/
messenger version pins match, parsing pip hash options separately from the LXMF version.
This version check does not attest every imported dependency byte or in-memory thread state.
Seven threads are observed; their existence/absence does not prove complete persistence closure.

At16:00:03UTC the original argv and all3 unit files are retained privately, together with their
hashes. The same PID/argv/all19 source hashes remain unchanged. Three OWNER containers remain
healthy/running/0 restarts with unchanged PIDs/images. No RU/NL contact or working-service stop,
deployment, schema, private profile/key, product/public version or catalog/signature change.

## Pinned installed-shape package

`scripts/package_support_capture.py` reads only the19 explicitly bound Python sources in the
installed application and six reviewed candidate inputs. The checked contract is
`deploy/support-chat/support-capture-v1.json`. It emits exclusive, private, deterministic
`baseline.pyz`, `candidate.pyz` and `receipt.json`; file/directory/parent fsync makes successful
output durable. It never reads product keys/databases or copies arbitrary non-source files,
starts a service, changes a unit or edits the installed application.

| Delta | Scope |
| --- | --- |
| Modified3 | `provisioning/support_worker.py`, `provisioning/subscription_notifications.py`, `messenger/routed.py` |
| Added3 | `control/capture_gate.py`, `provisioning/support_capture.py`, `provisioning/support_lifecycle.py` |
| Preserved16 | Every other installed Python source remains byte-identical |
| Removed0 | No baseline source is removed |

Baseline archive SHA256: `3aeb6f2badd3172e1e8d9417df77d7c097bb822153dc65b18a8318a097f6dd28`.
Candidate archive SHA256: `ae30efc5271f53d1bbcfa49097f899831c31deb37a8bdabc536d19490f7765e6`.
Both include an entrypoint and source-only hash manifest, plus namespace directory entries.
The candidate changes exactly the already qualified admission/lifecycle/reader behavior; no broad
commissioning-kit replacement or dependency upgrade is performed. Baseline and candidate CLI
help run isolated from checkout; only the candidate exposes `--capture-gate`.

The builder rejects wrong source digests/closure, missing files, symlinks, hardlinks, FIFOs,
oversized input, invalid contracts, syntax errors and existing outputs. Interrupted outputs
remain for diagnosis and cannot be silently overwritten. Packaging does not attest old in-memory
code, configure a gate, bind installed launchers or authorize a coherent capture.

## Qualification and recorded failures

**36 tests PASS/0 skips**,58.85s:25 package cases plus the11 existing lifecycle cases repeated
against this exact archive where they launch a worker. They are not36 newly invented acceptance
gates. The lifecycle fixture validates loaded packaged-module provenance at startup and completion;
its actual user-systemd case explicitly passes the archive binding to the child unit.

```sh
FC_TEST_SUPPORT_BASELINE="$INSTALLED_APP" \
FC_TEST_SUPPORT_ARCHIVE="$CANDIDATE/candidate.pyz" \
FC_TEST_SYSTEMD_SUPPORT_DRAIN=1 python -m pytest -q -ra \
  tests/test_package_support_capture.py tests/test_support_lifecycle.py
```

An additional **system-level** transient fixture runs the same archived worker under actual
`fc-support`/`fc-support-ipc` and `/opt/family-connect-support/venv/bin/python`, not as the owner or
root. All data, keys, IPC and runtime files are synthetic and isolated from production. Its
main-only TERM/mixed/infinite-stop/no-SIGKILL settings are verified while stopping. After41s the
service is still deactivating and its admitted child alive; the encrypted store is not closed.
Releasing the synthetic child permits commit/close/exit0, with packaged-module provenance intact.
A fresh installed-interpreter process under the same service UID reads the committed encrypted
record and drains the fixture gate. Working service pre/post fields match. The owned transient
unit is stopped/reset; fixture sources/state/receipts remain private. This qualifies that bounded
system-unit stop, not every production sandbox setting, live remote outcome or RNS writer.

Initial28-pass/8-failure evidence is retained. Seven lifecycle failures were a provenance-fixture
mistake treating the external test runner's `__main__` as packaged; the fixture now uses the source
manifest and correct package-initializer names. The other failure came from attempting to import
every installed leftover module: unchanged `messenger/notices.py` refers to absent `service_events`.
That unrelated installed helper is not imported by the support worker. It remains byte-identical;
qualification now verifies the actual worker's transitive imports, not that all unused leftovers
are runnable. No missing dependency was silently added and no production error is declared fixed.
Four changed documentation files/1121 local-link targets and whitespace checks PASS.

## Evidence, rollout boundary and rollback

Private evidence directory: `/tmp/fc-ha-support-authenticated-20261125`. Original unit/argv bytes,
source-only archives, failed/final logs, synthetic system-unit state and invocation source remain
outside Git. Only safe source/tests/docs and the source-hash contract are committed.

| Item | SHA-256 |
| --- | --- |
| Privileged preflight | `c4bdcbad398a01ca0236c9840414903da620d36015a9122e97952ca3bbb26d19` |
| Final36 JUnit | `1ee5ec717cd575ce4b8eb0d19bbc539059c181ee7dad80a5abc49c62ff518225` |
| Installed-UID system fixture | `298386607d4601a529dfe18e41894347701dee665f27d8de4b4684f491373bbf` |
| Retained original argv/unit receipt | `44b1bb2272839fff8d6444be3824c315c77d8ef0085b80eed58e2c49a1248338` |

No production rollback is needed. Do not apply the new kill policy alone or stop the old worker
by its ordinary TERM/40s timeout. Next is a qualified legacy main-loop admission/drain mechanism
and an independent replacement/rollback supervisor binding these exact original sources/argv/
unit files and candidate. Reticulum's independent periodic persistence/cache cleanup and exit
handlers still require exact closure; a drained delivery thread alone is insufficient. Keep all
old external outcomes unresolved until independently reconciled, and preserve current stores/
feeds/pending markers across any later code/config-only rollback. Never use the baseline source
archive as a reason to restore old product data or manufacture an empty gate.

Installed manual/OWNER integration, fleet coherent capture, independent trust/custody/approval and
combined post-ACK recovery remain. Isolated replication PASS, same three HA-02 gates partial;
no HA-03, automatic failover, complete client E2E or new ETA. Authentication is no longer the
only immediate obstacle; do not replace the remaining technical transition gates with a restart.
