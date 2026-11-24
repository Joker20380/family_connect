# 24 November 2026 — installed schema and unit census, no live barrier

## Scope and result

Continuation of the owner's selected **all HA-02 gates**, after source9034163d's
isolated replication PASS. This is actual read-only observation, not a deployment,
schema migration, coherent snapshot, writer fence or independent recovery PASS.
HA-02 remains IN_PROGRESS. Production still depends on RU.

Pinned SSH to RU185.251.89.19, NL1 185.10.158.212 and NL2 185.10.158.196,
**02:51:37–02:51:39UTC**. NL2 authorization is retained in its
[host runbook](2026-11-02-second-nl-ordinary.md#authorization-and-trust).
Default existing SSH authentication and strict existing host pins; no host-key scan,
password disclosure, retired/excluded host or neighbouring service operation.
Collector streamed to existing Python with `-I -B`; nothing installed.

## Schema evidence

| Store | User tables | Exact definitions SHA256 | Result |
| --- | --- | --- | --- |
| Registry |27|`2bf709c6c989593d09b486c7cd391ede06f3d5d6917de2bfb300f09cfb3bc37e`|22 supported tables unchanged; five handoff tables additional|
| Metadata |1|`b6c803d4e87e752cdf30113ef15f93caed776cfdbe26e6c3919d7effd4f0d189`|Exact v1|
| Diagnostics |1|`2b9a0d9173d7ac27ae61aedeb00ad11be4c771b44b63f88f241e2c6a47755194`|Exact v1|
| Notices |5|`35a9899330dd08943ffc9349f0f9eb6f7cb3fcae80b75e771ea580e52eedb72b`|Exact v1|

All29 v1 application tables and their existing indexes/triggers match. The registry
has22 additional objects: five tables plus17 indexes/triggers. Their definitions
exactly match [successor_owner_handoff.py](../../tests/fixtures/mesh_perf3b/successor_owner_handoff.py),
pinned with its source hash in [sqlite-handoff-v2.json](../../deploy/control-ha/sqlite-handoff-v2.json).
Tables: `restricted_owner_handoff`, `_operations`, `_current`, `_security`, `_schema`.
This is installed authority/history/security-floor state, not disposable test data.
No user row, default literal, identity, key or profile was exported by this census.

The strict v1 importer remains unchanged and correctly refuses the extra objects.
The new comparison says `schema_coverage=true`, **`import_ready=false`**,
`all_writers_qualified=false`, `activation=FORBIDDEN`. It does not authorize stripping
the extra tables or accepting arbitrary schema differences. Next import work must
preserve terminal history, current/predecessor generation and per-device security floors.

The selected HTTP process still points to accepted archive4e2df679 and the expected
default Friends store root. Archive SHA, source entrypoint AST, command binding and
stable MainPID were checked read-only; this does not attest already-loaded Python bytes.
NL1/NL2 have none of these four default stores; that is not proof they have no other state.

## Writer and health evidence

32/9/5 Family Connect unit names observed on RU/NL1/NL2 from both installed and loaded
lists.24/9/5 unit observations retained; eight old RU pressure-probe/qualification units
refused the observer's source/fragment scope and remain explicitly unclassified.
Unit state, command/environment hashes, entrypoint/archive and fragment hashes remain
private. Presence or inactivity does not establish a disabled dispatcher or stopped writer.

RU HTTP is active. At the final sample, RU `family-connect-friends-awg.service`
reports failed/timeout, `family-connect-paid-reconcile.service` failed/exit-code and
`family-connect-product-cert-renew.service` failed/timeout. Their timer state does not
erase the failures. Earlier sampling also saw paid-watch activating; the final sample
saw directory-sync activating. No sampled NL unit reported failed/activating. These are
point observations, **not end-to-end transport or recovery qualification**, and no repair
was attempted as part of a schema census.

Cron/forced commands, panel containers/operator queues, gateway/READY publishers and
offline administrative writers are not fully inventoried. No census result is a live
capture permit. The [writer/barrier requirements](../control-ha-files.md#writer-freeze-and-activation-checklist)
still require complete coverage, bounded interruption, preserved watchdog enforcement,
prestate and tested abort/recovery. Unhealthy or unknown prestate is not silently normalized.

## Implementation and checks

[Collector](../../scripts/control_ha_installed_census.py) selects four explicit default
store names rather than recursively treating backup DBs as live stores. Initial broad
discovery hit its database-count limit and stopped; it was not made permissive.
SQL reads only schema/column metadata, via URI `mode=ro`, query-only/trusted-schema-off,
bounded objects/columns/values, VM deadline and a read transaction. Existing WAL sidecars
are required; unsafe sidecars refuse rather than being initialized. Schema hashes cover
the full DDL read on-host, while exported SQL/default literals are hashed.
No common cross-store snapshot is claimed; SQLite locks/access times/SSH audit entries
are observational side effects, not a zero-side-effect guarantee or writer fence.

Only fixed read-only systemctl verbs and Family Connect unit names are accepted.
Command/environment contents are never returned. Unsafe/missing source/fragment reads
are retained as refusals rather than acceptance; store and unit errors remain explicit.
The pin is observation-only, not SQL supplied by an untrusted census for execution.

**28 tests PASS,0failed,0skipped** in the locked control/identity/PG environment:

```sh
python -m pytest -q tests/test_control_ha_installed_census.py
```

Coverage includes row/default privacy, actual WAL schema visibility, missing/unsafe
sidecar refusal, file/symlink/hardlink/object bounds, backup exclusion, absent stores,
read-only systemctl guard, loaded/installed unit coverage, secret argument suppression,
failed source retention, pinned migration equivalence, unknown/changed/partial schema
and explicit refusal to equate recognition with import/writer acceptance.

Private evidence: `/tmp/fc-control-ha-20261124/installed-census/`; final three host
observations and schema audit under `final/`, runtime binding and test log alongside.
Collector SHA256: `e60c4ab3081202761625579f59e134076f6e3f58dc7b41379806cda8211479da`.
Raw evidence, any private paths and state remain outside Git.

## Rollback and remaining gates

No service was stopped/restarted, no DB/config changed, no release or deployment.
Console5ce82415, HTTP4e2df679, NL GeoIP22November, Android126/catalog9 and8/12/120s/
all-three-node ACK remain unchanged. There is no live mutation to roll back. Discard a
failed observational receipt and repeat after investigation; never restore old authority
or floor files to reconcile a hash. A source rollback must be an ordinary reviewed revert.

Remaining HA-02: explicit handoff-preserving import/recovery; complete writer census
and qualified coherent capture; actual-current authorization/journal custody; independent
full recovery with all external secrets/configs/receiver floors. No HA-03..05 work or
production PostgreSQL/Patroni cutover is selected by this checkpoint.

## Writer discovery follow-up 03:20UTC

Following closed-handoff retention source63ecb859, the same read-only census now accepts
only the **exact requested Family Connect name** under `/run/systemd/transient/` as an
additional fragment location. It does not authorize arbitrary transient units, start old
probes or weaken symlink/size checks. The earlier eight refusals were transient fragments,
not missing/unsafe source data or masked units. All eight have main/control PID0 at the
sample; six report active/exited and two failed. This does not prove no escaped/manual
process or no future restart; it is not a process fence.

Final pinned SSH03:20:25–03:20:28UTC: **32/9/5 unit observations,0 refusals**. Source SHA256
`9663e56436797a980bcaa6c5cc8a793077829b0b17ef54f7d24948abb67ca67c`.
This records the actual probe bytes; the subsequently tested source-only guard also
rejects parent (`..`) path segments without changing these observational projections.
Root authorized-key lines are read with bounded no-follow checks, never exported.
Literal Family Connect root matches yield1/3/2 command candidates and2/1/1 other
noncomment lines. Only digests/counts are returned; this is not complete OpenSSH-option
parsing or proof that an unmatched entry cannot write. Root crontabs are absent on all
three hosts; system cron and other accounts remain unobserved. Never interpret these
bounded candidate counts as a complete writer allowlist.

The historical panel runbook describes the **OWNER workstation**, not a RU container.
An initial exact-name RU probe refused; it was not treated as absence of panel authority.
The owner-local observation uses a separate `--panel-only` mode and checks exact names,
Compose project label and immutable image IDs for only these three existing containers:

| Container | Image SHA256 | Observed state |
| --- | --- | --- |
| console |`5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a`|running/healthy|
| postgres |`18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`|running/healthy|
| system_publisher |`50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab`|running/healthy|

Only read-only Docker inspect runs. Environment/command/source-mount values are hashed;
only known standard destination roles are retained. No Docker exec, restart, compose up,
volume change, queue export or neighbouring container operation. Health flags are not
an end-to-end delivery/recovery test. The publisher and panel state must be included in
operator/queue recovery planning rather than omitted because the authority DB is on RU.

**39 focused census tests PASS,0failed,0skipped**: prior28 plus parent-path traversal refusal, exact transient scope,
project/name/image mismatch refusal, secret-suppressing container projection, bounded
literal dispatcher scan and absent-vs-failed cron distinction. Existing PG/import gates
are not rerun for this observational-only change; their separate receipts remain valid
for their respective source checkpoints. Private evidence is in `writers-final/`,
`owner-panel.json`, `pressure-mask.json`, `dispatcher-tests.log` under the original census
evidence directory. Earlier failed/partial observations remain retained.

Remaining writer gate: complete system/account/forced-command and queue/dispatcher
classification, independent publisher ownership, administrative quiescence and a
qualified bounded coherent capture/abort plan. `all_writers_qualified=false` remains
mandatory. No live service mutation, new signer, current-state permit or version change.
