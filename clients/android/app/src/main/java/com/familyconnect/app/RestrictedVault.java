package com.familyconnect.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.*;
import java.security.KeyStore;
import java.util.Arrays;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import java.nio.charset.StandardCharsets;

final class RestrictedVault implements RestrictedCache.Storage {
    static final Object LOCK=new Object();
    private final String alias;
    private final byte[] aad;
    private final AtomicFile file;
    RestrictedVault(Context context){this(context,null);}
    RestrictedVault(Context context,String gateway){
        String suffix=RestrictedGateway.namespace(gateway);
        alias="family-connect-restricted-readiness-v1"+suffix;aad=alias.getBytes(StandardCharsets.US_ASCII);
        file=new AtomicFile(new File(context.getNoBackupFilesDir(),"restricted-readiness"+suffix+".enc"));
    }
    private SecretKey key(boolean create)throws Exception{
        KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
        if(!keys.containsAlias(alias)){
            if(!create||file.getBaseFile().exists()||new File(file.getBaseFile()+".bak").exists()||new File(file.getBaseFile()+".new").exists())throw new IOException("Readiness key unavailable");
            KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());generator.generateKey();
        }
        return (SecretKey)keys.getKey(alias,null);
    }
    public byte[] read()throws Exception{
        synchronized(LOCK){
            if(!file.getBaseFile().exists()&&!new File(file.getBaseFile()+".bak").exists()) {
                KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
                if(keys.containsAlias(alias)||new File(file.getBaseFile()+".new").exists())throw new IOException("Readiness recovery required");return null;
            }
            byte[] raw;
            try(InputStream input=file.openRead();ByteArrayOutputStream out=new ByteArrayOutputStream()){
                byte[] buffer=new byte[4096];int count;while((count=input.read(buffer))!=-1){if(out.size()+count>70029)throw new IOException("Readiness bound");out.write(buffer,0,count);}raw=out.toByteArray();
            }
            if(raw.length<30||raw[0]!=1)throw new IOException("Readiness envelope");
            Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key(false),new GCMParameterSpec(128,raw,1,12));cipher.updateAAD(aad);return cipher.doFinal(raw,13,raw.length-13);
        }
    }
    public void write(byte[] raw)throws Exception{
        synchronized(LOCK){
            if(raw.length==0||raw.length>70000)throw new IOException("Readiness bound");
            read();Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key(true));cipher.updateAAD(aad);
            byte[] iv=cipher.getIV(),encrypted=cipher.doFinal(raw);if(iv.length!=12)throw new IOException("Readiness nonce");FileOutputStream output=null;
            try{output=file.startWrite();output.write(1);output.write(iv);output.write(encrypted);file.finishWrite(output);output=null;
                byte[] persisted;try{persisted=read();}catch(Exception failure){throw new RestrictedCache.PersistenceFailure();}
                try{if(!Arrays.equals(raw,persisted))throw new RestrictedCache.PersistenceFailure();}finally{if(persisted!=null)Arrays.fill(persisted,(byte)0);}
            }catch(Exception failure){if(output!=null)file.failWrite(output);throw failure;}
        }
    }
}
