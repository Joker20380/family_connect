package com.familyconnect.app;

import android.content.*;
import android.database.*;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;

/** Grants the system installer read access to one verified APK, never app data. */
public final class UpdateApkProvider extends ContentProvider {
    @Override public boolean onCreate(){return true;}
    private File file(Uri uri)throws FileNotFoundException{
        String name=uri.getLastPathSegment();
        if(!"content".equals(uri.getScheme())||!(getContext().getPackageName()+".updates").equals(uri.getAuthority())||uri.getPathSegments().size()!=1||name==null||!name.matches("update-[0-9a-f]{64}\\.apk")||uri.getQuery()!=null)throw new FileNotFoundException();
        File f=new File(getContext().getCacheDir(),name);if(!f.isFile())throw new FileNotFoundException();return f;
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{if(!"r".equals(mode))throw new FileNotFoundException();return ParcelFileDescriptor.open(file(uri),ParcelFileDescriptor.MODE_READ_ONLY);}
    @Override public String getType(Uri uri){return "application/vnd.android.package-archive";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] args,String order){
        try{File f=file(uri);String[] columns=projection==null?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;MatrixCursor cursor=new MatrixCursor(columns);Object[] row=new Object[columns.length];for(int i=0;i<columns.length;i++){if(OpenableColumns.DISPLAY_NAME.equals(columns[i]))row[i]="FamilyConnect-update.apk";else if(OpenableColumns.SIZE.equals(columns[i]))row[i]=f.length();}cursor.addRow(row);return cursor;}catch(FileNotFoundException e){return null;}
    }
    @Override public Uri insert(Uri uri,ContentValues v){throw new UnsupportedOperationException();}
    @Override public int delete(Uri uri,String s,String[] a){throw new UnsupportedOperationException();}
    @Override public int update(Uri uri,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
}
