# L04.1-LIVE-2-RESUME — continuation,25.10.2026

**ACTIVE, same checkpoint; no new task ID or architecture phase.** Entry main
`4abe406a7143d8f5353a1d1e1174f6ed05cd5dda`. Review accepts exact .4 A/B1 PASS.
The registry start18:28:22UTC predates B1 Connect18:34:12UTC and is not a B1 blocker.
[Earlier receipt](2026-10-25-linux-installed-awg-tcp-l04-1-live-2-resume.md) is retained
as historical evidence; B1 must not be repeated. Parent L04.1 remains IN_PROGRESS.

## Immutable inputs and execution boundary

Only `state-client-build/linux-prestart-journal-l041r1-20261025/build-2/`:
version `0.2.12~l03.2.4`, source `053c4e5f9532ca927f49a78f9c0ed17903375baf`,
candidate `42ea0699263f2527057a36082b2b95235c4ac452cc5e86eed6ec15ebd50898cf`,
system `8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d`.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| AppImage | 57928184 | `c78c68ec99b187269b87d40d457c8db09d3593b45f199a8705d0a83222cc3273` |
| DEB | 55986866 | `8b23ac6d93c747955017a3b0d5c33745e7272f2c24fc950f4e8f0d0b367af4da` |
| Embedded system archive | 49250848 | `ddd74c2132a76ac833b587d9df6409d779ce6afcdaa45fafd23faa86d7817726` |

Existing protected FC-3YSQ-BE2D/nl preflight PASS; no new identity/invite/activation,
provisioning, RU assignment or manual configuration fetch. Only protected `home/`
may enter the new encrypted KVM, never operator material. Product/installed bytes
must not be patched. No host network/service changes or server mutations.

Execution order: short positive P1 AWG/P2 TCP continuity, then B2,C1,C2,D,E,F1,F2.
Each destructive scenario uses a clean snapshot. Before each live action: three
consistent read-only server observations at least10s apart; structural firewall
canonicalization removes counters/timestamps. Service transitions are evaluated
against the action window, not an unrelated earlier baseline. First new product
failure stops further actions; only safe cleanup follows. No repeated fresh-DNS,
upload, reconnect loop or AppImage close/reopen positive gate.

## Installed progress

[Sanitized machine-readable receipt](evidence/l04-1-live-2-continuation-20261025.json).
Exact artifact/member verification PASS (707 user members). New encrypted KVM:
Ubuntu24.04.5, kernel6.8.0-147, systemd255.4; real NetworkManager/resolved,
polkit/password approval, D-Bus/Secret Service, TUN and firewall. DEB GUI UID1000,
explicit setup and exact system READY PASS; only protected home copied.

- **P1 AWG PASS:** one up/down, one owner/TUN and recent handshake; HTTPS200,
  download65536 bytes. Operation0→2 connected→3 disconnected, journal IDLE/null.
- **P2 TCP PASS:** one up/down, actual TCP/Xray and one TUN; HTTPS200,
  download65536 bytes. Operation3→5 connected→6 disconnected, journal IDLE/null.
- Both restore the full structural network/DNS/firewall baseline and preserve
  identity/cache/floors. Three immediate stable server reads before each action,
  post-readback identical target1/1 +1/1, foreign/config/catalog/service identity.
  No upload, fresh-DNS repeat, reconnect loop or AppImage close/reopen positive gate.
- **B2 PASS:** clean independent snapshot, foreign durable generation1/pending;
  one GUI Connect, helper requests0, terminal DISCONNECTED/PENDING_OPERATION,
  RECOVERY_REQUIRED and unchanged foreign reservation. The fixture waiter expired
  at its300s bound before release; a replacement UID1000 process resumed the exact
  same fixture owner and used production `lease.finish()`, not a journal edit:
  generation2/null, read-only poll PASS. This is same-owner completion, not a claim
  that the original waiting PID survived. No second GUI action. State/network and
  three-pre/one-post server checks PASS. Physical operation lock remains free.

- **C1 AWG unavailable PASS:** one endpoint-only guest firewall drop fixture,
  one Connect/up, no CONNECTED/fallback. HELPER_FAILED/OUTCOME_UNKNOWN correctly
  retained APPLYING/generation1/pending with no remaining network owner/TUN.
  Authorized same-owner startup recovery used down1/discard1, generation2,
  IDLE/null; poll, network baseline, identity/cache/floors and server readback PASS.
  Original HELPER_FAILED diagnostic retained (historical pending fields are not
  the current coordination journal). The first reopen lacked a polkit agent in
  its new SSH login session: no approval/down, pending correctly retained. After
  repairing only fixture agent/session binding, startup recovery succeeded; no
  repeated Connect. Initial nft syntax rejection was repaired before user action;
  its incomplete server pre-read is not counted among the three final reads.

C2/D/E/F1/F2 still NOT_RUN at this intermediate documentation checkpoint.
Only sanitized docs/evidence committed; product/installed bytes untouched.
L04.2/L05/device teardown/revoke/publication NOT_RUN.

STOP. NEXT — review завершённого L04.1-LIVE-2.
