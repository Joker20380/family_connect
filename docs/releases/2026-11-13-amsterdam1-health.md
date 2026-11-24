# Amsterdam1 — read-only health check, 13 November 2026

**READ_ONLY_HEALTH_PASS**, observed12:33:08–12:35:19 UTC. Owner asks to check
Amsterdam1 after the separate RU recurrence. Canonical target is `nl-amsterdam-1`,
`185.10.158.212`, verified against the existing collector mapping and SSH host pins;
the retired `186.246.45.246` is not queried. No remote mutation, restart, deployment,
new trust pin, assignment/subscription change or phone operation is performed.

## Observed result

Three samples over131.590915s pass: watcher, AWG and TCP are active/successful,
with stable PIDs/invocations, unchanged code/configuration/binding hashes and
restart counters0. Every sample has `applied` readback younger than2.5s,64 retained
records/52 allowed, registered peers covered by retained records and exact equality
of persisted TCP id/email/flow to allowed decisions. No current
`transport-failure.json` is present. Actual cohort admission advances
1794573284→1794573419, crossing the initial expiry and finishing within the renewed
lease; this is not merely an initial startup allowance.

| Service | PID | Observed start, UTC |
| --- | ---: | --- |
| Watcher | 1913886 | 7 November21:55:20 |
| AWG | 1913904 | 7 November21:55:20 |
| TCP | 3105804 | 13 November11:48:44 |

Monitoring, restricted-bootstrap, Reticulum and mailbox are also active/successful,
restart counters0 throughout the samples. Restricted-bootstrap start is13 November
12:06:28 UTC. These earlier starts are observations, not actions in this check;
zero current counters do not establish that a service was never restarted.

Credential-free workstation TCP connects to the canonical endpoint on443 succeed
three times:58.331ms,11.178ms and49.940ms. Existing independent panel probes also
show three recent successes. Panel transport snapshot observed12:33:58 UTC/imported
12:33:59 UTC is `ok` and matches the actual node archive. Inventory is fresh;
`registry_status=not_collected` is expected for NL, not an unavailable RU registry.

Remote disk has37GiB free/21% used. Memory full-pressure averages are0.00%; I/O
full-pressure averages are0.00% in all three samples. The RU-like storage-pressure
condition is not observed here during this window. A single bounded, low-priority
warning-level journal read for watcher/AWG/TCP/restricted-bootstrap over the preceding
hour returns zero records without timeout; this is not proof about all prior history.

## Actual runtime and boundaries

- Node archive SHA256: `f7571bd42bbd583017fc590b20c7c7097059d7f202fef8323558c4fa8f47885d`.
- Gateway SHA256: `69f32dbfdf0db5f57fb598d58935b5f2b098e53d0c0e2ac24517ad299ced26bf`.
- These are observed Amsterdam1 bytes, not the distinct RU runtime or a newly built
  candidate. No version change, rollout or rollback is needed for this check.
- **USER_TRAFFIC NOT_RUN**: active services/TCP443 reachability do not prove an
  authenticated AWG/REALITY tunnel, phone DNS/HTTPS/egress, restricted bootstrap
  under white lists or mailbox message delivery. No synthetic profile or owner key
  is used, and no message is sent.

Private samples/driver/receipts are retained under ignored
`state-client-build/amsterdam1-check-20261113/`; raw identity/configuration evidence
stays out of Git. Local root/data free space remains1.9/2.6GiB; no cleanup or build.
Documentation links/whitespace and staged scope/secret-marker checks are the only
source checks needed; no application code changes or historical test-suite reruns.

[RU recovery and its still-open cause](2026-11-13-ru-recurrence.md) are separate.
This healthy Amsterdam1 observation neither closes RU replacement nor starts queued
support/public-broadcast/payment/desktop work. Existing owner Android125 and the
[confirmed support exchange with user tunnel OFF](2026-11-12-android125-owner-install.md)
remain unchanged.
