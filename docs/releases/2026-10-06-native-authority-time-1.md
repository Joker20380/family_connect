# NATIVE-AUTHORITY-TIME-1 — PASS

2026-10-06. Investigation only, followed by read-only packaging preflight.
**Timing blocker resolved by clean source attribution; no runtime/test-code fix.**
DIAG-SOURCE-FREEZE-1 remains PARTIAL; DIAG-PAIR-DEPLOY-1 is NOT allowed to start.

## Proven cause and exact calculation

Classification **4: interaction with preserved, explicitly excluded readiness/control
changes**. Not a nondeterministic test clock, rounding error, subprocess delay or
native expiry mutation. The failing assertion is unchanged at
`tests/test_native_authority_compat.py:105`:
`response['expires_at'] == now + 3599`.

Let N be the fixture's captured integer Unix second:

| Source | Issuance/cap | Directory cap | Final response |
| --- | --- | --- | --- |
| Baseline8d04632 + diagnostic allowlist | issued=N; expiry candidate=N+3600 | N+3599 | N+3599 |
| Preserved mixed working tree | issued=N-5; expiry candidate=issued+3600=N+3595 | N+3599 | N+3595 |

Therefore `(N+3595)-(N+3599)=-4`, not a4-second execution delay. The same mechanism
explains the four-hour test: N+14395 instead of its unchanged N+14399 expectation.
In the mixed fixture the new CRL ThisUpdate cannot precede its previous N-1, so CRL
NextUpdate is N+3599, not N+3595. The response's issuance/lifetime cap is the tighter
bound. The generated device certificate also expires at N+3595.

Minimal disposable import overlays confirm causality without changing product files:
readiness_receipts alone and readiness_receipts+restricted_admin remain at delta0;
readiness_receipts+restricted reproduces-4. Thus the fetch calculation in
`control/friends/restricted.py:334`–358 is the relevant excluded change, not the
ACK rule or CRL calculation alone. This is not an identified native validator defect.

## Authoritative contract

Authority is the existing code/tests, including
[the05.10 clock-skew decision](2026-10-05-readiness-clock-skew.md#server-correction),
`tests/test_restricted_clock_skew.py`, `tests/test_friends_restricted.py`,
`carrier/wholedevice/provisioning.go` and `tests/vectors/bootstrap-timestamps.json`.

- Readiness issued_at/expires_at are **absolute integer Unix seconds**, not a TTL
  refreshed at import and not “approximately one hour from processing time.”
- Numeric expiry is preserved second-for-second across JSON and native validation.
  This does not require identical JSON whitespace or key ordering.
- Baseline issuance uses the captured service clock. The excluded server correction
  intentionally backdates issuance by at most5s, bounded by issuer/CA NotBefore,
  and bounds expiry by **issued_at + configured lifetime**, grant, issuer, CRL,
  device certificate and directory ceilings. It explicitly shortens expiry rather
  than extending the configured one/four-hour interval or prior absolute ceiling.
- Certificates/CRLs in this fixture have whole-second UTC bounds. Directory RFC3339
  timestamps support up to nanosecond precision; conversion to readiness's integer
  expiry conservatively floors that ceiling. The failing fixture has zero fractional
  directory seconds, so flooring loses nothing here.
- Native `ValidateDelivery` decodes int64 timestamps, requires issued_at<=now and
  expires_at>now, enforces maximum interval and every signed upper bound, then returns
  the same decoded delivery. It does not subtract elapsed time or mint a new expiry.
  `familysession.Configuration` selects a minimum of absolute certificate/CRL/CA
  times. `readiness.go` computes a display remaining-seconds value, not a replacement
  authority expiry.

Changing the mixed server expiry to satisfy the old N+3599 assertion would make
its interval3604s from the backdated issue instant. No such widening was performed.
No wider comparison tolerance, changed security constant or skipped failing test.

## Clock and boundary audit

`fixture()` captures `now=int(time.time())` once at line47, before generating keys,
profiles or certificates. `configured()` injects `Access(..., clock=lambda: now)`.
Both fetch clock reads (before trust validation and inside its DB transaction)
therefore use that same N. In the captured failing run all9 service-clock reads
equal1791262963: Access activation challenge/completion, grant, CRL publication,
restricted challenge, two fetch reads and two directory-clock conversions.
Delegation/X.509 timestamp conversions do not obtain fresh issuance time.

`clock_nanoseconds` uses Decimal(str(clock())) ×10^9 for this injected lambda;
its real-clock time.time_ns branch is not taken. `timestamp_ns` preserves RFC3339
fractional seconds; `timestamp` floors by10^9. `utc(N)` creates an aware UTC datetime.
All relevant values here are integral; no milliseconds conversion occurs. JSON
emits/decodes integer seconds; Python integers and Go int64 preserve these values.

Native tool compilation is pytest fixture setup, **before** the test captures N.
The failing assertion occurs **before** `native(...)` or `delivery(...)` is called.
Their wall-clock/certificate verification and process scheduling cannot cause this
failure. In successful executions, the CLI's time.Now/default x509 verification
checks validity only. The delivery checker uses explicit time.Unix(input.Now,0), or
time.Unix(0,input.NowNS) for nanosecond scenarios; it does not recompute issuance.

### One failing execution, exact UTC trace

Private receipt: `native-authority-time-1/mixed-isolated-20/01.json` under the
existing ignored DIAG-SOURCE-FREEZE evidence directory. Only scalar timing metadata
is recorded; no key, identity, profile, certificate, payload or credential contents.

| Stage | Actual UTC observation | Safe value |
| --- | --- | --- |
| T0 test call starts | 2026-10-06T05:02:43.854759Z | native tool setup already finished |
| Test clock captured | 2026-10-06T05:02:43.866436Z | N=1791262963 /05:02:43Z |
| T1 authority input created | 2026-10-06T05:02:43.933015Z | authority start N-10; initial CRL/directory expiry N+3599 |
| CRL publication | 2026-10-06T05:02:43.947413Z | ThisUpdate=N-1, lifetime3600s |
| Gateway certificate generated | 2026-10-06T05:02:43.949968Z | NotBefore=N-5, NotAfter=N+14400 |
| T2 response expiry assigned | 2026-10-06T05:02:43.965156Z | issued=1791262958; expires=1791266558 |
| Device certificate generated | 2026-10-06T05:02:43.966357Z | NotAfter=1791266558 |
| T3 response JSON round-trip | 2026-10-06T05:02:43.966648Z | integer1791266558 unchanged |
| T4 native import/processing | NOT REACHED | original assertion aborts first |
| T5 Python output observed | 2026-10-06T05:02:43.968664Z | expires06:02:38Z |
| T6 assertion executed | 2026-10-06T05:02:43.968691Z | same N; expected06:02:42Z, actual06:02:38Z |

T5 is the authority's Python response, not native output. The requested idealized
T0→T6 ordering is not the actual failing path: there is no T4 before the assertion.
Total call elapsed approximately0.114s. A separate synthetic native probe, without
altering/bypassing the original pytest assertion, supplies the missing process-boundary
evidence: serialization05:08:53.559450Z, native entry05:08:54.813943275Z, native output
05:08:54.815387250Z; expiry1791266928 is unchanged despite the1.25s delay. Validation
at expiry-1 succeeds; at expiry it rejects. Baseline/scoped source behaves identically
with its own exact N+3599 expiry. Receipts: native-mixed.json and native-scoped.json.

## Reproduction and acceptance

All runs use fresh pytest processes, synthetic local fixtures and the existing
lockfile-matched environment. No phone, gateway or production authority contacted.

| Source/experiment | Repetitions | Result / delta distribution |
| --- | --- | --- |
| Preserved mixed tree, unchanged isolated test |20|20 FAIL; {-4s:20} |
| Mixed tree,1.25s deliberate delay after authority input |5|5 FAIL; {-4s:5}; service clock remains fixed |
| Mixed tree, complete compatibility file |3|each17 PASS/2 FAIL; one/four-hour assertions both-4s |
| Scoped snapshot, unchanged isolated test |20|20 PASS; {0s:20} |
| Scoped snapshot, complete compatibility file |3|each19 PASS; both expiry assertions0s |
| Scoped + excluded readiness_receipts only |3|3 PASS; {0s:3} |
| Scoped + excluded readiness_receipts/restricted_admin |3|3 PASS; {0s:3} |
| Scoped + excluded readiness_receipts/restricted |3|3 FAIL; {-4s:3} |
| Scoped + all three excluded control modules |3|3 FAIL; {-4s:3} |
| Scoped full Python, official verified CI fixtures |1|1793 PASS,26 skipped,2 warnings; exit0 |
| Absolute-expiry native process probes |both sources|exact-value preservation and expiry-boundary rejection PASS |

The full scoped run lasted320.72s (05:06:32–05:11:54UTC). Its log SHA256 is
`03d8521758ef6ce02b4635c00ea304f801265e56e83a11ec2fe6caba2933b298`.
Opt-in skipped tests are not native/device/hosted-CI acceptance. The original mixed
full-suite failure905 PASS/26 skipped/1 FAIL is retained, not relabeled green.

## Exact correction, scope and remaining freeze work

**Correction: acceptance-source isolation, not a product/test patch.** A disposable
checkout of baseline8d046321039d0bd1e18ecc1af979ff90f591e029 receives exactly the32
non-document diagnostic paths from the previous scoped receipt, byte-for-byte.
Excluded readiness/control/test/docs edits stay out; originals remain untouched.
`snapshot.json` records every copied path/hash. This is a test input, not a frozen
release commit. No test assertion or clock was changed; no tolerances were introduced.
The mixed-source compatibility expectations belong to the separate control work and
were neither fixed nor absorbed here. Clean causal attribution is preserved.

No runtime/security semantics, credential lifetime, production retry/RTO/pacing,
TLS/Mux/TUN or native product source changed. All original scoped and unrelated
source hashes are preserved; working-copy scoped privacy/source scans and
`git diff --check` pass. The original Git index remains empty. Unchanged accepted
Android/Go/race gates were not restarted; only the requested compatibility/native
timing checks and full Python source-scope validation ran.

DIAG-SOURCE-FREEZE remaining gates resumed with Gradle source-provider inspection.
The command succeeds, but ownerDiagnostic's configured source providers do not
include Friends' restricted-generated JNI/assets directories. No restricted JNI or
restricted-build.json is currently in the owner's resolved inputs. This is a
**NOT_READY packaging-input gate**, not proof that an APK build failed. Newly built
owner-tagged JNI/schema1/source_revision metadata must be explicitly staged in that
variant before a pair can be accepted. Merely using initWith friends is insufficient
to inherit source directories; do not substitute old/default JNI. No packaging
source correction, candidate build or freeze commit was made in this timing task.

Final statuses: **NATIVE-AUTHORITY-TIME-1 PASS**; **DIAG-SOURCE-FREEZE-1 PARTIAL**;
**DIAG-PAIR-DEPLOY-1 NOT allowed**. Timing no longer blocks clean-scoped continuation;
native input integration and remaining freeze/CI/artifact/signing gates remain open.
Draft beta66/code66/schema1 and required signer67a90d1b are unchanged; no accepted
new APK/JNI/gateway, signature or pair manifest exists. No install/deploy/renewal/
READY/phone fault/physical Telemost/soak/Krasnodar contact/public beta65 or channel
change. No runtime rollback needed. Preserve the ignored evidence and original work;
do not revert deployed control code merely to reproduce the reference snapshot.
