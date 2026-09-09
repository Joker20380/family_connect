package com.familyconnect.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.Arrays;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;

final class ProfileStore {
    private static final String ALIAS="family-connect-profile-v1";
    private final AtomicFile file;
    ProfileStore(Context context) {file=new AtomicFile(new File(context.getNoBackupFilesDir(),"profile.enc"));}
    boolean exists() {return file.getBaseFile().exists();}
    private javax.crypto.SecretKey key() throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");store.load(null);
        if(!store.containsAlias(ALIAS)) {
            KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());generator.generateKey();
        }
        return (javax.crypto.SecretKey)store.getKey(ALIAS,null);
    }
    void save(String profile) throws Exception {
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key());
        byte[] plaintext=profile.getBytes(StandardCharsets.UTF_8);
        byte[] encrypted;
        try {encrypted=cipher.doFinal(plaintext);}finally {Arrays.fill(plaintext,(byte)0);}
        FileOutputStream out=null;
        try {out=file.startWrite();out.write(1);out.write(cipher.getIV());out.write(encrypted);file.finishWrite(out);}
        catch(Exception e){if(out!=null)file.failWrite(out);throw e;}
    }
    String load() throws Exception {
        byte[] raw=file.readFully();if(raw.length<30||raw.length>ProfileValidator.LIMIT+64||raw[0]!=1)throw new IOException("Invalid encrypted profile");
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,raw,1,12));
        byte[] plaintext=cipher.doFinal(raw,13,raw.length-13);
        try{return new String(plaintext,StandardCharsets.UTF_8);}finally{Arrays.fill(plaintext,(byte)0);}
    }
    void clear() throws Exception {file.delete();KeyStore store=KeyStore.getInstance("AndroidKeyStore");store.load(null);store.deleteEntry(ALIAS);}
}
