package com.familyconnect.app;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Versioned local storage only; not a network configuration envelope. */
final class ControlIdentityEnvelope {
    static final int SIZE = 1 + 12 + ControlIdentity.SIZE + 16;
    private static final byte[] AAD = "family-connect/control-identity/v1".getBytes(StandardCharsets.US_ASCII);
    static byte[] seal(SecretKey key, byte[] material) throws GeneralSecurityException {
        if (material.length != ControlIdentity.SIZE) throw new GeneralSecurityException("Invalid identity length");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key); cipher.updateAAD(AAD);
        byte[] iv = cipher.getIV();
        if (iv.length != 12) throw new GeneralSecurityException("Invalid nonce length");
        byte[] encrypted = cipher.doFinal(material), result = new byte[SIZE]; result[0] = 1;
        System.arraycopy(iv, 0, result, 1, 12); System.arraycopy(encrypted, 0, result, 13, encrypted.length);
        return result;
    }
    static byte[] open(SecretKey key, byte[] envelope) throws GeneralSecurityException {
        if (envelope.length != SIZE || envelope[0] != 1) throw new GeneralSecurityException("Invalid identity envelope");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, envelope, 1, 12)); cipher.updateAAD(AAD);
        return cipher.doFinal(envelope, 13, SIZE - 13);
    }
}
