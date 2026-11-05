# MESH authenticated credential exchange / 5 November2026

## Result and version boundary

**10:10UTC SOURCE IMPLEMENTATION / LOCAL QUALIFICATION; NOT DEPLOYED.** Continuation
of the selected Android MESH stability incident and the
[09:16UTC native boundary checkpoint](2026-11-05-mesh-renewal-continuity.md).
This implements the native authenticated successor exchange, not the complete fix for
the [scheduled two-node outage](2026-11-05-mesh-overnight-checks.md).

Owner Android118 and the [opt-in field118 download](2026-11-05-android118-field.md)
remain unchanged; default invitation/updater113/catalog7, Linux0.2.11 and
Windows0.2.16/catalog12 are unchanged. Both NL gateways were last verified at70e6c0fc;
this checkpoint performs no SSH, phone action, live readback, deployment, signing, tag,
catalog mutation or rebuild of118. Test executables are local qualification artifacts,
not installed gateway binaries. Field installation/allowlist acceptance remains OPEN.

## Protocol and invariants

`familysession.Session.RenewCredentials` is explicitly opt-in. Each peer independently
supplies a fresh profile over a trusted local path; the wire carries public leaf DER,
CRL digest/floor, generation, fresh nonce and signatures, never a private key/full profile.
`MuxConfig.CredentialRenewal` selects virtual port2 on the existing reserved hostname.
It shares the single bounded control lane with port1 lease renewal; no extra data quota,
external listener, DNS fallback or unbounded queue is introduced. An unconfigured peer
rejects the request and retains normal data traffic under its original security bound.

- TLS1.3 exporter, ordered client/server hellos, fresh32-byte nonces and generation are
  hashed into a purpose-separated Ed25519 proof. Replaying another TLS session's proof
  cannot authenticate this session. Canonical length-prefixed JSON is bounded to8192
  bytes per message and remote leaf DER to4096 bytes; duplicate/unknown fields fail.
- Authority DER, Family, gateway, minimum revision, identity subject/URI and public key
  bindings must remain unchanged. Revision changes and key/authority rotation are not
  eligible. CRL number/floor/times cannot regress; same-number CRLs must be identical,
  and existing revoked serials cannot disappear. Both peers must use the same CRL/floor.
- Chain/EKU/hostname/claims/validity and revocation checks apply to both predecessor and
  successor leaves. An expired or revoked predecessor cannot be revived. The successor
  bound is the minimum of both leaves, CRL NextUpdate and authority expiry and must
  strictly exceed the original bound. This API is not a no-op refresh scheduler.
- Exchange order: client/server hello, client-proof, server-proof, client-commit,
  server-committed, client-done, then FIN/EOF/graceful control close. Server commits after
  client-commit; client commits after signed server-committed. Both commits must precede
  the original hard deadline. This is not simultaneous distributed atomic commit:
  loss/corruption after one side commits fences the native session, not an expired rollback.
- Only one exchange can run per native session. The exchange is bounded by caller
  cancellation, the original security deadline and15s. Local ineligibility/busy rejection
  resets the control stream without extending anything; a started exchange's failure,
  cancellation or ambiguous confirmation closes the native session. No automatic retry.
- A mutex serializes credential commit with TLS I/O deadline installation. Existing
  blocked reads/writes receive the authenticated new security bound while retaining
  tighter caller deadlines. TLS connection, frame sequences, mux and TCP socket persist.
  `ConnectionState()` remains actual original TLS handshake evidence;
  `AuthorizationState()` provides a separate copy of renewed peer/chain authorization.

The new control protocol exposed an existing lifecycle limitation: server-side control
`MuxStream.Close()` could not acknowledge a drained bidirectional close and waited for
its timeout. The server-control path now completes the same close handshake as normal
forwarding. Client/data-stream behavior and the existing10s close bound are unchanged.

## Qualification and retained failures

Toolchain Go1.26.1; all native runs listed below use `-race` except the dedicated parser
fuzz/vet checks. Disposable signed Ed25519 leaves/CRLs, actual Family TLS/mux and persistent
loopback TCP are used, not a mocked deadline setter. Product-backed regression fixtures
are freshly generated with `pilot.telemost_family_fixture`, kept outside Git.

| Gate | Result and scope |
| --- | --- |
| Original leaf/CRL deadline continuity | PASS, three repetitions per boundary in isolated Docker; six actual wall-clock crossings, same TCP socket, concurrent24 payloads, unchanged original TLS peer and renewed authorization peer |
| DNS during renewed session | PASS in each of those six cases, real mux TCP DNS to a disposable local port53 fixture; not external Internet/Android DNS acceptance |
| Unsafe successor, proof corruption, cross-session replay, cancellation, malformed/version/generation/oversize messages, legacy peer | PASS; repeated security subset260 leaf cases over10 runs, zero skips |
| Late server confirmation beyond original bound | PASS; client cannot revive an expired session, both sides close |
| Two successive authenticated generations | PASS20 repetitions on one TLS/mux/TCP session, CRL2→3 and corresponding successor serials; no new handshake |
| Native regression | PASS five packages: familysession, tcpforward, roombroker, wholedevice, restrictedowner;358 passing leaf cases/409 total pass records,25 explicit skips |
| Canonical parser fuzz | PASS237,469 executions in10s, two workers,56 additional interesting inputs, no failing corpus |
| Formatting/static checks | gofmt and Go vet PASS; documentation links/whitespace checked before commit |

The25 host skips are20 pre-existing root canonical-profile cases, three optional
performance/process harness cases, and two new port53 DNS cases. The latter two are
actually exercised separately in the isolated harness, not counted as host passes.
The final20 repeated-generation cases follow the broad regression snapshot and are
reported separately, not added retroactively to its358 cases.

The DNS harness runs a host-built race binary in
`family-connect-renewal-tests:20261030`, image digest
`sha256:ca61f885607656ea89f5726853761c4c533d050faf26b71853575c24ca1ed123`,
with `--network none --cap-drop ALL --cap-add NET_BIND_SERVICE` and
`FC_RENEWAL_ISOLATED_DNS=1`. No product/state mount or external DNS is used.

Initial development failures are retained: an ephemeral DNS port in the test fixture
violated the existing port53 policy; the harness was corrected without weakening policy.
The subsequent control-close timeout led to the lifecycle fix described above.

The broader six-package run is **NOT all green**: bootstrap's
`TestProductIdentityOverBootstrapCarrier` fails the same six diagnostic-counter assertions
for unknown/wrong-family/revoked/wrong-gateway/stale-crl/stale-revision peers. A source-only
`git archive` of baselinebea04212950dab381229867418ec3873cc493816 reproduces exactly
those failures with the same fresh fixtures/race toolchain. They are not unauthorized
admission successes and are not repaired in this change. No full CI/platform PASS is claimed.

Raw local evidence remains ignored under
`state-client-build/mesh-renewal-exchange-20261105/`: `final-native.jsonl`,
`security-repeat.jsonl`, `repeated-generations.jsonl`, `security-final.jsonl`,
`isolated-dns-final.log`, `renewal-fuzz.log`, `vet-final.log`, `native-regression.jsonl`
and `baseline-bootstrap.jsonl`. No private fixtures, source capsules or binaries in Git.

## Remaining integration and activation gate

1. Connect trusted fresh Android/native credential delivery and a bounded renewal trigger.
   Handle unchanged/no-benefit candidates before starting an exchange; do not blindly
   invoke it on every refresh. Old118 peers must retain old behavior and their hard bound.
2. Integrate the new authorization generation with gateway lease admission/renewal and
   the broker's original control-session authorizer/monitor. Today these closures still
   capture the original identity/deadline; `AuthorizationState()` alone does not update
   them. Serialize refresh, revocation, cancellation and lease extension consistently;
   add end-to-end tests beyond the full old lease/security bound, not only native transport.
3. Build a separately qualified coordinated online publication path for eligible same-holder
   leaf/CRL refresh. Preserve single-writer locking, per-node preparation/readback, durable
   decisions and crash reconciliation. Keep existing quiescence/stop guards for ineligible
   and emergency changes; no timer pause or expired-material rollback. Neither production
   gateway registers the new handler and no current maintenance stop is removed here.
4. Exact-source platform CI/artifacts, then the same accepted binary on both NL nodes with
   verified running hashes. Observe scheduled renewal under traffic on both nodes; retain
   physical lossy/screen-off, paired-DNS/signaling diagnosis and real field-user allowlist
   gates. No local harness result substitutes for those environments or user installation.

Rollback is source-only: a normal follow-up revert removes this opt-in implementation;
there is no deployed runtime to roll back. Leave118 bytes and catalogs immutable. Future
client delivery requires a higher version, exact platform qualification and offline signing;
source commit/push is not permission to bypass those release/activation gates.
