CREATE TABLE provisioning_challenges (
    nonce_hash TEXT PRIMARY KEY,
    device_identity TEXT NOT NULL REFERENCES devices(identity),
    public_identity TEXT NOT NULL,
    wireguard_public_key TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    consumed_at INTEGER
);
CREATE INDEX provisioning_challenge_device ON provisioning_challenges(device_identity, expires_at);
CREATE TABLE provisioning_versions (
    device_identity TEXT NOT NULL REFERENCES devices(identity),
    revision INTEGER NOT NULL CHECK(revision > 0),
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id),
    entitlement_revision INTEGER NOT NULL CHECK(entitlement_revision > 0),
    wireguard_public_key TEXT NOT NULL,
    issued_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    envelope BLOB NOT NULL,
    PRIMARY KEY(device_identity, revision)
);
PRAGMA user_version = 2;
