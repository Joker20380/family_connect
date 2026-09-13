# Isolated AWG 3.1 experiment

This is a locally patched experimental engine, not an upstream release or a client
update. See [acceptance and limitations](../../docs/releases/2026-09-13-awg31-experiment.ru.md)
and [all measurements](../../docs/releases/2026-09-13-awg31-experiment.json).

From the repository root:

```sh
docker build -f pilot/awg31/Dockerfile -t family-connect-awg31:experiment1 .
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
