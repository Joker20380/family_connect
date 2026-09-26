package com.familyconnect.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.*;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

/** App-private no-backup storage. Caller must wipe returned key after Store closes.
 * One app process owns this vault; Keystore errors never silently rotate identity.
 */
final class ChatKeyVault {
    private static final String ALIAS="family-connect-chat-store-v1";
    private static final Object LOCK=new Object();
    private final AtomicFile file;
    ChatKeyVault(Context context) {
        file=new AtomicFile(new File(context.getNoBackupFilesDir(),"chat-store-key.enc"));
    }
    boolean hasState() throws Exception {
        synchronized (LOCK) {
            KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null);
            return keys.containsAlias(ALIAS) || file.getBaseFile().exists()
                || new File(file.getBaseFile()+".bak").exists()
                || new File(file.getBaseFile()+".new").exists();
        }
    }
    byte[] load() throws Exception {
        synchronized(LOCK) {
            KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
            if(!keys.containsAlias(ALIAS))throw new IOException("Chat wrapping key unavailable");
            byte[] raw;
            try(InputStream input=file.openRead()) {
                raw=new byte[ChatKeyEnvelope.SIZE];int count=0,n;
                while(count<raw.length&&(n=input.read(raw,count,raw.length-count))!=-1)count+=n;
                if(count!=raw.length||input.read()!=-1)throw new IOException("Invalid chat key file");
            }
            return ChatKeyEnvelope.open((SecretKey)keys.getKey(ALIAS,null),raw);
        }
    }
    /** Explicit first enrollment only. Missing/corrupt existing state is an error. */
    byte[] create() throws Exception {
        synchronized(LOCK) {
            KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
            if(keys.containsAlias(ALIAS)||file.getBaseFile().exists()
                    ||new File(file.getBaseFile()+".bak").exists()
                    ||new File(file.getBaseFile()+".new").exists())
                throw new IOException("Chat key enrollment already exists");
            KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
            SecretKey wrapping=generator.generateKey();
            byte[] secret=new byte[32];new SecureRandom().nextBytes(secret);
            FileOutputStream output=null;
            try {
                byte[] encrypted=ChatKeyEnvelope.seal(wrapping,secret);
                output=file.startWrite();output.write(encrypted);file.finishWrite(output);
                return secret;
            } catch(Exception failure) {
                if(output!=null)file.failWrite(output);
                Arrays.fill(secret,(byte)0);
                // Retain orphan alias: explicit recovery, never implicit regeneration.
                throw failure;
            }
        }
    }
}
