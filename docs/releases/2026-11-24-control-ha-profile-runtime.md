# CONTROL-HA — profile runtime and unit bindings, 24 November 2026

## Scope and decision

Continuation of selected CONTROL-HA-20261123 / HA-02, following the
[native renewal settlement guard](2026-11-24-control-ha-renewal-settlement.md).
This records actual existing Python, package inventory, effective sudo and systemd bindings
for the two previously resolved profile routes. It is **not activation or full helper qualification**.
Replication remains PASS; current independent trust/approval, coherent all-writer capture and
independent custody/final recovery remain three partial gates. No new numbered stage or HA-03.

No production helper/application handler, package import, service control or daemon reload was
executed. No chmod, package install, journal change, native lock, SSH/key/policy change, working
container change, client version, release/catalog/signature change or product DB/profile read.
The SSH/sudo queries can create ordinary audit records and filesystem reads can update atime;
this is not a claim of zero host activity. Existing strict SSH pins were used, without key fallback.

## Actual observations

Final scoped observations: **NL1 20:13:20.674531–20:13:21.637146UTC** and
**NL2 20:13:22.411603–20:13:23.807039UTC**. Both receipts are `PROFILE_BINDINGS_PARTIAL`.
The exact snapshot/helper interpreters agree with the preceding pinned source-chain evidence.

| Binding | NL1 | NL2 |
| --- | --- | --- |
| Actual isolated interpreter | CPython3.14.4, UID979 | CPython3.12.3, UID993 |
| Full strict site inventory | Refused: one inaccessible cache directory | 534 files, stable before/after |
| Five selected dependency RECORDs | Not accepted by this check | Hashes/sizes verify, versions match |
| Effective helper sudo listing | One root command, no arguments, NOPASSWD | One root command, no arguments, NOPASSWD |
| Configured restricted-bootstrap service | loaded / active / running / success | loaded / active / running / success |
| Loaded control process / queued job | ControlPID0 / empty Job | ControlPID0 / empty Job |
| Unit drop-ins | 13, exact files pinned | 0 |
| Nonempty loaded execution hooks | ExecStart, ExecStopPost | ExecStart |
| NeedDaemonReload | no | yes |

The unit status concerns only `family-connect-restricted-bootstrap.service`, not every NL
service or end-to-end client connectivity. Equal repeated loaded properties include invocation
and process IDs; a momentary empty Job/ControlPID is not all-writer quiescence or renewal settlement.
Empty execution arrays omitted by systemctl rendering were checked as typed empty D-Bus arrays.
No start, stop, restart, reload or native transaction was dispatched to test permissions.

**NL1 qualification limitation:** `cryptography/__pycache__` is root-owned0700 and not traversable
by UID979. It is not writable by that account. The pre-existing strict launcher inventory rejects
such a directory, so the new observer does not claim full dependency qualification or silently
ignore it. A separate interpreter-only `-I -S -B` probe succeeds under UID979. This observation
does not establish an application/import fault: Python may continue from readable source when a
cache is inaccessible. Do not chmod/delete this live cache merely to pass the inventory check.

**NL2:** selected versions are RNS1.5.1, cryptography46.0.7, pyserial3.5, cffi2.1.1 and pycparser3.0.
Their RECORD hashes/sizes verify against the static inventory, including17 referenced files in
venv/bin outside the site directory. Those extra pins are also rechecked after the probe.
Unhashed RECORD/bytecode entries are distinguished from hashed members; the full site-file pin
inventory includes bytecode bytes. No candidate `.pth`/sitecustomize/usercustomize file is found
in that selected site directory. This does not inventory every system-wide startup location.
No package or site hook was executed; native extension loading/shared-library/stdlib closure and
the existing helper's different `-E -s -B` root execution remain unqualified by this probe.

**Loaded unit versus disk:** NL2's `NeedDaemonReload=yes` is retained as a qualification limit.
It does not by itself prove different loaded command bytes, identify the cause, or authorize a
daemon reload. The main unit, loaded property projection and any drop-ins are pinned separately.
Both units reference environment files; their contents were not opened. NL1's loaded stop-post
hook is an additional external-completion boundary. No current process/shared-library attestation,
full loaded-versus-disk semantic comparison or actual helper/systemd lifecycle test is claimed.

## Implementation and verification

`scripts/control_ha_profile_runtime.py` reuses strict interpreter-link/account/venv pins from
the snapshot launcher. It bounds the site tree, parses static METADATA/RECORD without importing
packages, checks hashes/sizes and records potential site-startup files without executing them.
It rejects escapes, unsafe permissions/symlinks, missing/duplicate dependencies and changed pins.
The child uses exactly `-I -S -B`, cwd `/`, minimal PATH/LANG and the selected account's UID/GID/
groups; identity, isolation flags, interpreter target/version and no-site path are checked.
Repeated inventory/target pins reject drift. Receipts never permit capture or independent approval.
The inventory hash includes filesystem identity/metadata; it is not a portable content-only hash.

**135 tests PASS /0 skips**, Python3.14.4,16.25s:
`tests/test_control_ha_profile_runtime.py` and `tests/test_profile_snapshot_launcher.py`.
The37 new tests cover static RECORD integrity and external-script rechecks, metadata ambiguity, version reporting, startup
file/package discovery, isolation/identity refusal, changed inventories, bounded traversal and
the actual PYTHONPATH/sitecustomize exclusion. The real NL1 cache limitation is regression-tested;
the existing strict policy remains unchanged. No production service/import qualification is inferred.
Documentation check: four changed files/1052 local-link targets, zero errors; whitespace check
passes. Listed external URLs are not claimed as HTTP-verified public release artifacts.

Eight private read-only attempts are retained, including early refusal receipts. The observation
driver was corrected for shell-helper versus ELF pins, root-only configs, sudo alternatives links,
systemctl empty-array rendering and the existing13 drop-ins. These were observer assumptions,
not production repairs. The legitimate strict NL1 runtime refusal and NL2 reload marker remain.
Final probes use the current observer source; do not repeat the census as acceptance work.

## Evidence and bounded rollback

Raw source/config paths, unit/drop-in contents, sudo text, kernel identities and error receipts
remain in the owner's private0700 evidence store, files0600. Only sanitized hashes are published.
The local pointer is `/tmp/fc-ha-profile-runtime-current`; it is not a Git artifact or recovery key.

| SHA-256 binding | NL1 | NL2 |
| --- | --- | --- |
| Final private receipt | `1ffdea003e0f6fe00765648d9b6af8ceef4d01b931c9c7e5ab3afadd3975c1e1` | `e89762ab208119f9fdcf657c92cecdaeb2981252f5affeeebff20b1e21d3fff3` |
| Interpreter ELF | `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41` | `e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f` |
| Main unit on disk | `306aef9328bac4ae2fca2d2b4b6f17d1f87315d192e5f5b6e7906a6c20ae5f68` | `89763069c22df5c9c35be3eb9637e1f4bed6c42cf9e9e2e5b6d77210d70ee06b` |
| Loaded property projection | `e30222c3a86ac4cc7a8b511ac39423c6661d6c13ab071936ce28a0ecaa969c12` | `491d93babc0134fc1e55be24c217d63a7c2724026445518b9aa7892554f3f0be` |

NL2 site inventory: `4a3b9249e6cb7906fd9d67170759b95a7d6ab1532983d853730ff718925cdcc3`.
Sanitized summary: `e736d76d9408fca54314d23480876985661851e836d9ce757b58a3a9e127070b`.
Private scoped driver: `542071f70a43a133b723db39a616685d33ef91cff037aa3326a8f1c89ed068ee`.

No live rollback is needed: no deployment or service configuration changed. The new observer
can be omitted/reverted as a source-only change; do not restore product databases, alter sudo,
reload units, delete journals or touch emergency SSH as an observer rollback. Previous local
receiver/guardian/OWNER candidates remain unapproved and uninstalled.

Next selected work is the exact cache/runtime qualification and loaded/disk-unit reconciliation,
including environment/stop-post and full helper completion, plus remaining AWG/mailbox/support
external settlement. Then bounded manual-write coordination, independently approved gate/source/
runtime activation, measured real drain/joint interval, coherent capture and independent current
approval/custody/final recovery. These are the existing HA-02 gates, not new numbered stages.
