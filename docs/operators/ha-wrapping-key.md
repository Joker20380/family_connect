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

The current HA continuation already has a generated candidate. **Do not generate another key.**
The following preparation command is only for a genuinely new installation with no existing entry:

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

The qualified selective CLI workflow is `scripts.ha_wrapping_activate`: local confirmation requires
saving/closing KeePassXC, then only the existing HA attachment is added. An encrypted working-before
backup and immutable phases are retained. Existing UUIDs, values, attachments and history are checked
in memory; attachment references use content rather than export-local numeric IDs. A real HA consumer
readback is required. Never replace the working vault wholesale with a stale candidate.

Current local operation `ha-activation-20261127-02` reached add/import, then failed its original
comparison. Do **not** invoke `activate` or `prepare` again for it. Its read-only reconciliation is:

```sh
python3 -m scripts.ha_wrapping_activate --reconcile \
  --candidate "$HOME/.local/share/family-connect-vault/ha-candidate-20261127-01/Family-Connect.kdbx" \
  --working "$HOME/.local/share/family-connect-vault/Family-Connect.kdbx" \
  --journal "$HOME/.local/share/family-connect-vault/ha-activation-20261127-02"
```

This performs no vault write or new key generation. A failed native read is recorded separately
from the first comparison refusal and is not automatically retried. It does not prove a wrong
password, damaged database or changed secret. Resolve local unlock/read access using the native
dialog before another bounded read. Secret contents are never printed. A `reconciled.json` plus
real-consumer PASS is required before claiming activation; it still does not prove external custody.

Joker remains responsible for signer/pins/floors; ciphertext destination remains
NL2 `/opt/apps/family_connect/ha-recovery/`. External custody and access after laptop loss are
separate unverified requirements. Vault preparation does not close HA-02 or source-host-free restore.
