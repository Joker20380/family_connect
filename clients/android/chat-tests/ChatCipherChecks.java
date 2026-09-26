package com.familyconnect.app;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Arrays;

/** Same AES-GCM fixture as Python cryptography; no Android runtime dependency. */
public final class ChatCipherChecks {
    public static void main(String[] args) throws Exception {
        byte[] key = new byte[32], nonce = new byte[12];
        for (int i = 0; i < key.length; i++) key[i] = (byte) i;
        for (int i = 0; i < nonce.length; i++) nonce[i] = (byte) i;
        byte[] text = "Привет 🙂".getBytes(StandardCharsets.UTF_8);
        byte[] aad = "fc-chat-v1:meta".getBytes(StandardCharsets.UTF_8);
        byte[] expected = hex("979d079b155d12a95df446099119e7f401122ae76e1ee9b7a79a9727cca64570f5");
        ChatStoreCipher cipher = new ChatStoreCipher(key);
        Arrays.fill(key, (byte) 0); // Caller can wipe its buffer immediately.
        check(Arrays.equals(expected, cipher.encrypt(nonce, text, aad)));
        check(Arrays.equals(text, cipher.decrypt(nonce, expected, aad)));
        for (int i = 0; i < expected.length; i++) {
            byte[] damaged = expected.clone(); damaged[i] ^= 1;
            try { cipher.decrypt(nonce, damaged, aad); throw new AssertionError("Tamper accepted"); }
            catch (GeneralSecurityException correct) {}
        }
        try { cipher.decrypt(nonce, expected, new byte[] {1}); throw new AssertionError("Wrong AAD accepted"); }
        catch (GeneralSecurityException correct) {}
        for (int size : new int[] {700000, ChatStoreCipher.MAX_RECORD_BYTES}) {
            byte[] record = new byte[size];Arrays.fill(record,(byte)42);
            byte[] uniqueNonce = nonce.clone();uniqueNonce[0]=(byte)(size==700000?100:101);
            byte[] sealed = cipher.encrypt(uniqueNonce,record,aad);
            check(sealed.length==size+16);
            check(Arrays.equals(record,cipher.decrypt(uniqueNonce,sealed,aad)));
        }
        try { cipher.encrypt(nonce,new byte[ChatStoreCipher.MAX_RECORD_BYTES+1],aad);throw new AssertionError("Oversized row accepted"); }
        catch (GeneralSecurityException correct) {}
        try { cipher.decrypt(nonce,new byte[ChatStoreCipher.MAX_RECORD_BYTES+17],aad);throw new AssertionError("Oversized sealed row accepted"); }
        catch (GeneralSecurityException correct) {}
        cipher.close(); cipher.close();
        try { cipher.encrypt(nonce, text, aad); throw new AssertionError("Closed cipher accepted"); }
        catch (GeneralSecurityException correct) {}
        System.out.println("PASS: Python/Java AES-GCM fixture, UTF-8, key copy, tampering, AAD, closed cipher");
    }
    private static void check(boolean ok) { if (!ok) throw new AssertionError(); }
    private static byte[] hex(String text) {
        byte[] result = new byte[text.length()/2];
        for (int i=0; i<result.length; i++) result[i]=(byte)Integer.parseInt(text.substring(i*2,i*2+2),16);
        return result;
    }
}
