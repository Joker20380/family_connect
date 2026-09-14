package com.familyconnect.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.*;
import java.security.KeyStore;
import java.util.Arrays;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

/** Single app process. Explicit enrollment; interrupted/corrupt state never rotates keys. */
final class ControlIdentityVault {
    private static final String ALIAS = "family-connect-control-identity-v1";
    private static final Object LOCK = new Object();
    private final AtomicFile file;
    ControlIdentityVault(Context context) {
        file = new AtomicFile(new File(context.getNoBackupFilesDir(), "control-identity.enc"));
    }
    private static KeyStore keys() throws Exception {
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null); return keys;
    }
    ControlIdentity load() throws Exception {
        synchronized (LOCK) {
            KeyStore keys = keys();
            if (!keys.containsAlias(ALIAS)) throw new IOException("Control identity wrapping key unavailable");
            byte[] encrypted = new byte[ControlIdentityEnvelope.SIZE];
            try (InputStream input = file.openRead()) {
                int count = 0, n;
                while (count < encrypted.length && (n = input.read(encrypted, count, encrypted.length-count)) != -1) count += n;
                if (count != encrypted.length || input.read() != -1) throw new IOException("Invalid control identity file");
            }
            byte[] material = ControlIdentityEnvelope.open((SecretKey) keys.getKey(ALIAS, null), encrypted);
            try { return ControlIdentity.restore(material); }
            finally { Arrays.fill(material, (byte) 0); }
        }
    }
    ControlIdentity create() throws Exception {
        synchronized (LOCK) {
            KeyStore keys = keys();
            if (keys.containsAlias(ALIAS) || file.getBaseFile().exists()
                    || new File(file.getBaseFile()+".bak").exists() || new File(file.getBaseFile()+".new").exists())
                throw new IOException("Control identity enrollment already exists");
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
            SecretKey wrapping = generator.generateKey();
            ControlIdentity identity = ControlIdentity.generate(); byte[] material = identity.material();
            FileOutputStream output = null;
            try {
                byte[] encrypted = ControlIdentityEnvelope.seal(wrapping, material);
                output = file.startWrite(); output.write(encrypted); file.finishWrite(output); output = null;
                // AtomicFile logs some fsync/rename failures. Read back before exposing new identity.
                try (ControlIdentity persisted = load()) {
                    if (!identity.reference().equals(persisted.reference()) || !identity.wireguardPublicKey().equals(persisted.wireguardPublicKey()))
                        throw new IOException("Control identity persistence failed");
                }
                return identity;
            } catch (Exception failure) {
                identity.close(); if (output != null) file.failWrite(output);
                // Keep orphan alias for explicit recovery; never implicitly re-enroll.
                throw failure;
            } finally { Arrays.fill(material, (byte) 0); }
        }
    }
}
