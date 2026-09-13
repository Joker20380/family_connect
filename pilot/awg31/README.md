# Isolated AWG 3.1 experiment

This is a locally patched experimental engine, not an upstream release or a client
update. See [acceptance and limitations](../../docs/releases/2026-09-13-awg31-experiment.ru.md)
and [all measurements](../../docs/releases/2026-09-13-awg31-experiment.json).

From the repository root:

```sh
docker build -f pilot/awg31/Dockerfile -t family-connect-awg31:experiment2 .
```

Extract `/opt/awg31/` from that image into an operator-owned scratch directory with
`docker create` / `docker cp`, then remove the stopped extraction container.
The directory contains `amneziawg-go`, `awg`, and both upstream licenses.
A separate standard `wg` binary is required for the kernel WireGuard control case.

On a Linux host with TUN, kernel WireGuard, iproute2/netem, ethtool, ping, Python3
and Polkit, run using absolute binary paths:

```sh
pkexec unshare --net /usr/bin/python3 pilot/awg31/lab.py \
  --engine /absolute/path/amneziawg-go \
  --awg /absolute/path/awg \
  --wg /absolute/path/wg
```

The script refuses the host network namespace and namespaces with existing links.
It creates one named server namespace, fresh synthetic private keys, and temporary
interfaces. Normal completion/errors clean up the resources. Stdout is JSONL metrics;
no private configurations or packet payloads are emitted. Do not SIGKILL the harness:
crash recovery is not implemented. No Amsterdam deployment, production identities,
client journals, application update or signed catalog changes are performed.

The Docker build gate runs the explicitly listed device/runtime packages three times.
The broader upstream `go test ./...` currently fails the external Outline integration
fixture; the failure and exact scope are retained in the report. The local patch is
not a general solution for atomic parameter changes while traffic is in flight.

## Adverse conditions

Add `--resilience` for three AWG base runs with invalid profiles, wrong header key,
mismatched H4, tunnel MTU boundaries,1% independent random loss each direction,
1MiB integrity-checked TCP transfer, brief100% loss, client link cycle, server engine
restart, and accelerated rekey. The readiness observation window is30s; this is not
an accepted product reconnect SLO. Original defaults/rekey timing and path MTU
blackholes are separate acceptance work. Each transfer has a90s budget.

Experiment2 adds a separate tools patch and a C boundary regression. Engine bytes
are identical to experiment1. Full upstream Outline integration remains unresolved.
See the dated resilience report in docs/releases for initial failures and measurements.
