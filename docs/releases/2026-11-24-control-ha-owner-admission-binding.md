# 24 November 2026 — installed OWNER admission bindings

Selected task: CONTROL-HA-20261123 / HA-02. This is a targeted read-only continuation
of the [receiver source checkpoint](2026-11-24-control-ha-receiver-admission.md),
not a repeated fleet census, deployment, coherent capture or new acceptance stage.
Replication remains PASS in isolation; the same three HA-02 blocks remain partial.

## Actual observation and decision

The OWNER console and system publisher are **not configured to participate** in the
new admission boundary. A source push did not install those changes. Observation of
the two existing containers finds:

| Participant | Installed image | Observed host UID:GID | Gate environment | Gate mount |
| --- | --- | --- | --- | --- |
| console | `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a` | `10001:10001` | absent | no configured gate to resolve |
| system publisher | `sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab` | `1000:1000` | absent | no configured gate to resolve |

Both containers are running, not paused/restarting, with read-only root filesystems.
The sampled image/instance/start/argv/environment/mount/host-configuration bindings
are identical before and after the observation. This is not an in-flight drain or
proof that no request/DB operation happened between samples. The configured Docker
user string is not substituted for actual numeric process identities.

In particular, the publisher is observed as UID1000, **not root**. Treat its installed
identity as separate from the console, not as an assumption based on an image default
or old source configuration. User-namespace mappings and gate inode ownership are not
attested by Docker top/inspect; host IDs alone do not prove an in-container UID map.

**Decision: no coherent capture and no enablement from this observation.** There is
no configured common gate, and simply setting the same path for both services cannot
establish a validated single-UID boundary. Do not widen0700/0600 permissions, chown
existing product/token state, run the console as root or change the publisher identity
to bypass this failure. The proposed identity-preserving layout uses separate gates
for distinct runtime identities, jointly drained and held for one overlapping interval.
That coordination is not implemented/qualified by this preflight; independent successful
drains at different times would not suffice. Namespace/mount/inode bindings must also
be verified before enabling either gate.

## Reproducible read-only check

`scripts/control_ha_owner_admission_preflight.py` uses only six Docker Unix-socket GETs:
inspect the two fixed OWNER containers before/after and sample numeric process columns
by their immutable container IDs. It accepts only those names, the OWNER Compose project
and corresponding service labels. It does not invoke Docker exec, run anything inside
containers, read product rows/files/tokens, acquire locks, send process signals or
contact RU/NL. No services, mounts, policies, images, versions or catalogs are changed.

Responses are bounded to1MiB, sockets to3s, total execution to30s by an independent
kernel alarm. Duplicate JSON/environment fields, inactive/unexpected containers, missing
main process, invalid paths, bad process columns and changed bindings refuse. Gate mount
resolution uses the deepest path ancestor, so a nested read-only/tmpfs mount cannot be
mistaken for its writable parent. Non-tmpfs alone does not prove durability or a local
filesystem. argv/environment/labels/host settings and source/destination paths are
hashed rather than exported; token values and private host paths are never printed.
Docker inspect returns environment values in process memory; core dumps are disabled.

Run against the already installed local Docker daemon, with output retained privately:

```sh
umask 077
python scripts/control_ha_owner_admission_preflight.py > /private/new-observation.json
```

Exit0 means **observation completed**, not acceptance or authorization. Every successful
report has `capture_permitted=false`, `all_writers_qualified=false`,
`services_changed=false`, `commands_executed_in_containers=false`. Loaded source bytes,
user-namespace maps, gate inode identity, manual/programmatic writers and external
in-flight completion remain explicitly unattested even when every sampled field matches.
Any refusal exits1 with a fixed redacted error, not raw Docker responses or exceptions.

## Validation and evidence

104 focused tests PASS /0 skips:42 new OWNER-binding tests plus62 existing installed
census/writer-preflight tests. They cover redaction, GET-only endpoint allowlisting,
bounded/duplicate responses, real versus configured identity, missing/invalid gate,
mount shadowing, process disappearance/incomplete samples, changed container/config
bindings and refusal output. No historical release/platform suite is claimed.

Private observation, source pin and test/link receipts are retained under
`~/.local/share/family-connect/control-ha/20261124-owner-admission-m3lkVk/` with0700/0600
permissions, outside Git. The initial16:49:41.696–16:49:41.714UTC observation is retained
as `observation.json` (SHA256
`015357c13109b21c3f91d8d566a9997f71d4eb2ee238082887001ecc41b88eca`).
It precedes the final wording/runtime-shape tightening; final verification is recorded
separately, not substituted for the initial receipt.
Final16:52:37.521–16:52:37.539UTC observation completes with unchanged bindings and the
same missing-gate/distinct-identity result. The publisher's process records differ
between the two observations despite equal counts/configuration/UIDs; this is not
quiescence and no process-list equality is claimed. `final-observation.json` SHA256 is
`2a6a7b7db97e6d16e8f10fb73639716ed175cece4fb6fffbd70d6e838b48ce06`;
observer source SHA256 is `f2008b7735b445ea0c0926cc20ffd3ee99ff53dfda75365ac63785b2c935c639`.
Final targeted suite104 PASS/0 skips; four documentation files/1029 local-link targets
and whitespace checks PASS. External URLs are enumerated, not claimed HTTP-verified.

## Rollout, rollback and remaining work

This checkpoint installs nothing. Rollback is stopping this observer; it owns no live
boundary/service/config to undo. Do not restart previously stopped/failed services or
remove pending-operation records as an observational rollback. Current installed images
in the table remain unchanged; no build is represented as installed/publicly released.

Next: qualify identity-preserving joint drain of the OWNER identities in isolation;
complete actual source/config/argv/UID/mount and manual/SSH entrypoint bindings across
the existing writer inventory. Then settle external operations independently, qualify
flush latency and the overlapping fleet capture interval, obtain independent approval
and key/access custody, and execute the final combined current/post-ACK/stale restore.
Do not reimplement the completed receiver/OWNER/timer/renewal source hooks or repeat
the accepted NL2 retained-state recovery. Keep paid-watch/deny enforcement operating;
the current NL permission still excludes changes to working services. These are the
same three incomplete HA-02 gates, not HA-03/cutover or additional numbered stages.
