# Local panel availability — 10 November 2026

## Diagnosis / Причина

The owner reported the local panel unavailable during SUPPORT-CHAT-1 development.
`http://127.0.0.1:8765/health/` refused the connection. Both existing panel containers
were stopped, exit0, OOMKilled=false; immediately preceding health probes passed.
Docker's journal records graceful daemon termination at22:22:13UTC and successful
restart at22:27:05UTC. Both containers had restart policy `no`, explaining why they
remained stopped after Docker returned. This is not a new application crash or a
support-chat deployment. The initiator of the Docker restart was not established.

## Bounded recovery

- Started only `fc-control-plane-0-postgres-1`, waited for PostgreSQL readiness,
  then saved a private `pg_dump -Fc` and checked that `pg_restore --list` could read it.
- Set `unless-stopped` on the two existing panel containers and started the existing
  console. Same IDs/images/volumes; no `up --build`, recreation, cleanup or restore.
- Console image remains
  `sha256:c179d1aea89821c9386909d6bfed3face29391e3d8e8e590c2328d7dffc5eead`;
  PostgreSQL remains
  `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`.
- Volumes remain `fc-control-plane-0_postgres_data` and
  `fc-control-plane-0_synthetic_state`. Existing entrypoint runs its ordinary
  migrate/seed/static steps; latest console migration is still0011, not support0012.
- Updated the installed Compose file and source Compose with the same restart
  policy. No application source was copied into the running image.

Private backup lives under ignored local `state-client-build/panel-availability-20261110/`.
No row values, credentials, session cookies or dump contents enter Git or receipts.
Listing a backup is **not** an isolated restore test; none is claimed. No application
update was performed, so the separate pre-update restore gate is still required.

## Checks and limits

Both containers report running/healthy with `unless-stopped`. Health returns200;
inventory returns302 to the existing `/admin/login/`, whose GET returns200, preserving the authorization
boundary. Django check reports no issues, existing user count1, migration0011.
The initial diagnostic used `/accounts/login/` (404); the actual login route is
`/admin/login/`, not a new authentication failure.

Both existing read-only jobs subsequently return success: monitor22:54:37UTC,
network probe22:55:20UTC. Four focused source/context tests pass; installed Compose
validates;5 affected Markdown documents/750 links have zero link errors. Whitespace
validation passes. Authentication was not bypassed or reset; a new authenticated
browser session was not required for this unchanged-image restart.

Whole-host/Docker reboot acceptance was deliberately not run: it would affect
neighbouring services. Restart policy is verified by runtime readback and Compose
validation, not claimed as an observed subsequent reboot. Other containers were not
restarted or reconfigured. No production VPN, paid policy, RU/NL or phone change.

SUPPORT-CHAT-1 remains incomplete and uninstalled. Its working-tree Android124
candidate does not replace installed beta123. Real support delivery is not certified
by these panel health checks. No version, public artifact, update catalog or download
link changed in this recovery.

## Rollback

If explicitly required, restore only `restart: "no"` in the installed/source Compose
and apply `docker update --restart no` to these same two containers. Do not restore an
old DB or delete volumes to revert a restart policy. Deliberate `docker stop` remains
respected by `unless-stopped`.
