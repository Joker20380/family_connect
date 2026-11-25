# 25 November 2026 UTC — exact OWNER overlay content inspection

Selected task: CONTROL-HA-20261123 / HA-02. This closes the source-content evidence gap called
out in the [configuration proposal](2026-11-24-control-ha-owner-activation-plan.md), not its
independent approval or installation. The [four stage2 gates](../control-ha.md#когда-заканчивается-этап-2)
are unchanged: isolated replication PASS, the same three other gates partial. No HA-03 selected.

## Why metadata verification was insufficient

`control_ha_owner_upgrade.verify` checks image runtime configuration/platform and that the
candidate adds exactly one layer to the original prefix. It does not inspect that added layer:
an extra executable, whiteout, link, modified source or permissive mode could satisfy the same
metadata shape. The new offline `scripts/control_ha_owner_overlay.py` checks the actual OCI
image graph and added-layer bytes against an explicitly SHA-pinned source manifest.

The existing image-custody verifier remains unchanged: it has a closed original console/
publisher/PostgreSQL scope and is not repurposed or weakened to accept candidate images.
This new checker is **not a replacement for full image custody validation** or a Docker loader.

## Checked boundary

- Exact selected candidate and role-baseline OCI manifest digests, their config descriptor
  size/hash, runtime Config/platform equality and unchanged compressed-layer/diff-ID prefixes.
- Selected added compressed blob size/hash, bounded decompression and exact uncompressed diff ID.
- Exactly ten permitted nonempty regular files, each root:root0644; only their eight root:root0755
  parent directories. All source bytes/sizes must match the separately supplied manifest.
- Extra/missing/duplicate members, symlinks/hardlinks/devices/FIFOs, whiteouts, path aliases,
  traversal, executable/setuid/group-writable modes, extended headers/xattrs, sparse files and
  nonzero trailing content refuse. No tar member is extracted or executed.
- Input source manifest and archive are private0600, same-owner/single-link under a0700 parent,
  with no symlink ancestors. Full archive SHA and before/after file identity/metadata are checked.
  OCI member count, JSON/blob sizes and gzip expansion are bounded; no descriptor URL is fetched.

The archive reader supports this pinned OCI layout, not a permissive legacy-format fallback.
It does not revalidate inherited base-layer payloads, audit dependencies, prove loaded processes,
read product state, reconcile external work or make any service change. `manifest.json` is not
treated as an executable import plan. Immutable OCI references identify the inspected content;
this does not authorize loading the archive, retagging images or recreating containers.

Source commit and expected hashes are inputs, **not independent approval minted by the tool**.
All receipts retain `independent_approval=false`, `runtime_qualified=false`, `capture_permitted=false`
and `deployed=false`. The prior configuration proposal remains a separate nonexecutable artifact.

## Actual retained candidates

The four existing baseline/candidate images were exported privately with `docker image save`;
the archive is69,692,416 bytes with53 members. No image build/pull/load/tag, container creation,
exec/restart, database access, source/config/permission change, RU/NL connection or version change.
No previous native stand was repeated. Source expectations came from `git show` at the exact
already pushed commit `fa05f0da63c2d6a8abfd767ea4c6d52c64fe023c`, not an uncommitted checkout.

**00:05:28.961783–00:05:29.491192UTC:** both candidate audits return SOURCE_MATCH/exit0.
Each layer has10 exact files and8 permitted directories. There is no observed source drift.
Both uncompressed added layers are53,760 bytes; differing archive metadata yields distinct
compressed/diff-ID hashes despite identical source content. This is not a measured capture window.

| Role | Original / rollback image | Inspected candidate |
| --- | --- | --- |
| Console | `sha256:5ce824159e9f206c27ba92185097857382aa5fec71678ce5e728423509d1446a` | `sha256:b62e66930cd672ed5350c1e5b7c19f48f0f77ffcdbe3ce9b2b2b9a85a608e8e0` |
| Publisher | `sha256:50de6f25a04c1127b127b3278314619c69eddeec229d0d4ad9b7e67c1d2ffeab` | `sha256:2162635c93cf7cdf376aa7a0cb6189ff8a4f8105f4c26aea6d28e63ccfb93a79` |

| Evidence | SHA256 |
| --- | --- |
| Exported private archive | `aaad36c23002d8b4939f17cae0ca65a5962fcdd52091a81f71eda636694cff44` |
| Exact source-manifest file | `828d94899e66e586be582d6e7fc3fb3637024066db3905c035f8db8882b56639` |
| Final checker source | `9f01febea1ce427865a6cddb44c8ade662f735a8b9704e1466b446ec151a5d7f` |
| Console receipt | `22690bbb6971ad7b647f62c72491377e48539baa96249732d781034d1c531bbe` |
| Publisher receipt | `f0688650661cc02fde96688388ba3be9ac6b274423ccd897f33ca03328e13915` |

Private files are retained under `~/.local/share/family-connect/control-ha/20261124-owner-overlay-*`
(export started24 November); `/tmp/fc-ha-owner-overlay-current` identifies the directory.
Archive/raw image config never enters Git or command output. Receipts expose only known source
paths, digests, sizes, role/image IDs and explicit nonapproval flags, not environment values.

## Repeatable offline command and tests

```sh
python -m scripts.control_ha_owner_overlay \
  --archive /private/owner-images.tar --archive-sha256 "$ARCHIVE_SHA256" \
  --sources /private/expected-sources.json --sources-sha256 "$SOURCES_SHA256" \
  --role console --candidate "$CANDIDATE_IMAGE_ID"
```

Exit0 means exact source match; exit2 means a structurally closed but stale/different source
layer, with only known changed source paths in the receipt. Exit1 emits only
`OWNER_OVERLAY_REFUSED` for invalid/unverifiable input. No output file is overwritten by the CLI;
it reads the pinned inputs and emits a sanitized JSON receipt to stdout. Exit0 is not deployment
authorization. Supply trusted pins; do not substitute hashes merely to make a failed check pass.

`python -m pytest -q tests/test_control_ha_owner_overlay.py tests/test_control_ha_owner_upgrade.py
tests/test_control_ha_owner_activation_plan.py`: **173 PASS,0 skips,1.35s**,56 new cases.
Coverage includes forbidden tar members/metadata, runtime/base/reference drift, stale source,
digest/duplicate-JSON/expansion bounds, private-file replacement/permissions/links/FIFO/oversize,
read-only CLI behavior and sanitized decompression failures. No Docker dispatch in unit tests.
The actual final CLI checks above reuse the retained export; no additional export or stand run.
Documentation checks: four files/1079 link targets/zero errors, plus clean whitespace. External
URLs are enumerated, not fetched; test and documentation receipts remain private.

## Rollback and next decision

There is no working change to roll back. Preserve original images and the private proposal;
do not restore old DBs, remove uncertain markers or weaken permissions. Prior cross-container
gate proof stays accepted and is not installed binding approval. The last installed observation
remains the24 November23:50 OWNER pre/post check, not a new runtime observation from this audit.

Next is independent acceptance of this exact candidate/config/runtime evidence and an authorized
actual gate/guardian setup, with existing publication/support/manual operations settled before
replacement. Working console namespace access is still unqualified; do not bypass it with chmod
or privileged host-PID helpers. Remaining RU/NL/manual/transport participation, approved coherent
capture, independent current checkpoint/key/access custody and final combined recovery remain.
Working-NL deployment remains outside current permission. Do not repeat this completed content
audit, config plan, cross-mount stand, build, collector packaging or NL2 diagnosis as new gates.
