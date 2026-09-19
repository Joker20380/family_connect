# Licensing audit — 2026-09-19

No repository-wide LICENSE was present in the repository or detected by GitHub during
this audit. The owner has not selected one. Do not infer a license from public visibility
or apply a new root license to third-party code and artwork.

The owner intends to earn revenue from the service. A free app download and permission
to reuse source code are separate from authorization to use operated VPN servers.
Billing/subscription enforcement is not claimed to be production-ready by this audit.
MIT was discussed but not approved. License choice remains open pending the intended
commercial/reuse model and dependency review.

## Known third-party material

- The networking builds embed external projects with their own licenses and attribution
  requirements. Preserve pinned build inputs and packaged license notices. The Xray
  text is available at [pilot/tcp/LICENSE-Xray](../pilot/tcp/LICENSE-Xray).
- Classic smileys have an explicit [provenance record](../clients/android/app/src/main/assets/chat/icq-classic/provenance.json).
  It says the exact official version and redistribution license are not established.
  Its old “not released” wording does not describe current distribution: the beta APK
  now contains these assets. Resolve rights or replacement before claiming a fully
  licensed open-source distribution. The user has deferred the visual replacement.
- Original project artwork and third-party materials need separate scope/ownership
  confirmation; a root license must not silently relicense them.

This is an inventory of known gaps, not a completed dependency-license compatibility audit.
No license text or reuse permission was added in this documentation change.
