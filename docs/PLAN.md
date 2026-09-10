# Working plan / Рабочий план

## Active: 0.2.1 rollout and signed client updates

1. Finish Linux/Windows release checks and publish immutable pilot artifacts.
2. Replace the Linux installation; keep profiles/keys and a rollback path.
3. Back up and deploy only Family Connect on 185.251.89.19: gateway helper, product DB/API and periodic reconciliation.
4. Verify health, retained peers, worker and an install/remove transaction; publish signed update catalog.
5. Record exact deployed versions, CI evidence and outstanding user-device checks in STATUS.

## Next after verified rollout

1. Integrate provisioning into client runtime application and ACK; known-good VPN recovery.
2. Reticulum update announcements/catalog delivery through the same signature verifier.
   Notifications alone never authorize installing code. HTTPS remains the large-file delivery path.
3. Native secure storage/invitation flow for Windows and Android; check actual Windows DPI,
   VPN and in-place update on the user's machine when access becomes available.
4. Signed update root rotation/recovery, stable release channel, unattended-update policy
   only after publisher signing and OS integration are validated.
5. Distributed gateway agents and topology migration; real Reticulum delivery/failover.

Accounts, billing, public production ingress and hardware rollback protection are not
implemented by pilot entitlements, update signatures or a local SQLite database.
