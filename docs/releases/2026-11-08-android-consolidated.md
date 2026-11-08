# ANDROID-CONSOLIDATED-CANDIDATE — beta121

## Scope and immutable predecessors

Integration starts from main `931023334ebf7419d0e7f2e976d99409b09b6cb5` and merges
cold `d3cf49c76ca9e2ebd45f69a9c59f524e0f6305ec` in a separate worktree. PR1–9,
the installed paid108/119 policy and RU recovery remain intact. Remote branches,
open PRs, tags and local worktrees were checked before reserving **code121 /
0.1.18-beta121**; no121 allocation was found. This does not make121 eligible for
new paid operations. Existing entitlement and own authenticated status are separate.

Owner beta120 remains installed, with its exact source55525859 and APK
`24a5338a98cfb7e67537c27085356d7932e500c916bf93e3f169b3b9c79517ea`.
Its locator is expired, subscription UI119 is absent, WARM WiFi is PASS and
COLD_ENTRY is NOT_ACCEPTED. The corrected frozen G4 result remains
FULL_CORE_PATH_PASS/exit0, not physical cold or whitelist acceptance.
No phone installation, entry start, server rollout, paid write, public release or
updater change is part of this integration.

## Integrated contracts

- Current main's personal challenge/proof subscription request, strict schema1
  decoder, encrypted projection, revisions, event pairing, deduplication and
  owner/cancellation fences remain. HTTP200 and snapshots without an event never
  mean payment received. Cached/unavailable/unsupported/identity rejection remain
  distinct. Opening subscription or Refresh fetches the latest corresponding event;
  ordinary launch may drain already-saved notices, not fetch payments in background.
- Cold readiness is added to the same FriendsAccessAndroid without routing
  subscription traffic over the cold carrier. Ordinary HTTPS/cache/RNS behavior,
  TLS refusal, recipient/gateway binding, finite expiry and replay protections stay.
  Cold is attempted only for the permitted readiness challenge after eligible
  direct/relay failure and with no usable cache. Cancellation closes the native
  carrier and a changed owner cannot commit material.
- UI60/thin layout, picker, preferences, strings and subscription screen from main
  are retained. Source-review hashes for119 and120 are historical: one explicit
  consolidated FriendsAccessAndroid adaptation records their composition, rather
  than replacing the old references or calculating expectations at test time.
- Native inputs are built from the new integrated tree. Neither55525859 nor the
  old120 native hash is assigned to the new APK. The release CI emits exact APK,
  native source inventory and corresponding-source receipts.

## Candidate gates and evidence contract

The ordinary PR runs mandatory hosted gates, including native race/contracts,
Android JVM/lint, API27/API35 transport runtime and unsigned ARM64 packaging. New
offline API35 fixtures perform119→121 and120→121 in-place version transitions with
the unchanged historical vault/envelope formats, real Android Keystore, persistent
identity/profile/preferences and subscription cache. These are explicitly versioned
**format fixtures**, not installation of historical production-signed APKs.119 has a
confirmed snapshot without an event;120 has no subscription cache. Process stop,
UID/first-install preservation and reopened encrypted state are checked. Fixtures
cannot contact production and run only on a disposable hosted emulator.

Visual evidence includes the existing main/picker/error renderings and actual121
subscription dialogs for both migrated states. Downloaded images must be inspected;
XML/JVM success alone is not visual acceptance. Final PASS/FAIL, CI URLs, exact
artifact/source SHA and inventory belong in the final PR receipt, without a cosmetic
post-CI source revision. The resulting ARM64 Friends artifact is an **unsigned
prebuild without a locator**, not an installed/signed release or ready cold handoff.

## Corrected operator preparation

The two owner-operation errors were operator preparation errors, not evidence of
an APK crash: a reformatted verification receipt was selected, then applicationId
was incorrectly used as Java namespace. Both receive explicit negative regressions.

1. Obtain the original `restricted-release/verification.json` from the accepted CI
   archive. Independently retain run/job/artifact IDs, archive SHA, source SHA,
   original receipt SHA, APK/native/anchor SHA. A reformatted derivative is rejected
   even if its JSON values match. Do not create a fresh short-lived entry yet.
2. Use the separately reviewed121 qualification descriptor and its independently
   pinned SHA with `scripts/cold_field_preflight.py preflight`. It verifies the
   immutable prebuild/receipt/source/native/anchor, pinned locator verifier,
   release tools and manifest. Unlock/check the existing signing mechanism and
   confirm device availability before the private start hook. No replacement key.
3. The private operation must use `run_field(args, start, operation, stop)` from
   that module: complete preflight precedes `start`; its `finally` always invokes
   cleanup, including a partially failed start. Rehearsal uses synthetic callbacks,
   not a production entry. The historical120 descriptor remains unchanged/default.
4. Resolve `launchable-activity` from the inspected APK, then compare installed
   `cmd package resolve-activity --brief --components` output with
   `check-launcher`. The Friends component is currently
   `com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity`.
   Never construct `applicationId/.FriendsActivity`.
5. After signing/install and immediately before the **single** Connect, obtain a
   fresh status from that entry: active/running, PID>0, original InvocationID,
   observed_at≤5s, stopped=false. Bind the ready observation to the same invocation,
   verify ready≤90s, matching locator SHA/expiry, and at least200s remaining.
   `check-entry --status STATUS.json --ready READY.json --locator VERIFIED.json
   --invocation ORIGINAL_ID` refuses stale, stopped, restarted or short-window entry.
   A successful ready before installation is not a substitute. On refusal, cleanup;
   no implicit restart, TTL extension, new locator or repeated Connect.

For121, the external approved qualification JSON has state
`ANDROID_RELEASE_CI_ACCEPTED`, exact version121/name/package/signer, head_sha,
run_id/android_job_id/artifact_id, and SHA256 fields artifact_sha256,
verification_sha256, apk_sha256, native_sha256, anchor_sha256, verifier_sha256.
It is selected only with BOTH `--qualification FILE` and
`--qualification-sha256 INDEPENDENT_PIN` on preflight/finalizer. The final receipt
pins its exact bytes after successful CI; pending templates are not accepted.
No auto-discovery of the latest APK, self-derived acceptance pin or version≥120 rule.
The signer remains `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.

## Physical cold boundary and stop

Physical COLD remains NOT_RUN for121. A later separately selected operation needs:
no usable cache (do not delete owner's cache to manufacture this condition), actual
unavailability of the preceding direct service paths without a TLS/trust bypass,
an available cold carrier, a fresh signed locator and live same-invocation entry,
and correlated evidence that readiness materials arrived through that carrier.
Ordinary WiFi success and Android's activity “COLD launch” are not this evidence.
Russian whitelist acceptance is separate. Installation, paid eligibility expansion,
future field attempts and publication are not automatically started after this PR.
