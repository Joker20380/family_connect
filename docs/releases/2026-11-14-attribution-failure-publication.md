# Attribution fixture failure publication race

Selected CI-only correction over PR36/main07d825cb356460289f647327b66efaba65dcfdad.
Original dirty checkout preserved; existing clean worktree fast-forwarded to remote
main. No production/RU access, new probes, architecture, persistence or user data
change. PR36 NO_GO_PREFLIGHT and RU CAUSE_OPEN remain unchanged.

## Original evidence (not erased by an intervening PASS)

| Source | Linux control run / job | Full step and later steps |
| --- | --- | --- |
|ea19c1d751cfb330ad1f9f503e650cdee27151c3|43646201975 /132604440606|FAIL standard context; later GTK/package steps skipped|
|07d825cb356460289f647327b66efaba65dcfdad|43646417300 /132605128651|same failure; later GTK/package steps skipped|
|e4089cd203a357827872eae35d81f738f1e41185|43646384184 /132605100860|PASS full step and all later GTK/render/build/extracted recovery steps|

Both failures name only
`tests/test_ru_attribution_recorder.py::test_real_pipe_drains_sigint_tail_and_preserves_first_failure`:
`invalid_failure` instead of `first_failure`. Standard/root/snapshot314 returncodes
are1/0/0; coverage is false, outer command exits1 (not an external timeout).
The successful documentation-head run has0/0/0 and coverage PASS. Executable fixture
and reader are identical across these three SHAs; a successful interleaving does
not invalidate the two failures.

Downloaded `control-full-pytest` artifacts retained privately under
`/mnt/data/fc-attribution-publication-20261114` with these verified ZIP hashes:

- source artifact14134647980: `2a8747234fb6abddf667dedfc04a682054ad537f6319b6de30ef3b833807414d`
- main artifact14133898405: `62397b045015dd6fc89296eb09716c1fa2044bf683cedc7b9f5ee8b877e3f474`
- documentation artifact14134811094: `bde54f44909338234f37390b349efec2b582878eaffa28cf4c326f8ea818a8f0`

Historical logs do not retain the exact bytes at the failed read. They cannot
distinguish an empty file from a partial JSON; both boundaries are reproduced below.

## Deterministic cause and minimal repair

The positive subprocess fixture called `path.write_text(json.dumps(...))` on the
final watched path. Opening with `w` exposes an empty inode before the buffer is
written/closed. Recorder checks existence independently, opens/read/parses once,
then irreversibly stops with `invalid_failure` on ValueError/OSError. A normal SIGINT
tail/EOF can still be drained; that does not turn an invalid failure into success.

New tests coordinate a real separate publisher using stdin/stdout handshakes:
create/flush empty or partial content → acknowledge prepared → block; reader
observes the defined boundary before the publisher is allowed to finish. No sleep
selects the interleaving and no repeated-until-green run is used. Four cases:

- final path + empty/partial prefix: the actual reader rejects exactly once;
  publisher subsequently finishes valid JSON, but result stays invalid/incomplete;
- temporary path + empty/partial prefix: recorder executes its no-final-path branch
  while preparation is blocked; only after close+replace may it read the complete
  failure and report first_failure. Pending preparation is not publication.

A separate permanently corrupt final file remains invalid after successful drain;
exactly one read, no retry, no success relaxation. Handshakes/child cleanup are bounded
at2s, recorder duration5s and existing stop limit8s, without increasing any limit.

Repair is in **positive synthetic producers**, not reader:

- pipe-tail fixture writes sibling pending file, closes it, then replaces final;
- v2 BEGIN/attached readiness reproduction publishes its successful failure the same
  way; these modes are positive failure-file producers even though BEGIN deliberately
  demonstrates an incorrect probe-readiness barrier;
- main v2 and legacy lab already use pending+replace and remain unchanged;
- synchronous test callbacks and files completed before reader startup cannot expose
  a concurrent write window and remain unchanged; intentionally invalid files remain
  invalid controls.

Original102-event SIGINT tail assertion is preserved, with separate EOF, END,
child exit0, bounded stop and non-forced checks. First receipt equals the unchanged
first file after a distinct second-failure publication. No xfail/skip, assertion
weakening, polling retries, timeout, launcher, UID/Python context, fixture pin or
lockfile changes. `ru_attribution_recorder.py` is byte-unchanged.

## Explicit production limitation

Repository `control/friends/transport_gateway.py:report_failure` currently creates
the final transport-failure.json with O_CREAT|O_EXCL, then json.dump/flush/fsync.
O_EXCL preserves first-writer ownership but DOES NOT publish a complete JSON
atomically. The isolated fixture repair is therefore NOT a proof that this reader
is ready to consume that production file concurrently. A separately qualified
producer/reader completion contract is needed before future deployment, retaining
first-failure ownership/durability and protective-stop bounds. Nothing in this task
changes that producer or an installed runtime; no production readiness claim.

## Verification / integration

100 scoped recorder/contract/compact/observer/analysis/production-diagnostic tests
PASS in the existing locked environment; collection6269 PASS. This includes all
five new boundary/corruption cases. Existing kernel scenarios are NOT rerun: this
is a filesystem fixture correction, not transport Gates A–C or a new RU collection.
Source/doc whitespace and privacy guard checked before commit.

Executable source: **a5067ae24599023e6d3f2d14e6e8b95d30b5b810**. Hosted PR37 checkout
is the test merge **f3b38e51d1e770aef75fa7db02bb6f83357c2a20**; both Git trees are
**244092c7240acbf58c600e98793b4e45a7a0d17a**, verified by fetching refs/pull/37/merge.
These are completed results, not internal PASS markers while a command still runs:

| Check | Run / job | Completed result |
| --- | --- | --- |
|phase0/tests|43648982308 /132612972198|SUCCESS; full pytest, then cargo test --locked actually executed successfully|
|Linux control|43648982300 /132612972299|SUCCESS entire workflow; full pytest, system GTK, render/interaction, paired/six-file build, extracted artifacts outside checkout, extracted GTK recovery/digest and uploads|
|Readiness wire contract|43648982296 /132612971919|SUCCESS|
|phase0/failover|43648982308 /132612972043|SUCCESS, observed23:04UTC; actual failover/auth/offline/revocation steps all executed successfully after Docker build|

Both downloaded full-suite artifacts prove the same complete collection:6269,
standard5913/root258/snapshot31498, all returncodes0, no failure/error IDs, coverage
PASS. Standard execution:5637 passed/276 existing skips/356 context deselections;
root258 passed, snapshot31498 passed. No new skip or omitted test. Launcher, wrapper
and outer pipeline ended; command/tee/console all0, completed=true. Standard duration
636.24s in phase0 and498.92s in control; these are execution measurements, not timeout
changes. Artifact ZIP SHA256 verified locally against the API digests:

- phase0-full-pytest14136055505: `c58c7e2f66ef546b89073f56a6a8d682ef73eae3d5dd6066e200f6547117fd67`
- control-full-pytest14135328522: `8534728f8c5ae6771f7f42da6726c0c77afc8c3514ac12b634a37ca0b771a284`

Private logs/receipts remain under the evidence directory above. Subsequent report
changes are documentation-only and do not substitute another executable source for
these checks. The source failover job was allowed to finish before the documentation
push (not cancelled/restarted). All three selected-source workflows finished
successfully. CI jobs for other heads are not inferred successful from this source.

[PR37](https://github.com/Joker20380/family_connect/pull/37) uses ordinary merge, not
force or bypass. Review5907527890 is **own scoped review**, not independent approval.
Rulesets list is empty; this task's explicitly required hosted gates nevertheless
finished before integration. Remote branch source SHA was verified after push;
final documentation-head and merged-main receipts are recorded in the PR integration
comment to avoid a self-referential commit hash. The unrelated dirty original checkout
is preserved. No deployment, new RU observation or architecture gate is authorized.
