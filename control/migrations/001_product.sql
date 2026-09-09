-- SQLite, single-host product-plane pilot. Never applied to the lab state files.
CREATE TABLE families (
    id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL
);
CREATE TABLE entitlements (
    id TEXT PRIMARY KEY,
    family_id TEXT NOT NULL UNIQUE REFERENCES families(id),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0),
    expires_at INTEGER NOT NULL,
    device_limit INTEGER NOT NULL CHECK(device_limit BETWEEN 1 AND 100),
    revoked_at INTEGER
);
CREATE TABLE invitations (
    id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id),
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    max_uses INTEGER NOT NULL CHECK(max_uses BETWEEN 1 AND 100),
    uses INTEGER NOT NULL DEFAULT 0 CHECK(uses >= 0 AND uses <= max_uses),
    revoked_at INTEGER
);
CREATE TABLE challenges (
    nonce_hash TEXT PRIMARY KEY,
    invitation_id TEXT NOT NULL REFERENCES invitations(id),
    public_identity TEXT NOT NULL,
    wireguard_public_key TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    consumed_at INTEGER
);
CREATE INDEX challenge_invitation ON challenges(invitation_id, expires_at);
CREATE TABLE devices (
    identity TEXT PRIMARY KEY,
    public_identity TEXT NOT NULL UNIQUE,
    created_at INTEGER NOT NULL,
    revoked_at INTEGER
);
CREATE TABLE device_entitlements (
    device_identity TEXT PRIMARY KEY REFERENCES devices(identity),
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id),
    joined_at INTEGER NOT NULL
);
CREATE INDEX entitlement_devices ON device_entitlements(entitlement_id);
CREATE TABLE transport_keys (
    id TEXT PRIMARY KEY,
    device_identity TEXT NOT NULL REFERENCES devices(identity),
    transport TEXT NOT NULL CHECK(transport = 'wireguard'),
    public_key TEXT NOT NULL UNIQUE,
    registered_at INTEGER NOT NULL,
    revoked_at INTEGER,
    UNIQUE(device_identity, transport)
);
CREATE TABLE product_audit (
    id INTEGER PRIMARY KEY,
    event TEXT NOT NULL CHECK(event IN ('entitlement_created', 'invitation_created',
        'device_enrolled', 'device_revoked', 'entitlement_revoked', 'invitation_revoked')),
    subject_id TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
PRAGMA user_version = 1;
