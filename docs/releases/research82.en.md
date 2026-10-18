# Research82 — private lease continuity candidate

Version `0.1.18-research82-lease`, code82, package `com.familyconnect.app.friends`.
Reserved after checking owner81, persisted reservations and current public tags.
Built and installed in place on the owner only; no public download/distribution.
APK SHA256 `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18`.
Source/native commit `fbbecb81c033557f6c29819a02b8382519465961`, same package/signer.
Existing public downloads and invitation versions are unchanged.

Authenticated renewal uses the current Family/Mux session and admission holder;
expiry, revocation and credential security deadlines remain enforced. Local
controlled-clock tests retain one TCP socket across two lease boundaries. Live
Telemost trial accepted two renewals and11 full HTTPS replies after both previous
deadlines. Persistent socket crossed the first boundary but failed assertion170,
without reopening; exact cause UNKNOWN. Full seamless continuity is not established.
Startup refresh, automatic recovery,
UI, normal transports and publisher identity are preserved.

See [acceptance and remaining gates](2026-10-11-telemost-lease-continuity-1.md).
Six historical diagnostic assertions remain a separate known issue. No public
release, APK distribution or Krasnodar FIELD trial is authorized by this build.
Final VPN OFF, ChatDeliveryService ON; helpers removed, cleanup restart0. No repeat.
