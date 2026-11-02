# Second Amsterdam ordinary-node preparation

Subsequent result: [ordinary AWG/TCP production admission](2026-11-02-second-nl-ordinary-live.md).
The preparation boundary below is historical; the new node is now admitted for new assignments,
while existing devices and MESH remain on the first NL. See the later report for reconciled
failures, exact publication state and rollback rather than treating this as another active NEXT.

## Authorization and trust

Continuation of FLEET-BOOTSTRAP-2, not a new PLAN ID. The owner requests a second
simultaneous Amsterdam node for Android, Linux and Windows and explicitly accepts
proceeding without another provider/VNC host-key comparison. This is acceptance of
the existing TOFU pin, **not** independent host authentication. StrictHostKeyChecking
remains enabled with the dedicated single-host known_hosts file. A changed pin stops
execution; no insecure SSH option, password in chat or new trust scan is introduced.

Read-only SSH preflight of185.10.158.196 confirmed the previously accepted RSA pin
`SHA256:0pv6U7BX3DpwojL8XAWwqcda06DKUG38S1036U9upgo`, Ubuntu24.04/x86_64, no reboot
required, no Family Connect units, no ordinary application directory, forwarding0
and only SSH/system resolver listeners. Existing RU and first NL were not accessed
or changed by this preflight. Rehearsal trials remain retired.

## Bound first-install source

`deploy/friends/standby-node.py` is a separate first-install helper for an unpublished
AWG3.1/TCP REALITY node. It does not change or bypass the signed disposable runtime,
permit, retirement, SSH or external-acceptance contracts. It is not a general fleet
production controller and has no MESH, renewal, catalog, user-invitation or paid action.

- Root-only exact manifest binds target, source commit, operation and all five source/
  binary files. Three native hashes are the accepted existing production binaries.
- Fresh node-local AWG/REALITY keys, AWG3.1 header material and short ID; zero peers/
  users initially. No existing server identity or private client profile is copied.
- Fixed ordinary service paths, no arbitrary argv, bounded subprocess execution with
  captured/suppressed private diagnostics. Dedicated TCP user;0600/0640 material.
- Preparation is separate from start; exact Xray config test and systemd unit verification
  run before startup. Existing service/port/interface/owned-chain collisions are refused.
- Fsynced first-install intent precedes writes. Interrupted or repeated preparation/start
  requires readback, never blind replay. A failed start stops only the two owned units and
  restores the captured forwarding value/removes only the owned sysctl file.
- Explicit stop preserves keys/config/database for recovery. An admission marker fences
  this unpublished-node helper from starting/stopping an admitted node.
- Registration remains the existing fixed AWG/TCP helper. Publication and registration-key
  admission are separate gates; a started standby is not a publicly admitted node.

Focused source qualification:29 new tests PASS; combined ordinary/routing/catalog/HTTP/
client regression316 PASS,25 existing environment-dependent skips, zero failures/errors.
The first template test caught a missing IPv6 full-tunnel route; the template was corrected
to the existing IPv4+IPv6 parser contract and the entire selected contour passed again.
This is not an assertion of IPv6 egress support. Client update versions are unchanged.

Native Windows conformance, ordinary-user access, desktop visual and Client builds for
the preceding routing source have completed successfully. Corrected Android wire CI also
passed. Full phase0/Linux preview were still running at observation, not claimed PASS.

## Deployment boundary

The first bound preparation was transferred but stopped before creating any unit or starting
a service: the private umask made newly created application ancestors0700, correctly denying
the TCP service user access. Readback localized the failure to that DAC boundary; forwarding
remained0 and both units remained absent. No automatic prepare retry was attempted.

The correction explicitly sets0755 on newly created, exact application ancestors, checks
existing ancestor ownership/modes without changing them, and adds an umask regression.
The focused source contour now has30 PASS. A separate network-disabled Ubuntu24.04 root
container ran the exact accepted native Xray config test as `fc-friends`, systemd-analyze
verification and positive TCP/negative AWG secret access checks: PASS. Systemd manager,
network routes and firewall observations in that simulation are fixtures, not service or
data-plane acceptance. The failed live preparation must be reconciled/preserved before a
new bound preparation; it is not treated as an installed or running node.

The separate `scripts/accept_friends_standby.py` operator-container harness consumes fresh
disposable probe credentials on stdin, validates profiles with the existing client parser,
checks all three native hashes, and checks AWG3.1 handshake/DNS/HTTPS/egress and REALITY
auth/DNS/HTTPS/egress. It has no MESH/publication path. Probe argv contains only fixed native
commands and private file paths; errors never echo credentials. Operator interface/routes/
processes are removed in finally paths. Target-side addition/removal of the disposable peer
is separate and must be receipted before any admission. Source contour:37 PASS, no skips.
The harness source is not itself a live acceptance result.

Next authorized work is its corrected bound unpublished preparation, local health and external
AWG/TCP acceptance, then separately guarded routing/backend admission. Existing production
MESH and renewal remain on the first NL; simultaneous second-node MESH/renewal integration
is not implemented or claimed here. No synthetic or retired permit is repurposed.

Rollback before admission: stop only the owned ordinary units through the bound helper;
preserve node material and receipts, do not reinstall the VPS or touch the first NL.
After admission, use the routing policy's higher-sequence catalog rollback and a separate
reviewed production operation, not this first-install helper.

Production RU/first-NL writes0; catalog publications0; invitations0; paid events0; phone
actions0. Public Android109/sequence4, Linux0.2.11, Windows0.2.15, catalog4, paid108,
owner entitlement, ledger1/4, cohort1/10 and revenue0 remain unchanged at this checkpoint.

[Compatible routing source](2026-11-02-fleet-multinode-source.md) ·
[Completed disposable reboot/retirement](2026-11-02-fleet-bootstrap-2-reboot.md).
