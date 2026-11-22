# 22 November 2026 — device OS and IP-geography coverage audit

## Scope and runtime provenance

The owner observes OS information on only two devices and no IP location. This is
a read-only diagnosis of the deployed metadata path, not authorization to enable
collection for users, change retention, deploy clients or restart RU. The separate
RU transport outage remains open; no recovery is performed in this task.

The running console image is
`sha256:5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da`.
Its metadata modules are not present in this checkout's main source tree. Relevant
source and delivery evidence are read from existing commit `3539ebe4`, without
switching branches, editing another worktree or inferring deployment from a commit.
Three actual container files match that commit byte-for-byte:

- `control/friends/geoip.py`:
  `265e8e3f2b8eb0ca06d8ee7231a1df823a90afd0465d1fa38e4f2042d0a0ee41`.
- `control/friends/technical_metadata.py`:
  `58f4d5decd865f95eeaa47f39b41bd907bda5569cda51afbcb351c672173cd3a`.
- `control_plane/apps/console/technical_metadata.py`:
  `41bf2f16f40bff38a6c5500a575a9f3b772366cd087f9c0e0d011825ce4d5110`.

The installed RU HTTP archive remains
`4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8`;
its GeoIP and canonical metadata members match the same two hashes above.

The external SSH collector source is inspected in that commit; it is not in the
console image. Attempting to hash that absent fourth file fails and is not counted
as a four-file match. No payload-bearing collector is invoked for this audit.

## OS: the panel is not dropping the existing profiles

At **19:17:20–21UTC**, read-only PostgreSQL and canonical SQLite queries show:

| Evidence | Result |
| --- | --- |
| Latest RU inventory | 69 device records, including4 revoked; not69 active physical devices |
| Metadata collector | `ok`, last sample19:16:15, age65s |
| Canonical and panel metadata rows | 3 each:2 enabled,1 revoked |
| Current profile/network/mobile/session/diagnostic groups | 2 of each in both stores |
| Android OS profiles | Android15/API35 and Android13/API33; both report beta126 |
| Profile ages in panel | 102s and2745s; neither has expired |
| Inventory records without a metadata row | 66 |
| Panel presentation labels | 2 available,1 revoked,26 unsupported,40 not received |

The Android sender introduced in126 has its own **default-OFF** switch, labelled
"Технические сведения для поддержки / Support technical information" in settings.
It is independent of prior support/diagnostic preferences and ordinary readiness
reports. With explicit consent, `Build.VERSION.RELEASE` and API level are sent in
the profile group. App/session/network changes trigger bounded uploads; an active
process also schedules a six-hour refresh. A background process that is not running
is not a guaranteed six-hour delivery agent. Latest observations expire separately
after7days; revocation clears payloads and retains only a minimal tombstone.

Only the two enabled rows have current OS payloads on the canonical server, matching
the panel count. One row explicitly records revocation. For the66 absent rows,
absence cannot distinguish never-enabled consent, an older/unsupported client,
inactivity or an undelivered report. Do not label all of them "consent denied".
Inventory app versions can be historical and are a separate observation source;
the UI's numeric126 threshold is not proof of current installed platform/version.
The profile schema and compact template expose Android fields, not universal
Windows/Linux OS collection. No desktop sender is established by this audit.

## GeoIP: currently limited to RU/AWG

The deployed enrichment function accepts only enabled metadata with a session
reported as `gateway-ru`, `AWG`, `CONNECTED`, received within180s. It then joins the
canonical AWG public-key binding to a fresh RU `fcopen31` handshake and endpoint.
The IP must be public and not a known VPN exit. It is used transiently with local
DB-IP City/ASN, not exported or saved as a raw address. HTTP ingress headers are
not used as a replacement because they may describe a VPN/relay rather than the
device's access network. No NL, TCP or MESH peer enrichment is implemented here.

The two current session observations are **NL2/AWG/CONNECTED** (102s old) and
**UNKNOWN/NONE/DISCONNECTED** (2745s old). Neither qualifies. Both geographic
records explicitly say `no_suitable_direct_observation`, with no country/city/ASN;
the revoked row has no geographic payload. This exclusion happens before lookup.

Canonical `/opt/apps/family_connect/geoip/current.json` exists, declares2026-11,
and both City/ASN files exist. Declared build age is21.68days, below the45-day
staleness limit. This lightweight check does not rehash large databases or claim
full structural validation. Their absence is not the observed failure reason.

The compact device list renders a location line only when a city exists, hiding
unavailable reasons there. The full device card contains the reason and source.
Previously valid geography can be retained, age-labelled, for up to7days within
the same consent epoch; no such retained location exists for these current rows.
Restoring RU alone would not add geography to NL/TCP/MESH sessions.

## Follow-up boundaries and conservation

Potential improvements, not implemented by this audit:

1. Explain absent/unsupported/revoked/stale data in the list instead of blank fields.
2. Verify compatible Android version and voluntary switch state on a chosen device;
   do not automatically enable consent or equate an absent report with refusal.
3. Extend authenticated, consent-bound AWG peer observations to NL1/NL2, retaining
   identity binding, freshness, privacy and VPN-exit exclusions.
4. Qualify Windows/Linux profiles and trustworthy TCP/MESH observation sources
   separately; never substitute gateway geography for device location.

Raw IPs, device identifiers, model names, keys and user messages are not emitted.
Only bounded aggregate/version/session diagnostics are retained privately under
ignored `state-client-build/metadata-audit-20261122/`. Queries enforce read-only
transactions; no collector import, consent change or metadata-pruning call runs.
No runtime/client version, catalog, database schema or public release changes.
No deployment/rollback is needed. Source tests are not rerun for a read-only audit;
documentation links/digests/whitespace and staged-source safety are checked.

Pre-existing dirty changes are preserved. Only this report and new STATUS/PLAN
entries are staged; ordinary push outcome is reported separately. Existing branch
divergence is not resolved with a force push, reset or unrelated merge.
