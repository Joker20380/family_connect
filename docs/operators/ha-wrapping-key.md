# Dedicated HA wrapping key in KeePassXC

This consumer is separate from all release/root signing keys. It uses the established
`vault_archive` attachment-to-memfd reader, **not** `signing_key.load` or Ed25519 conversion.
Unlock occurs only in the local Zenity dialog. Password/key bytes are not command arguments,
logs, Git content or stdout. Core dumps are disabled. Python memory is not a secure-erasure
guarantee; no plaintext key is intentionally persisted.

Exact contract:

- Database: `Family-Connect.kdbx` (default existing local vault directory).
- Entry: `HA custody encryption`, distinct from signing entries.
- Attachment: `recovery.tar.gz`; exact regular members `ha-custody/aes256gcm.raw` and
  `HA-ENCRYPTION.json`. Unknown/duplicate/link/oversized members refuse.
- Purpose: `family-connect/ha-custody-encryption/v1`; algorithm AES-256-GCM; exactly32 raw bytes.
- In-memory consumer: `scripts.ha_wrapping_key.load(vault)` returns the validated AES key.
  Read it before admission is closed; never wait for a password dialog inside a capture barrier.

Read-only verification of the dedicated entry:

```sh
python3 -m scripts.ha_wrapping_key check
```

If the dedicated entry is absent, prepare a new encrypted vault candidate:

```sh
python3 -m scripts.ha_wrapping_key prepare --destination /private/new-ha-vault-candidate
```

The destination must not exist. The original vault is copied as encrypted bytes into a0700
directory. After local unlock, KeePassXC creates the separate entry; OS CSPRNG generates32
bytes, and the attachment is passed through memfd, imported and independently exported/read
back. Existing same-name entries are never overwritten. The original vault is checked unchanged.
Failure leaves any encrypted candidate for inspection, never labels it activated, and never
deletes original data. A duplicate invocation needs explicit reconciliation/new destination.

**Activation remains local and explicit:** open the encrypted candidate in KeePassXC, review
the new entry and merge only it into the current vault using the normal application workflow;
save, then run `check` against the actual current vault. This tool deliberately does not replace
a possibly open/edited live vault. A prepared candidate is not an installed key or recovery kit.
Do not put a master password in a shell command, chat, environment variable or a file.

Joker remains responsible for signer/pins/floors; ciphertext destination remains
NL2 `/opt/apps/family_connect/ha-recovery/`. External custody and access after laptop loss are
separate unverified requirements. Vault preparation does not close HA-02 or source-host-free restore.
