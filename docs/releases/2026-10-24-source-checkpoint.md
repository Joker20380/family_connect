# Source checkpoint and immediate commit/push policy —24 October2026

The owner explicitly requested preserving all current work in GitHub and committing/
pushing each completed logical change immediately in future. AGENTS.md now carries
that standing instruction, with secret/state exclusions, ordinary non-force pushes
and mandatory remote-SHA verification. This request supersedes the earlier no-push
instruction for this source checkpoint; it does not resume paused implementation.

## Scope

- Existing branch `main`, existing origin `Joker20380/family_connect`; no new branch,
  tag, history rewrite or release-prefixed commit message.
- All current safe tracked/untracked source, tests, CI definitions, documentation
  and sanitized reference/evidence manifests, including the accumulated desktop106
  work and owner-diagnostic/P1 fixtures. Fixtures remain distinct from accepted code;
  committing them is not permission to deploy experiments or change entitlements.
- Private `state-client-build/` and other ignored state directories, capsules,
  raw evidence, user identities/profiles, databases, backups and signing keys stay
  local. Native binaries and the internal component are referenced by checksums in
  the parity report, not uploaded as source or published as installers.

## Validation and delivery boundaries

The latest finalized parity checkpoint is phase22 in
[the continuing report](2026-10-23-desktop-parity106.md#linux-user-chat-admission-and-existing-exit-handoff-24-10-phase22):
1218 selected Python regressions PASS, six Linux native packages race PASS,
Windows native cross-build only,175 shared/2073 capsule checks PASS. The internal
component has98 files,22 root modules and4 common modules. These results do not
certify every historical fixture included in this source checkpoint or replace
GitHub CI and installed target-OS checks. Commit preparation adds staged-content,
secret/path and whitespace checks; exact remote-SHA verification follows the push
and is reported to the owner rather than predicting its outcome in this document.

Staging found eight harmless extra blank lines at Python file ends; only those EOF
lines were removed. Historical evidence retains its pre-checkpoint source hashes;
these whitespace-only changes are not a new behavioral acceptance run. Raw patch
files retain their exact bytes and pinned SHA256: `.gitattributes` applies the
existing diff-file whitespace exceptions to all `*.patch`, where leading context
spaces before tabs and context-only blank lines are required by the patch format.

Gitleaks8.30.1 is downloaded from its official release and checked against the
release-asset SHA256 before local scanning. The initial staged scan reports22 false
positives:18 exact64-hex SHA256 manifest values, one explicitly labelled128-bit
public signing-key fingerprint and3 ordinary descriptive phrases.
Each is inspected; the second scan uses only those exact finding fingerprints as
a local reviewed baseline, not a repository-wide secret-rule/path exemption.
Raw scanner files and the review remain in ignored local state. No private key,
profile, database, raw capture or binary is intentionally added to the source tree.

Linux0.2.11/Windows0.2.15 and accepted Android0.1.18-beta106-recovery remain unchanged.
No Android reference rebuild/install, gateway action, entitlement change, new signed
catalog, release tag or installer publication is part of this request. Existing CI
may run on the source push; completion or success is not assumed. The main client
release job is gated by release tags or a `Release ` commit subject; this checkpoint
must use neither. Historical distribution jobs target other dedicated branches or
manual dispatch and are not requested.

No installed deployment changes, so no runtime rollback is necessary. Keep prior
local capsules/artifacts/evidence; rollback of code, if requested later, should use
an ordinary revert rather than reset/force-push. The parity goal remains paused and
incomplete: protected DIRECT/service-only, Windows product integration, full visual
acceptance, exact installed upgrade and full private installers are still pending.
