# Fleet contracts v1

The executable strict schema is [`contracts.py`](../contracts.py): `FIELDS`, `typed`,
`validate` and `inventory`. It uses only the Python standard library. Every field is
required (nullable fields explicitly end in `?`); unknown keys, duplicate JSON keys,
nonfinite numbers, booleans masquerading as integers and invalid bindings fail closed.
`transition` is the only lifecycle graph. No `PROVISIONING` state or STAGED→ACTIVE edge.

Physical deployment identity is separate from client transport keys and logical routes.
The inventory carries public digests only, never credentials, private paths or journals.
Artifacts must be registered before either desired or actual bundle references resolve.
One logical gateway has one active instance; active deployment identities are exclusive.
Verification and activation need health acceptance in addition to a legal graph edge.
