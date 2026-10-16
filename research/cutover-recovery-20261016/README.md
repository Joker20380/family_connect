# Android cutover recovery — isolated local candidate

See [the report](../../docs/releases/2026-10-16-cutover-recovery-local-1.md).
This patch is relative to the retained **UI60-4 cumulative source**, inventory
`e90893aee5fdc04aae1cacd296d5291ca8a743350de42334b290f08504c48fce`, not the
publication branch's product files. Do not apply it to root main or the independent
fast-retransmit candidate and call that the tested build.

- `candidate.patch`: six Java product changes, one new test and private versionName.
- `boundary.json`: exact per-file before/after hashes and patch round-trip proof.
- `cumulative-source.json`: full cumulative delta inventory relative to retained
  `f5240994869826c6a28f59e58e38256c688cf6eb`; the digest is not a Git commit.
- `build-receipt.json`: fixed JVM suite outcomes, unsigned APK/native identities.
- `artifact-check.json`: actual package/API/ABI, alignment, unsigned status and12
  unchanged shared libraries, compared with the retained UI60-4 unsigned artifact.
- `validation-history.json`: stopped batches and the corrected synthetic-fixture
  failure, distinguished from the final97+14 PASS executions.
- `thermal.json`: final batch temperature/time/exit; no emulator.
- `build_and_check.py`, `bounded_check.py`, `seal.py`, `check_artifact.py`:
  retained-workspace runners; run `check_artifact.py` after the successful batch.

To reproduce, first materialize a private isolated copy at
`state-client-build/cutover-recovery-1/source` from the verified retained UI60-4
source, retaining its source-base Git metadata. Check every entry of its recorded
inventory, apply `candidate.patch`, and copy these runners into the parent private
task directory. Existing retained Android SDK/JDK/Gradle/native inputs named by the
runner are required; absence is a blocker, not permission to rebuild a guessed
baseline or disable provenance. Runners do not fetch device/server credentials.

Run `seal.py` to verify that only the listed files changed and that the patch applies
cleanly. Run `bounded_check.py` under the accepted half-core user scope:

```sh
systemd-run --user --scope --unit=fc-cutover-recovery-check \
  -p CPUQuota=50% -p MemoryMax=3G -p TasksMax=160 \
  python3 state-client-build/cutover-recovery-1/bounded_check.py
```

Start below75°C; the runner stops its process group at85°C or1500s. This is a build
and correctness check, not a throughput measurement. Gradle uses its offline mode
and retained dependencies, one worker and the exact accepted native library. Its
ordinary source/native provenance guards remain active. One full assemble/targeted
JVM invocation is followed by one fixed repeat of the new recovery tests, not an
unbounded retry loop. Tests use synthetic data only; no provider, phone, ADB/SSH,
room, network fault, system VPN or maintenance operation is performed.

Synthetic tests prove Java policy transitions, cache selection and evidence
classification. They do not prove live handset recovery, maintenance-free calls,
mobile throughput, a ten-minute timer, or that HELLO waits can safely be retried.

## Next device gate

The owner requested installation **after checks**. Do not label the recovery-only
artifact as the combined throughput build. Complete the separate fast-retransmit
stack/mixed-peer checks and build the intended exact combined artifact before that
installation. Preserve the previous signed APK, verify actual installed package/
signer/code and VPN OFF, then use the existing previous-key signing/replace-install
workflow. No downgrade bypass, data clearing or automatic CONNECT. This research
directory does not authorize gateway deployment or manufacture a maintenance outage.
