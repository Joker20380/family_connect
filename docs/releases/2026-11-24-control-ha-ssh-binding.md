# CONTROL-HA — SSH dispatch bindings, 24 November 2026

Selected task: CONTROL-HA-20261123 / HA-02, remaining fleet/manual writer bindings.
This closes the earlier default-key-file/literal-path observation gap for the explicit
accounts and connection contexts below. It does **not** close manual admission, settle
external work or authorize a coherent capture. Replication PASS; the same three other
HA-02 blocks remain partial. No new acceptance stage, deployment or version change.

## Bounded observer

`scripts/control_ha_ssh_binding.py` queries `/usr/sbin/sshd -T -C` for each existing
account in the writer preflight inventory. Contexts are the actual pinned SSH connection
and the fixed RU/NL1/NL2 source addresses, using the actual local address/port. The
projected policy must contain every required field and `UseDNS no`; unknown, incomplete,
duplicate or unsafe values refuse. The default on-disk sshd configuration is evaluated;
this is **not** an attestation of the running daemon's loaded configuration or alternative
startup flags/configuration files.

The observer follows only standard declared `AuthorizedKeysFile` paths under the observed
account home, including `%h`. It does not follow symlinks, custom key paths or private-key
arguments. Quoted commas/escaped quotes are parsed without treating key comments as options.
Unknown key formats, malformed/oversized inputs, failed reads and sshd errors refuse rather
than produce an empty successful inventory. Missing accounts/files are explicit.

Two observations of the selected policy projection, account IDs and authorized-key contents
must agree. Command/key/file/context values are hashed; raw commands, keys, comments,
source-address restrictions and the operator's source IP are not exported. Dynamic key/CA/
principal providers remain explicit, never treated as inspected. `restrict` and a lexical
mention of a capture launcher are not proof of admission. Every successful result still
sets `capture_permitted=false` and `all_writers_qualified=false`.

Only sshd test-mode processes run remotely; forced commands are neither invoked nor imported.
The code streams through stdin without installation, with a90s process alarm and5s query
timeouts. No SSH policy/key edits, daemon reload, product service action, signal to an existing
process, lock acquisition, database read, package install or working-source change occurs.
This observation does not claim service availability or unchanged application activity.

## Actual results

All connections use existing agent-backed authentication and strict existing host pins;
`UpdateHostKeys=no`, no pin replacement or authentication fallback. NL2 retains the previously
owner-accepted pin, not a new independently authenticated provider-console identity.

| Node | UTC observation | Accounts | Root keys | Root keys without per-key command | Other forced-command keys |
| --- | --- | ---: | ---: | ---: | --- |
| RU | 18:18:48.334509–18:18:48.714055 | 3 | 3 | 2 | none in the selected non-root accounts |
| NL1 | 18:18:49.394452–18:18:50.188305 | 6 | 4 | 1 | one for `family-restricted` |
| NL2 | 18:18:50.838573–18:18:51.464273 | 5 | 3 | 1 | one for `family-restricted` |

All14 explicit accounts exist. All four named context projections agree per account, as do
the repeated observations:112 sshd test-mode queries total. Every selected context reports
`ForceCommand none`, public-key authentication enabled and no dynamic authorized-key,
trusted-user-CA or principal-command provider. Thus no global ForceCommand in this tested
on-disk projection supplies the absent per-key command. This is configured-key evidence,
not a successful login test of every key or source restriction.

RU has password authentication disabled and `PermitRootLogin prohibit-password`.
NL1/NL2 have password authentication enabled and `PermitRootLogin yes` in this projection.
That does **not** establish that any account has a usable password, that PAM/account rules
allow login, or that the live daemon loaded the same policy. No password, shadow data or
authentication attempt was collected. Do not silently change SSH authentication as HA work.

The two restricted-account commands are now included despite the earlier literal-root matcher:
NL1 command hash `5e05e31a2a151966f7c933fc5e541034ad91e13fa61ba88735de817a88c2ac5f`,
NL2 `2547d55c866b27a076f36af5ee885198015c54f0dad9b1fdcc178eb7b7ccabf2`.
Each has one shell token; neither mentions the prepared capture entrypoints. The root
forced-command entries have no such lexical mention either. That is not proof that an
indirect wrapper lacks admission: installed source/dependency binding remains required.
The shared NL root command hash
`57f8bca933ffb4f8f1a2c146e5d56acde1ef596fbfcf263a4c3106fca361ca89` exactly matches the known
`/usr/bin/python3 /opt/apps/family_connect/friends-awg/awg-gateway.py register` route; no
command is dispatched to establish this match.

## Decision and remaining completion gate

Adding the prepared launcher to service keys alone cannot close manual root dispatch.
Do **not** delete owner root keys, disable SSH/passwords, change account shells or reload
sshd as an improvised barrier: that risks losing recovery access and exceeds this observation.
Do not equate a key without a forced command with a malicious operator or an actively running
writer. Root remains a trusted administrator, not an adversary this cooperative gate can fence.

The next bounded implementation must use this observed route set, not repeat a broad census:

1. Resolve the exact installed forced-command source/dependency pins and bind participating
   routes to the already-built receiver launcher. Review effective daemon startup/config
   separately; this on-disk projection alone cannot approve installed participation.
2. Explicitly coordinate a time-bounded **no manual product writes/deployments** interval
   with all administrative dispatchers, while retaining emergency SSH recovery access.
   Automation must use the admitted entrypoints. If this operational precondition cannot be
   established, refuse capture; the observer cannot manufacture an owner acknowledgement.
3. Independently reconcile already-dispatched SSH/Docker/support/publication work, then measure
   real flush/capture latency and establish the overlapping all-store/fleet interval. A returned
   client call, empty process sample or lexical command match does not settle remote effects.

These are inputs to the existing coherent-capture gate, not new numbered stages. Independent
OWNER image/config approval and current checkpoint/key/access custody still precede the final
combined recovery. Working OWNER images/gates remain at the
[previous observed state](2026-11-24-control-ha-owner-upgrade.md); no OWNER container access
occurs in this step. Current NL authorization remains read-only/isolated qualification,
not receiver installation or a working-service change.

## Checks, evidence and rollback

`python -m pytest -q tests/test_control_ha_ssh_binding.py
tests/test_control_ha_writer_preflight.py tests/test_control_ha_installed_census.py`:
**112 PASS /0 skips**, comprising50 new parser/context/redaction/refusal tests and62 existing
writer/census regressions. Tests cover unscoped/unsafe inputs, standard versus private/custom
paths, symlinks, read errors, forced/dynamic providers, absence, drift of policy/key contents,
exact sshd test-mode invocation and unconditional refusal of a capture permit.
Four changed documentation files pass the public-doc checker with1044 local-link targets;
whitespace checks pass. Listed external URLs are not counted as HTTP-verified links.

Private reports, stderr, source pins and per-account/context summaries remain under
`~/.local/share/family-connect/control-ha/20261124-ssh-binding-oks98hlh/`, directory0700,
files0600, outside Git. Observer source matches the executed bytes:
`593acfdb98ea6e7ece1fa842120e360956bce30bc58a5beaed40d4e86d040c4f`.
Imported writer observer pin:
`730e411e147b182aa81eab9dbb4cde2163dfa13bb9d919a1db23437f500d005a`;
census pin:
`e0bd54e5a075f7b91e62114607bdaafc3583f0e8ea72b3ce1ab1baa21aeb4ef6`.

| Receipt | SHA256 |
| --- | --- |
| RU | `ee6eca67fac2fefa7bb6302460a9a2064465918d22759c8d3946165cdf1b869f` |
| NL1 | `16a6ce62e042c07519cc0fcd532f1b1c9bf5a90660c1d0c49c9bc2fe62713caf` |
| NL2 | `d617db761072bbfd1161039197e3d8c0dcb6057e5bea30ff1c0f213db4ca3639` |

All observation processes have returned. Rollback is process exit only: no persistent
installation, held barrier or changed service/SSH setting needs undoing. Retain private
evidence and existing recovery access. This is a source/evidence checkpoint, not a rollout,
release, independent approval or HA-02 acceptance PASS.
