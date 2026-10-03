package com.familyconnect.app;

import android.content.*;
import android.database.*;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;

public final class DiagnosticsProvider extends ContentProvider {
    @Override public boolean onCreate(){return true;}
    private File file(Uri uri)throws FileNotFoundException{
        String name=uri.getLastPathSegment();
        if(!"content".equals(uri.getScheme())||!(getContext().getPackageName()+".diagnostics").equals(uri.getAuthority())||uri.getPathSegments().size()!=1||name==null||!name.matches("diagnostics-[0-9a-f]{32}\\.json")||uri.getQuery()!=null||uri.getFragment()!=null)throw new FileNotFoundException();
        File result=new File(getContext().getCacheDir(),name);
        if(!result.isFile()||result.length()>256*1024||System.currentTimeMillis()-result.lastModified()>3600000)throw new FileNotFoundException();return result;
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{if(!"r".equals(mode))throw new FileNotFoundException();return ParcelFileDescriptor.open(file(uri),ParcelFileDescriptor.MODE_READ_ONLY);}
    @Override public String getType(Uri uri){return "application/json";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){
        try{File result=file(uri);MatrixCursor cursor=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});cursor.addRow(new Object[]{"FamilyConnect-diagnostics.json",result.length()});return cursor;}catch(FileNotFoundException missing){return null;}
    }
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}
    @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException();}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args){throw new UnsupportedOperationException();}
}
