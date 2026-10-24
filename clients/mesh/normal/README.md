# Protected normal configuration — desktop adapter

Status24.10: shared native source and Linux parent are locally tested. This is
not a product Auto coordinator, live authorization acceptance or Windows broker
integration. Android APK/source pins and deployed server policy are unchanged.

`fc-mesh --normal-stdio` accepts one schema1 request on private inherited pipes,
using the existing four-byte big-endian framing. Requests are bounded to192KiB,
with exact action-specific keys, canonical base64, duplicate/null/unknown-field,
UTF-8/depth and integer validation. IDs are1..2^53−1. No caller-selected URL,
executable, resolver, proxy or filesystem path is accepted.

- `fetch`: schema,id,action,anchor,country,floors,identity,wireguard_public,
  wireguard_private,underlying_index,budget_ms. Identity is64 bytes; Ed25519
  anchor and WireGuard keys are32 bytes; private/public WireGuard binding must
  match. The underlying interface must be live and not a Family VPN/loopback.
  Budget1..30000ms is bounded by the parent deadline, not a new retry loop.
- `inspect`: schema,id,action,anchor,country,floors,public,response. This verifies
  signed catalog/floor and response binding offline, not new authorization.
  Never turn inspect or a saved response into an offline normal-access fallback.
- `validate`: schema,id,action,anchor,country,floors,identity,wireguard_public,
  wireguard_private. This verifies key binding and all signed floors without
  interface lookup or network access. It returns only VALIDATED_MATERIAL and the
  derived public identity, never an authenticated configuration. The root host
  runs it even when offline, so missing connectivity cannot hide invalid keys or
  conflicting floors and inadvertently admit a restricted fallback.

The existing accepted readiness signer performs the fresh Friends challenge and
proof. Only the fixed authenticated normal origin and its challenge/RU/NL
configuration paths are allowed. The shared underlay protects sockets on the
selected real interface; redirects, compressed/oversized replies and trust
failures are rejected. There is no plain unprotected HTTP fallback. Cancellation
is checked again after transport return. Raw credentials are cleared/redacted,
not placed in command arguments, logs, error strings or test evidence.

At most three signed floors cover the two existing user-country catalogs plus
the root service floor. Signature domain remains
`family-connect/invited-test/v1\0`, schema2, increasing sequence; conflicting
highest-sequence payloads are rejected. Device/IP/UUID assignments are bound to
the fresh authenticated HTTPS response; the common catalog signature alone
does not authenticate personal assignments.

Success is `AUTHENTICATED_RESPONSE`, not READY/CONNECTED. The parent must still
apply the existing full Friends profile grammar before persistence or platform
configuration. Linux `auto_configuration.NormalOwner` reuses that same parser,
persists only the signed common catalog atomically, reads it back, then asks the
native child to inspect the result. Credentials remain in private process state
until supplied to the existing root helper; root floor files contain no actual
assigned TCP credentials or WireGuard private key. Existing Linux helper private
profiles remain0600, not a new Windows storage model.

Errors are bounded categories AUTH/CONFIGURATION/NETWORK/CANCELLED/INTERNAL.
Authorization/trust/configuration denial is terminal; cached normal configuration
is not accepted on transient refresh failure. This differs from the accepted
restricted-readiness cache contract, which remains unchanged.

The36 existing catalog vectors run through the actual native inspect process and
the shared Python profile validator. Other checks cover protected socket refusal,
fresh proof, cancellation, floor rollback, exact fields and bounded HTTP. These
local checks do not authenticate a real desktop device against the gateway.
Root→user floor synchronization, product service IPC/capabilities/coordinator and
Windows DPAPI/broker integration remain required before Auto activation.
