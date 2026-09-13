# Stage 5 conformance inputs — PUBLIC TEST ONLY

`control-v1/manifest.json` is the portable contract for Python and future native
runners. This corpus does not implement a native verifier or use a VPN/carrier.
All fixture keys are intentionally public, derived from named TEST ONLY labels.
Never import them into a device, relay, signing configuration or deployment.
The generator has no key-file argument and reads no production key/profile file.

The manifest contains:

- `files`: exact byte length and SHA256 of every input/resource; check before use.
- `fixture_identity`: the PUBLIC TEST ONLY identity, WG key and issuer fixture.
- `domains_b64`: exact domain bytes, including the terminating NUL.
- `configurations`: file, clock, client version, expected category; accepted inputs
  also include expected decoded payload and SHA256 of the original wire bytes.
- `acknowledgements`: expected rejection or complete verified ACK body.
- `transcripts`: explicit initial clock/version/floor/committed state and ordered
  receive/crash/recover/flush operations with expected state and application counts.

Transcript application state is simulated; restarting the core preserves the
simulated external connection. A `flush` failure must retain the exact ACK bytes,
and a later successful flush must retry those bytes. `error` refers to the latest
outgoing ACK, not to the journal's retained last final application result.

Configuration categories are the reference ConfigError categories. ACK `REJECT`
is the reference generic invalid-ACK result, not a configuration error category.
An ACCEPT verification vector alone says nothing about revision acceptance by the
journal: `same-revision-other-bytes` and `wrong-previous` are valid signed envelopes
that the corresponding transcript rejects when applying sequence/chain rules.

Run the immutable corpus without regenerating it:

```sh
python -m pytest -q tests/test_control_vectors.py
```

Generate a candidate corpus into a **new** directory for explicit review:

```sh
python tests/generate_control_vectors.py --output /tmp/fc-control-vector-candidate
```

Encryption randomness means newly generated ciphertext/hashes differ. Commit and
review a new set explicitly; do not replace golden inputs in normal tests or CI.
The generator refuses an existing output directory. Git attributes disable newline conversion for the corpus and mark wire inputs as
binary, preserving boundary whitespace on Windows as well as Linux.
The committed bytes are what
Python, .NET and Java must share. Fixture keys are excluded from the paired preview
by its public-file allowlist; fixtures/generator also stay outside runtime images.
