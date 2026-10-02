package com.familyconnect.app;

import android.content.Context;
import android.util.AtomicFile;
import java.io.*;

final class ReadinessReceiptStore implements RestrictedCache.Storage {
    private final AtomicFile file;
    ReadinessReceiptStore(Context context){file=new AtomicFile(new File(context.getNoBackupFilesDir(),"restricted-readiness-result-v1.json"));}
    public byte[] read()throws Exception{
        synchronized(RestrictedVault.LOCK){
            try(InputStream input=file.openRead();ByteArrayOutputStream output=new ByteArrayOutputStream()){
                byte[] buffer=new byte[1024];int count;
                while((count=input.read(buffer))!=-1){if(output.size()+count>4096)throw new IOException("Receipt bound");output.write(buffer,0,count);}return output.toByteArray();
            }catch(FileNotFoundException missing){return null;}
        }
    }
    public void write(byte[] raw)throws Exception{
        synchronized(RestrictedVault.LOCK){
            if(raw.length==0||raw.length>4096)throw new IOException("Receipt bound");FileOutputStream output=null;
            try{output=file.startWrite();output.write(raw);output.getFD().sync();file.finishWrite(output);output=null;
                if(!java.util.Arrays.equals(raw,read()))throw new IOException("Receipt persistence");
            }catch(Exception failure){if(output!=null)file.failWrite(output);throw failure;}
        }
    }
}
