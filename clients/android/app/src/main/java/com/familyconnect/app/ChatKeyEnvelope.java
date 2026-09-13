package com.familyconnect.app;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Fixed-size encrypted Store key; never a VPN profile or chat identity envelope. */
final class ChatKeyEnvelope {
    static final int SIZE=61;
    private static final byte[] AAD="family-connect/chat-store-key/v1".getBytes(StandardCharsets.US_ASCII);
    static byte[] seal(SecretKey wrappingKey, byte[] storeKey) throws GeneralSecurityException {
        if(storeKey.length!=32)throw new GeneralSecurityException("Invalid chat key length");
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE,wrappingKey);cipher.updateAAD(AAD);
        byte[] iv=cipher.getIV();
        if(iv.length!=12)throw new GeneralSecurityException("Unexpected nonce size");
        byte[] encrypted=cipher.doFinal(storeKey);
        byte[] result=new byte[SIZE];result[0]=1;
        System.arraycopy(iv,0,result,1,12);System.arraycopy(encrypted,0,result,13,48);
        return result;
    }
    static byte[] open(SecretKey wrappingKey, byte[] envelope) throws GeneralSecurityException {
        if(envelope.length!=SIZE||envelope[0]!=1)throw new GeneralSecurityException("Invalid chat key envelope");
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE,wrappingKey,new GCMParameterSpec(128,envelope,1,12));
        cipher.updateAAD(AAD);
        return cipher.doFinal(envelope,13,48);
    }
}
