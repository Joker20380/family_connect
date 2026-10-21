# Owner support automation (98 → 99)

This is not another speed matrix. The exact installed97 capsule is the parent of
98; the sealed98 capsule is the parent of99. Repository main is older and is not
the APK source of truth. Do not build main and label it the installed candidate.
No production transport defaults, tester identities, public catalog or invitation
links change. Full readback/results are in
`docs/releases/2026-10-21-owner-support-automation.md`.

## Android and operator path

- `prepare.py`, `mux_reasons.py`, `build.py`, `sign.py`, `install.py`: historical98
  creation on installed97. `android97-to98.patch` freezes this delta. The original
  new Java files are read from that patch, not mutable current uploader sources.
- `candidate99.py prepare|build|sign|install`: exact98→99 upload timing correction.
  `android98-to99.patch` changes five Android files only. Native and all12 bundled
  libraries are byte-identical to98. No RS/Mux/security-policy changes.
- Use `sign --check-only` before signing; actual signing uses the existing protected
  vault dialog. Never supply passwords in CLI arguments/environment/logs.
- Installation requires `install --allow-owner-vpn-interruption`, preserves signer,
  package and UID and uses only `adb install -r`. Intent/receipt guards prevent a
  blind repeat. An APK replacement ends the VPN and the process-local USB consent.
- USB support: app-local explicit consent, one hour/process lifetime, UID2000+DUMP.
  No touch injection, root or network command API. After a package update the owner
  must enable it once again. Online consent is a separate persistent7-day opt-in.

```sh
python3 scripts/owner_android_support.py --serial 31ce63ba status
python3 scripts/owner_android_support.py --serial 31ce63ba snapshot --output /tmp/support-before.json
python3 scripts/owner_android_support.py --serial 31ce63ba disconnect
# Observe OFF before profile/connect. Do not retry UNKNOWN or change a live profile.
python3 scripts/owner_android_support.py --serial 31ce63ba profile --profile P0
python3 scripts/owner_android_support.py --serial 31ce63ba connect
python3 scripts/owner_android_support.py --serial 31ce63ba collect --seconds 60 --interval 5 --output /tmp/support-capture
```

The gateway's owner-targeted profile is separate; existing speed policy tooling
must prepare it for an authorized transition. Never infer both-end effective RS
or Mux from an Android selection. `verify.py` correlates a complete phone snapshot
with a fresh gateway readback, bounded exact-invocation journals, identity hashes
and the authenticated online report. Select a journal interval containing session
startup; missing entries are not zero counters. Its outputs are private evidence.
For status including upload state, the provider's status Bundle exposes both fields;
the CLI helper's short status prints only the connection result.

## Online contract and limits

`POST /friends/device/diagnostics` is for authenticated uploads, not remote control
or public diagnostic downloads. Challenge purpose binds SHA256 of the exact report
string; the server derives Support ID from the existing identity. Only fixed enums,
session tags and bounded counters are accepted. Latest≤4KiB/report/device, ≤1 changed
report/minute,5000 devices,7-day retention. USB exports are fuller but remain local.
Read online data using `scripts/read_online_diagnostics.py` in the existing service
venv with the installed HTTP artifact on its Python path, not bare server Python.

99 schedules the next upload ≥60s after successful completion, not request start;
failure cooldown stays5min. One worker/no backlog,15s request budget, no VPN bypass.
The new bounded states distinguish RATE_LIMITED/AUTH_REJECTED/TIMEOUT/UNAVAILABLE.
The locally reproduced timing defect does not prove every98 UNAVAILABLE was429.
Native statistics ticks trigger updates; this is not an OS-level all-day collector
when the process is killed or native statistics are absent. Missing data is unknown.

Server schema supports Android/Linux/Windows, but desktop uploaders and wider
Android delivery are not shipped by this fixture. Every client requires consent;
the owner's permission is not authorization to enable telemetry for other people.

## Verification

Pinned Android build runs193 tests for98 and198 for99, including scheduling gates.
Python tests use `control/requirements.lock` and `device_identity/requirements.lock`:

```sh
python -m pytest -q tests/test_online_diagnostics.py tests/test_owner_android_support.py tests/test_support_ids.py tests/test_support_automation_fixture.py
```

No protocol errors are suppressed. New reason counters identify the incrementing
branch, not frame provenance or application damage. Keep historical speed failures
and the unknown cause of17 errors; do not turn a reconnect or upload into speed or
long-term recovery acceptance. Disable support in the app to return to normal
operation without APK downgrade/data clearing. Shared HTTP rollback is documented
in the report and does not restart media gateways or touch renewal/security state.
