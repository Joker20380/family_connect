# OWNER Docker executor boundary — candidate, not installed

Selected HA-02 NEXT: executor admission **and** lifetime containment. AuthZ is a shared Docker
management-path change, not a per-project failure-isolated service. No fleet capture permit is
issued by `control.capture_docker`; CLOSE means admission only, never HELD writers.

## Exact qualification, 27 November 2026

Installed Engine29.1.3, Ubuntu build29.1.3-0ubuntu4.1, binary SHA256
`8f1c19d27e182ce6c82ddfd900d596195b0fd9d6740a9ff1ccac584e04355cb0`.
The native harness uses this binary with its own containerd socket/root/state/namespaces,
Docker data/exec roots, pidfile, configuration, network-disabled vfs Engine and disposable data.
The public Python fixture image is pinned in the harness. Product DB, keys and mounts are absent.

Native q2 confirms direct-socket denials for resource-bound exec create, old exec start, container
start/restart/unpause, restart-policy update, Binds/Mounts/local-bind-volume/VolumesFrom/ancestor
mount create with a different container ID, and archive PUT. Archive PUT first demonstrably changes
the disposable protected mount before CLOSE; `docker cp` therefore belongs in this boundary.
Resource comparison uses the actual statx mount ID and backing device/root, including symlink and
bind aliases, not just names/IDs. Unknown volume driver/options fail closed; inline DriverConfig
cannot hide an anonymous bind volume. This is a finite policy, not general Engine API support.

**Counterexamples retained, not counted as containment:** an already permitted request delayed
before dispatch executes after CLOSE; detached children keep writing an open FD, prefaulted shared
mmap and late temporary-file rename; internal automatic restart launches again without an AuthZ
request. Pending callback count0 does not repair any of these. A resource-enrolled, non-escapable
executor domain must finish cleanly and remain physically constrained for the interval.

Valid plugin attachment/removal through configuration+SIGHUP preserves the isolated daemon PID.
`docker info` can still report Authorization=[] after a successful reload: use actual callback and
denial probes, not that field alone. Plugin activation must handle an empty body, chunked requests
and Engine's `RequestUri` spelling. Loss/restoration of the config hook or daemon replacement makes
the old lease terminal FAILED. First failure is retained. A lost RELEASE response can be read back
and repeated **in the same process** without effects; a replacement process cannot adopt that lease.

An unrelated disposable neighbor can exec/write normally with the live policy. Killing enforcement
causes the neighbor's management request to fail too, while its existing process continues. This
global API failure is a deployment risk, not evidence that neighboring workloads are unaffected.
Policy rejects unclassified mutation APIs and elevated/unknown container powers; normal neighbor
build/plugin/device-management operations are not qualified by the simple neighbor exec test.

## Installation/recovery plan — NOT EXECUTED

### Enrolled-domain composition, source-only q7

`DomainAdmission` now requires the configured dedicated CgroupParent, private cgroup namespace,
ordinary runc and restart=no for protected resource containers. New resource aliases/IDs cannot
choose another parent or enable automatic restart. Privileged exec and unproven old exec privileges
refuse; host control/cgroup/proc/device/socket/config mounts are not treated as harmless neighbors.
Every mount is checked, including mounts after the first protected one. This is intentionally a
finite supported runtime, not a claim to cover arbitrary Docker plugins/runtime extensions.

`ExecutorBoundary` composes that admission with the existing launch keeper and recursive ClosedCgroup.
It waits boundedly for tracked API callbacks before clean domain termination; pending uncertainty
refuses, it never becomes a drain permit. The actual empty cgroup is frozen and the same admission,
daemon/config, cgroup inode/freeze and keeper leases must remain valid. Release is ordered and recorded;
a completed same-process release is idempotent. An incomplete release requires reconciliation, not
another acquisition. It does not restart product services or adopt a dead controller's capture lease.

Exact-binary q7 qualifies a real container plus detached exec child retaining writable FD/shared mmap:
both finish before HELD, then direct start/new-ID create refuse and data remains unchanged. Automatic
restart policy is rejected before holding. Normal container restart and clean stop after release pass.
Enforcer hang/death makes check refuse within its timeout while the physical freeze remains; controller
death also leaves it in place. Explicit same-identity reconciliation thaws only the empty lab domain;
none of these fault cases is labeled a completed capture or normal application resume.

q5/q6 did not accept cleanup: during hook removal GET /version returned HTTP200 with an empty body;
the fixture dereferenced None. q6 preserves the exact traceback. q7 retains the empty-read observation,
never treats it as readiness, then performs only bounded idempotent readback until a valid response.
Cleanup confirms all own children exited and no own freeze remains. The observation does not prove
the deeper Engine/response cause. The earlier q3 missing PYTHONPATH fixture failure is also retained.

**Still missing at production cutover:** `/containers/create` or `/containers/{id}/start` admitted by
the existing daemon **before the hook was installed** may still target a protected volume outside
the new parent. The new policy and a later census cannot retroactively fence that request. Installed
console/publisher remain in their old default scopes with unless-stopped. Initial enrollment must
prove a no-bypass boundary for those requests and move the existing images/config into the enrolled
domain without affecting unrelated workloads. Neither the component nor q7 sets
`initial_admission_coverage_proven=true`. This is the next concrete integration gate, followed by
the accepted stopped-support/independent reader/native-pair/custody lifetime and remote receiver rows.

Read-only working prestate21:20UTC: dockerd PID4386/invocation
`849e0a8de257429892b378bcfc482fcf`; ExecStart uses `-H fd://` and the installed containerd socket;
ExecReload sends SIGHUP. `/etc/docker/daemon.json` contains `runtimes`, no authz and no live-restore.
Both installed console/publisher still have empty CgroupParent and `unless-stopped` restart policy.
Their images, IDs, PIDs and working configuration are unchanged. Do not re-create PostgreSQL or
publisher casually or run the repository's synthetic/seed compose as a recovery command.

1. Finish actual resource-domain enrollment and late-work containment first. Account for API work
   admitted before initial hook attachment; a post-reload empty request census is not that proof.
   Qualification must include actual installed images/config, whole descendants, automatic restart,
   fresh-process recovery and bounded support/runtime-directory/IPC/panel resume. Current q2 is
   an admission experiment, not this gate.
2. Save exact root-owned daemon config bytes/hash/mode, effective unit/config and installed project
   configuration privately. Pin executable/source closure and protected native parents/volume backing
   sources, plus indirect engine/control powers. Validate the plugin socket and protocol before any
   reload; do not overwrite the `runtimes` map or other owners' plugins/configuration.
3. Only with all gates accepted, merge the single own plugin entry under a checked fresh prestate;
   validate configuration, install own supervised service, reload, verify unchanged daemon generation
   and actual effective direct-socket denials. Record that all Docker clients use this hook. Do not
   claim the change is per-project merely because normal admission decisions are resource-scoped.
4. Hook/service failure invalidates capture. Preserve the first reason and exact outstanding effects;
   never replay an unknown mutation. Keep physical restrictions until their explicit reconciliation.
   The bounded recovery path removes **only** the operation's hook against its recorded config hash,
   reloads and checks effective API recovery. A daemon crash requires the separately qualified shared
   daemon recovery plan; live-restore is not enabled, so restarting it can affect other applications.
   This is not authorization to stop the entire daemon or neighboring services to complete HA-02.
5. Record readback before removing each own external restriction; response loss is reconciliation,
   not automatic re-execution. No production install until the shared-failure/recovery impact and
   finite domain contract are qualified. Restore normal project configuration, not stale product bytes.

Initial laboratory setup implicitly reused the installed containerd namespace and is **not** accepted
as an isolated qualification. Only its two identified disposable tasks were removed. Separate q1/q2
containerd runs supersede that setup, not its evidence. The first plugin protocol/fixture failures
remain local history; the initial invalid activation causing a lab daemon exit is a warning, not a
qualified shared production recovery. No product daemon reload, stop, gate close or capture occurred.

Continue with [finite OWNER lifetime composition](owner-maintenance-boundary.md). Preserve all UNKNOWN
groups and strict Gate.drain. Custody, source-host-free restore, reboot startup and production
onboarding remain separate acceptance gates.
