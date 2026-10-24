# Shared Auto policy process boundary

`fc-mesh --auto-stdio` embeds `carrier/desktopauto`. It is a managed child of a
privileged platform owner, not a standalone VPN or an invitation/rights endpoint.
`--version` advertises `auto_policy_protocol:1`; that is **not** a claim that the
desktop Auto host, capabilities, GUI or installed VPN path is complete.

The Linux adapter is `clients/linux/auto_policy.py`. `PolicyProcess` owns private
inherited pipes, one reader, one serialized platform worker and at most four
pending control tickets. `GuardedHost` places the real nftables guard around a
trusted platform implementation. It prevents a restricted candidate being
reported ready through an AWG plan. It does not fetch configuration or implement
the platform callbacks itself. `clients/linux/auto_mesh.py` now supplies a real
single-attempt MESH adapter using the same `PacketSession` as manual MESH: native
readiness/cache authorization, protected underlay, TUN/routes/DNS and native health,
without a second reconnect loop. It observes the remaining Auto deadline and
retains pending cleanup on failure. Unknown failures remain terminal; authorization
never becomes a temporary bootstrap failure. This adapter is not yet wired into
the product Auto coordinator. Normal configuration/AWG/TCP callbacks and external
authenticated root coordination remain required before enabling Auto.

Frames are4-byte big-endian length plus UTF-8 JSON, at most32KiB. Duplicate JSON
keys (including case-alias spellings), null fields, invalid UTF-8, unknown fields/actions, oversized/deep frames, mixed message
roles, reused request IDs and unexpected host replies terminate the channel.
No private key, profile, invitation, URL, identity proof or raw error belongs in
this protocol. Root-owned platform callbacks keep those outside the policy child.

Parent→child:

- `{"command":{"schema":1,"id":1,"action":"connect","generation":7,"network":true,"preferred":"awg"}}`
- `status` has no generation; `network`, `retry`, `lost`, `healthy`, `disconnect`
  require the current generation. `lost` carries an enum `reason`, `healthy` a
  boolean `healthy`, `network` a boolean `network`. Control IDs strictly increase.
- `{"host_reply":{"schema":1,"id":1,"ok":true,"candidates":["awg","tcp"]}}`
  answers one host call, not a control command. Candidates occur only for
  configure and contain unique normal types. Failure uses an exact category;
  `temporary_bootstrap` is valid only with BOOTSTRAP_UNAVAILABLE.

Child→parent:

- `host_call`: schema/id/generation/operation/budget_ms, plus candidate only for
  open/remember. Operations are configure, open, close, release, remember. Budget
  is remaining time, not a fresh retry allowance. Ready means the platform has
  verified authorization, TUN, route, DNS and health; guard readiness alone is not
  sufficient. Network availability must come from the service, not a GUI guess.
- `host_cancel`: the specific host-call ID. The parent cancels that operation and
  acknowledges only once it has drained. Even a success arriving after cancel
  cannot commit connected. The child starts no cleanup/next callback before ACK;
  a20s missing-ACK grace terminates the channel instead of overlapping work.
- `reply`: schema/id/ok/error/snapshot, after the control operation completes.
  Snapshot/status remains available during a host callback. `ok` means the
  operation was accepted by the controller; inspect snapshot for actual state.
  A failed cleanup must not be interpreted as successful Disconnect merely
  because it has a well-formed reply.

Now/jitter/pause, candidate ordering, retry limits and timers stay in the shared
Go controller. There is no Python/C# copy of that state machine. Only one normal
control operation and one cancellation waiter can exist. An initialization
barrier prevents immediate Disconnect racing ahead of Connect's generation.
Old-generation commands never cancel a newer session. Timed-out control tickets
must not be replayed; query status or explicitly disconnect the same generation.

EOF, malformed data or native death makes the Linux adapter cancel its active
host callback, then block and close the platform without releasing the guard.
The service must retain ownership/intent and supervise callback deadlines; it
must not create another owner while an uncooperative callback is still running.
The Python adapter cannot safely kill a Python thread. `close()` reports failure
if its bounded join cannot complete. The process-level systemd owner must then
contain/reap its own children and reconcile the journal before any new attempt.

The caller persists monotonic generations and creates a GuardedHost for the
matching generation. Private pipes authenticate this parent/child relationship;
they do **not** replace SO_PEERCRED authorization at the future GUI/service socket.
Neither the guard nor the policy process exposes a new external listener.

`scripts/check_desktop_auto_policy.py` exercises the compiled policy child,
Python root adapter and actual nftables/TUN in an empty isolated network. Its
platform fixture is deliberately synthetic: it proves IPC/guard lifecycle, not
live AWG/MESH authorization, service configuration, media bypass or full VPN.
The Windows protocol tests/cross-build likewise do not validate a Windows broker,
driver or GUI. All remaining two-client parity gates still apply.
