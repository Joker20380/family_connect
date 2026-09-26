package com.familyconnect.app;

import java.security.GeneralSecurityException;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/** AES-GCM callback for encrypted Store rows. No key getter or serialization. */
public final class ChatStoreCipher implements AutoCloseable {
    // A 128 KiB voice is stored as base64 audio plus hex signed bytes and a
    // persisted hex relay envelope. Bound the whole JSON row, not just audio.
    static final int MAX_RECORD_BYTES = 1024 * 1024;
    private byte[] key;

    ChatStoreCipher(byte[] secret) {
        if (secret == null || secret.length != 32) throw new IllegalArgumentException("Invalid chat key");
        key = secret.clone();
    }

    public synchronized byte[] encrypt(byte[] nonce, byte[] data, byte[] aad) throws GeneralSecurityException {
        return transform(Cipher.ENCRYPT_MODE, nonce, data, aad);
    }

    public synchronized byte[] decrypt(byte[] nonce, byte[] data, byte[] aad) throws GeneralSecurityException {
        return transform(Cipher.DECRYPT_MODE, nonce, data, aad);
    }

    private byte[] transform(int mode, byte[] nonce, byte[] data, byte[] aad) throws GeneralSecurityException {
        if (key == null) throw new GeneralSecurityException("Chat cipher closed");
        if (nonce == null || nonce.length != 12 || data == null || aad == null
                || aad.length == 0 || aad.length > 256
                || data.length > MAX_RECORD_BYTES + (mode == Cipher.DECRYPT_MODE ? 16 : 0)
                || (mode == Cipher.DECRYPT_MODE && data.length < 16))
            throw new GeneralSecurityException("Invalid chat record");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(mode, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, nonce));
        cipher.updateAAD(aad);
        return cipher.doFinal(data);
    }

    @Override public synchronized void close() {
        if (key != null) Arrays.fill(key, (byte) 0);
        key = null;
        // Provider/JNI temporary copies are not guaranteed to be zeroed.
    }
}
