# Open test distribution

Explicit user authorization, 2026-09-14: anyone receiving the APK may use both
countries without an account, payment or expiry. This is separate from per-device
managed Reticulum acceptance; its gates remain open in STATUS/PLAN.

Android `friends` build type: `com.familyconnect.app.friends`, non-debuggable,
`FriendsActivity`, shared existing TCP engine. Only a bounded HTTPS-fetched catalog
signed with the offline root under `family-connect/open-test/v1\0` is accepted.
The catalog has a monotonic sequence, two strict TCP profiles, and deliberately no
lease. An already verified cached catalog works when refresh is unavailable.
No user identity, payment check, invitation or managed journal is created. Test
access credentials are intentionally public; server REALITY private keys remain
private. Never substitute personal device profiles. Keep generated files outside
Git, CI and command output, under `state-enroll/friends-pilot/`.

Dedicated services on the two authorized hosts:

- RU label:185.251.89.19:8446, NL label:186.246.45.246:443.
- `/opt/apps/family_connect/friends-tcp/`, `family-connect-friends-tcp.service`.
- Xray26.3.27/d2758a0, binary SHA256
  `4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940`.
- Separate REALITY keys and shared test credentials for each gateway; no log of traffic.
- Existing API, WG, AWG, TCP443 and Android TCP8444 retained. Outbound private/local
  address ranges blocked for the open service.

`install-tcp.py` reads private configuration on stdin and refuses overwriting an
existing install; upload the verified binary first. `publish-catalog.py` only
publishes the first already-signed catalog at the existing HTTPS ingress and
retains a before-friends nginx config. Sign offline with
`scripts/sign_open_test_catalog.py`; never send the signing key to a server.

Before distribution, require platform CI, APK signature/version/ABI checks, and
real Android RU→NL→RU traffic tests. Sign the accepted APK with the persistent
local beta key. Never overwrite an already distributed version with new binaries.

Rollback: stop only `family-connect-friends-tcp.service` on the affected host;
this deliberately disables that country's open test, so it is not routine test
cleanup. Preserve configs and profiles for recovery. Restore nginx's
`.before-friends` backup only after reviewing any later changes; test config and
reload. Keep registration/TLS renewal working. Do not remove existing Pilot state.
For clients, publish a higher version/code, without uninstalling user data.
