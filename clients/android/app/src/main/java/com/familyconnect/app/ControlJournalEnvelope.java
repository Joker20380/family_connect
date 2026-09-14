package com.familyconnect.app;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class ControlJournalEnvelope {
    static final int OVERHEAD = 29;
    private static final byte[] AAD = "family-connect/control-journal/v1".getBytes(StandardCharsets.US_ASCII);
    static byte[] seal(SecretKey key, byte[] plain) throws GeneralSecurityException {
        if (plain.length == 0 || plain.length > ControlJournal.LIMIT) throw new GeneralSecurityException("Invalid journal size");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key); cipher.updateAAD(AAD);
        byte[] iv = cipher.getIV(); if (iv.length != 12) throw new GeneralSecurityException("Invalid journal nonce");
        byte[] encrypted = cipher.doFinal(plain), result = new byte[plain.length + OVERHEAD]; result[0] = 1;
        System.arraycopy(iv, 0, result, 1, 12); System.arraycopy(encrypted, 0, result, 13, encrypted.length); return result;
    }
    static byte[] open(SecretKey key, byte[] raw) throws GeneralSecurityException {
        if (raw.length <= OVERHEAD || raw.length > ControlJournal.LIMIT + OVERHEAD || raw[0] != 1)
            throw new GeneralSecurityException("Invalid journal envelope");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, raw, 1, 12)); cipher.updateAAD(AAD);
        return cipher.doFinal(raw, 13, raw.length - 13);
    }
}
