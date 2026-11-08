# Apps and VPN

Beta123/code123 candidate: **Settings → Apps and VPN**. This is not a public update
announcement. Exact artifact identity and acceptance belong to the
[task receipt](releases/2026-11-08-android-app-vpn-recovery.md); the owner's installed
beta122 and its signed bytes are not changed by this preparation.

- **All apps** is the default, including migration from previous versions.
- **Selected apps only** sends the selected apps through VPN. An empty or unavailable
  selection prevents connection; it never silently becomes All apps.
- **All except selected** leaves selected apps on their ordinary connection.

Search local labels or package names, distinguish identical labels by package name,
and use the selected filter. Apps lists current-profile launcher packages, including
preinstalled apps. All apps and components also exposes non-launcher services.
Retained unavailable selections remain inspectable; disabled and unknown packages
are distinguished without assuming that another profile means uninstalled.
Inclusion and exclusion lists are stored
separately, locally only. Apps sharing an Android UID share a rule; a work profile
has a separate VPN and cannot be managed from this profile's screen.

Save the selection. During a connection it remains **pending until the next explicit
Connect**. Auto handoff, recovery and the blocking interface retain the active
snapshot. Server/transport selection does not reset it. Review unavailable apps
before connecting; reinstalled packages are resolved again on a new connection.

Apps outside VPN use the ordinary connection and remain subject to that network's
restrictions. Android's Block connections without VPN can additionally block them;
this screen never changes lockdown or Always-on. Explicit Disconnect/system revoke
removes the VPN interface and does not preserve its blocking protection. IPv6 depends
on the transport/profile; unsupported VPN traffic is not silently sent directly.

The selection changes neither server profiles nor trust, subscription or access
decisions. Family Connect is not secretly excluded: protected transport sockets are
distinct from user traffic. Package inventories and selection never go to servers,
telemetry or ordinary logs.
