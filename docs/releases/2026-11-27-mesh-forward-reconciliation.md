# Bounded MESH forward reconciliation — 27 November2026

Selected task remains CONTROL-HA-20261123 / HA-02 OWNER/all-writer NEXT. This is a
current availability recovery, not a new deployment, common capture or HA-03 cutover.
Installed root collector b7f4cbd2/observer8b9355db, console3af9fbf9/publisher35158514 and
host binding sourceb49c76c0 remain unchanged. Independent custody source preparation
d7d8b9a9 is [qualified separately](2026-11-27-owner-runtime-current.md).

## Exact failure chain, not a provider diagnosis

The fresh04:39–04:40UTC check finds NL1 inactive/PID0 and NL2 failed/PID0. Earlier02:31
traffic success was historical. Both node boot IDs remain the same; this is not a reboot.

NL1 invocation b50a80b0768b44939d46483267bd594b/PID2011396 exits03:16:28UTC:
SEED_READ/SIGNAL_READ records WebSocket IO_TIMEOUT, context ACTIVE, carrier_closed=false,
returned_error, empty Unix signal and completed cleanup. Credential headroom4955s.
Application receipt SHA2564345d37557ae62cc0cdabf1528c6f6a319e916330207cb88d3e98e8b19c574f3;
matching systemd receipt cdcb128962437f93c4a13445906551fdbd1b074fc31ebcb41e98f526e1893d8c.
The preceding01:32 CONNECTION_RESET remains a different failed invocation, not this timeout.

Subsequent NL1 attempts record SUBSCRIBER_DISCONNECTED03:20:24, provider_timeout at
SEED_CREATE03:21:09, and seed_join_failed03:21:55. Separate03:24:17 and03:25:05 records
explicitly show SIGTERM/CANCELLED; those signals are not substituted for the03:16 cause.
NL2 journal retains TURN permission refresh failures followed by its03:16 exit and
automatic retries. It has no matching application fatal receipts in the inspected scope;
its initiating cause cannot be inferred from NL1's records. Provider blocking is unproven.

The current scheduled renewal scheduled-1795749826-f5ee70e0e85b504d has all three nodes
acquired/quiesced, equal PROMOTED reconciliation, commit_decided=true and state
RECOVERY_REQUIRED with first_cause SERVICE_ACTION_FAILED. Both NL ownership records
belong to that operation; their current committed credentials validate through07:24:19UTC.
An earlier startup receipt's04:39 expiry does not describe those current credentials.
Old start-intent records already exist, so blindly rerunning recover would refuse
START_ALREADY_ATTEMPTED and could re-fence readers. They are not deleted or edited.

RU independently shows severe I/O/memory pressure, including IO PSI some99.33/full87.15;
some bounded diagnostic reads time out. Later pressure drops substantially. This is an
observation, not proof of the underlying storage/provider/process cause. No apt operation,
MicroTrader service, paid-watch/deny policy or resource policy is changed.

## Controlled current-commit reconciliation

Own renewal/directory-sync timer holds prevent repeated failed invocations. Existing
directory-sync work is allowed to finish; no service is killed to obtain a quiet census.
The separately failed user monitor invocation b6878fa133984e859e6d02fe444cc0ea is retained;
only its timer receives an additional own hold. The independent healthy probe timer runs.

Under the actual coordinator operation lock, the current transaction, original cause,
commit decision and all three readbacks must exactly agree. Each NL then takes its node
lock, verifies the matching owner/reconciliation/services-before/retained start intent,
valid current authority/CRL/leaf/key binding and sufficient headroom, exact unchanged
70e6c0fc binary, disabled boot enablement and stopped state. A new private audit intent
authorizes one explicit start, never an automatic retry or an edited old ticket.

Each first invocation must remain active with NRestarts0 and produce a newly validated
directory. Loaded binary, protected profile bytes and original start intent must remain
unchanged. Only after both successes does the still-locked coordinator run its installed
normal recover path. It returns COMMITTED/receipt_written=true and retains original
first_cause SERVICE_ACTION_FAILED. No credential/authority/grant regeneration, rollback,
database restore, systemd reset-failed or enablement change is performed.

Fresh runtime:
- NL1 PID2215748, invocation3fdd38bd8b774689a27673b28af5f78f.
- NL2 PID2871488, invocation28f5a4f21ceb484aa455ddfc8f7eb83f.
- Both still active/running, NRestarts0 at05:05UTC; unchanged gateway sourcea597d2a/binary70e6c0fc.

Independent read-only checks subsequently verify all three completed ledgers, absent
owner records and every archived file against its manifest: RU9 files, NL1/NL2 eight
each. Both original start-intent byte hashes survive normal archival. These are
downstream terminal proofs for this exact recovery, not merely the controller's exit0.
They do not settle unrelated older collector/Docker/HTTP uncertainties.

The retained authorized FLEET_MESH_PROBE_1 identity is used without a new invitation,
normal-broker fallback or SSH tunnel. NL1 at04:55:49 and NL2 at04:57:08 both pass Family
authentication,4 concurrent HTTPS,3 DNS and expected node egress. Probe processes exit0
and identity bytes remain unchanged. These are bounded traffic proofs, not sustained
stability, a provider-root-cause fix or Android/phone E2E acceptance.

## Normal dependencies and history

Normal installed renewal invocation3b06012efba04a08a61e1a203bc01b6b completes0.
Directory-sync invocationd45758365cb4494c97eaa1cbd9e5cdcb completes0. Only own holds are
removed; both RU timers are enabled/active/waiting. Local monitor bounded recheck
5fedac54c6f54333bd629c6c0f75796a and later automatic645229cb902941deab8412ee993fc752
complete0; probe automaticb84ee23c5d6c483fb7101d3d9eb60825 completes0. Both user timers
are enabled/active/waiting. Normal subscription-notifications invocation
e93f17a587034031bf652f05547229f8 completes0 at04:57:15UTC.

At04:59UTC real panel login, overview/subscriptions/payments/two existing cards and
logout PASS. No synthetic messages or manual user-data changes are used. Observer8b
returns ACCEPTED_SUPPORT_READ_ONLY_NORMAL and independently preserves supportPID240065,
archive621009b8, authorityb0c470dc, NL1 generationb75ef2a2, cursor hash and support33 history.
No completed support Resume.run is executed. Console startup still requires its existing
support runtime-directory mount; automated reboot startup remains unqualified.

Exact original history metadata/bytes remain: root119 plus earlier41 plus11 later,
inventory3+12+6 plus earlier8 plus2 later, probe14 and support33. The additional counts
are separate observed partitions, not original UNKNOWN3, deletion or settlement. Strict
Gate.drain remains unchanged. No maintenance hold becomes a capture permit.

Private evidence is under `/mnt/data/fc-owner-next-20261127/mesh-outage-0440` and scoped
`/root/fc-owner-next-20261127-mesh-outage-0440` records on the authorized hosts. Bounded
reconciliation script SHA2564df554623132aafa4e863b42309640028279344a3e24579dcfe9f408a36a7634.
Initial read-only diagnostic import refusals and timeouts are retained; no mutation is
attributed to them. Raw profiles, state, private journals and recovery material stay out
of Git. Actual external KeePassXC copy/access remains a separate nonblocking custody item.

Remaining NEXT: qualified historical/external-dispatch fencing, including Docker and
receiver-side work, then common-cycle integration of the explicit new OWNER custody
policy. A fresh held RU/NL1/NL2/OWNER cycle must take a new stopped-support snapshot,
independently verify the kit and normal resume. None of that common capture has run;
e4eace1a remains history. Full OWNER/all-writer acceptance is NOT_PASS at this checkpoint.
