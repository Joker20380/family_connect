package com.familyconnect.app;

import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import java.io.*;

public final class OwnerSupportProvider extends ContentProvider {
    private void authorize(){if(!SupportAutomation.ACCESS.allows(Binder.getCallingUid(),SystemClock.elapsedRealtime()))throw new SecurityException("Owner USB support disabled");}
    @Override public boolean onCreate(){return true;}
    @Override public Bundle call(String method,String argument,Bundle extras){
        authorize();long token=Binder.clearCallingIdentity();
        try{return SupportAutomation.command(getContext(),method,argument);}finally{Binder.restoreCallingIdentity(token);}
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        authorize();if(!"r".equals(mode)||!"/snapshot".equals(uri.getPath())||uri.getQuery()!=null||uri.getFragment()!=null)throw new FileNotFoundException();
        long token=Binder.clearCallingIdentity();
        try{
            byte[] raw=Diagnostics.supportSnapshot(getContext()).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
            if(raw.length>DiagnosticRing.RECORD_LIMIT)throw new FileNotFoundException("Snapshot bound");
            File file=new File(getContext().getCacheDir(),"owner-support-snapshot.json");
            synchronized(OwnerSupportProvider.class){
                if(file.exists()&&!file.delete())throw new IOException("Snapshot cleanup");
                try(FileOutputStream output=new FileOutputStream(file)){output.write(raw);}
                ParcelFileDescriptor descriptor=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
                if(!file.delete()){descriptor.close();throw new IOException("Snapshot unlink");}return descriptor;
            }
        }catch(IOException failure){throw new FileNotFoundException("Snapshot unavailable");}finally{Binder.restoreCallingIdentity(token);}
    }
    @Override public String getType(Uri uri){authorize();return "application/json";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){authorize();return null;}
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args){throw new UnsupportedOperationException();}
    @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException();}
}
