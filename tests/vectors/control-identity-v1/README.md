# Android control identity — PUBLIC TEST ONLY

`identity-binding-proof.json` is the deterministic Python `DeviceIdentity.prove_transport_key`
output for `../control-v1/TEST-ONLY-identity.json` and a 32-byte zero challenge.
All keys and the challenge are public test data. Never enroll this identity.
No new private fixture keys are added and the immutable control-v1 corpus is unchanged.

Python `tests/test_android_control_identity.py` recomputes and verifies the proof.
Java `ControlIdentityTest` requires exactly the same public fields and Ed25519 signature.
The proof authorizes no enrollment by itself: the server still validates invitation,
entitlement and the live, single-use challenge.
