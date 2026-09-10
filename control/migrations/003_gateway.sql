CREATE TABLE peer_deployments (
    device_identity TEXT PRIMARY KEY REFERENCES devices(identity),
    network TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);
CREATE TABLE peer_allocations (
    address TEXT PRIMARY KEY,
    device_identity TEXT NOT NULL REFERENCES devices(identity)
);
CREATE TABLE peer_outbox (
    device_identity TEXT NOT NULL REFERENCES peer_deployments(device_identity),
    gateway_id TEXT NOT NULL,
    public_key TEXT NOT NULL,
    desired TEXT NOT NULL CHECK(desired IN ('present','absent')),
    applied TEXT CHECK(applied IN ('present','absent')),
    attempts INTEGER NOT NULL DEFAULT 0,
    retry_at INTEGER NOT NULL DEFAULT 0,
    checked_at INTEGER,
    error TEXT CHECK(error IS NULL OR error = 'GATEWAY_UNAVAILABLE'),
    PRIMARY KEY(device_identity,gateway_id)
);
PRAGMA user_version = 3;
