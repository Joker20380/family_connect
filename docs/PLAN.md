# Working plan / Рабочий план

Updated 2026-09-23. Use [STATUS](STATUS.md) for verified versions.

1. Refresh public versions and native screenshots for beta35 distribution / beta38 testing; see [publication record](releases/2026-09-23-public-client-status.ru.md). Earlier product documentation published to main (`9c4114b`); both languages, links, images
   and Mermaid verified. Remaining metadata task: update About/topics when owner API
   authentication is available. Do not choose a license implicitly.
2. Reconcile and publish the current Android/messenger source checkpoint separately.
   Preserve local work, verify dependencies and release receipts; documentation publication
   does not rebuild or replace the working Android APK.
3. Continue [Linux/Windows modernization](desktop-modernization.ru.md): signed Friends
   profiles, sequence floors, AWG 3.1 compatibility, broker apply/recovery, then UI,
   invitations and messenger. Identity storage checks passed; no new desktop release yet.
4. Verify real Linux/Windows installation and networking and cross-platform messaging.
   A physical Windows computer is not currently available for acceptance. Preserve the six-file Linux updater
   contract; immutable releases and offline signing only after platform gates.
5. Finish messenger offline/restart/background behavior and broader device acceptance.
6. Decide license and commercial access model; resolve artwork rights, private reporting,
   publisher signing and public privacy/retention policy before a paid public launch.
   Existing pilot access is not changed by these planning notes.

Documentation rollback is a separate revert of this publication, without changing APKs,
server state, device keys or signed catalogs. Future release rollback must preserve
identity and monotonic update/configuration floors.

[Presentation audit and owner commands](releases/2026-09-19-github-presentation.ru.md) ·
[Previous public plan, historical](PLAN.before-2026-09-19.md).

<a id="release-gates-three-platforms"></a>

## Release gates

Platform validation and immutable release signing remain required. The detailed
[earlier three-platform gates](PLAN.before-2026-09-19.md#release-gates-three-platforms)
are preserved; follow current STATUS and the release runbook for actual versions.
