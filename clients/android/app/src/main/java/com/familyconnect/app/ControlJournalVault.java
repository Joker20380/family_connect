package com.familyconnect.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.*;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.util.Arrays;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

/** Atomic encrypted journal used by ConnectionService; no backups or implicit recreation.
 * See docs/managed-control-code-map.ru.md for identity, ownership and recovery boundaries.
 */
final class ControlJournalVault implements ControlJournal.Storage {
    private static final String ALIAS = "family-connect-control-journal-v1";
    private final AtomicFile file;
    ControlJournalVault(Context context) {
        file = new AtomicFile(new File(context.getNoBackupFilesDir(), "control-journal.enc"));
    }
    private static KeyStore keys() throws Exception {
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null); return keys;
    }
    private static SecretKey key() throws Exception {
        KeyStore keys = keys();
        if (!keys.containsAlias(ALIAS)) throw new IOException("Control journal wrapping key unavailable");
        return (SecretKey) keys.getKey(ALIAS, null);
    }
    public byte[] read() throws Exception {
        synchronized (ControlJournal.OWNER) {
            SecretKey key = key();
            try (InputStream input = file.openRead(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096]; int n;
                while ((n = input.read(buffer)) != -1) {
                    if (out.size() + n > ControlJournal.LIMIT + ControlJournalEnvelope.OVERHEAD) throw new IOException("Control journal too large");
                    out.write(buffer, 0, n);
                }
                return ControlJournalEnvelope.open(key, out.toByteArray());
            }
        }
    }
    public void create(byte[] raw) throws Exception {
        synchronized (ControlJournal.OWNER) {
            KeyStore keys = keys();
            if (keys.containsAlias(ALIAS) || file.getBaseFile().exists() || new File(file.getBaseFile()+".bak").exists() || new File(file.getBaseFile()+".new").exists())
                throw new IOException("Control journal already exists");
            if (raw.length == 0 || raw.length > ControlJournal.LIMIT) throw new IOException("Invalid control journal size");
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
            persist(generator.generateKey(), raw); // Retain alias on failure: explicit recovery required.
        }
    }
    public void write(byte[] raw) throws Exception {
        synchronized (ControlJournal.OWNER) {
            // Refuse missing/corrupt storage rather than silently resetting its replay floor.
            byte[] prior = read(); Arrays.fill(prior, (byte) 0); persist(key(), raw);
        }
    }
    private void persist(SecretKey key, byte[] raw) throws Exception {
        byte[] encrypted = ControlJournalEnvelope.seal(key, raw); FileOutputStream output = null;
        try {
            output = file.startWrite(); output.write(encrypted); file.finishWrite(output); output = null;
            byte[] persisted = read();
            try { if (!MessageDigest.isEqual(persisted, raw)) throw new IOException("Control journal persistence failed"); }
            finally { Arrays.fill(persisted, (byte) 0); }
        } catch (Exception failure) {
            if (output != null) file.failWrite(output); throw failure;
        }
    }
}
