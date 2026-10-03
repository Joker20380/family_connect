package com.familyconnect.app;

import android.content.Context;
import android.content.pm.ProviderInfo;
import android.net.Uri;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class DiagnosticsProviderTest {
    @Test public void onlyBoundedFreshReadOnlyBundleIsAccessible()throws Exception{
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        DiagnosticsProvider provider=new DiagnosticsProvider();ProviderInfo info=new ProviderInfo();info.authority=context.getPackageName()+".diagnostics";provider.attachInfo(context,info);
        String name="diagnostics-"+java.util.UUID.randomUUID().toString().replace("-","")+".json";
        File file=new File(context.getCacheDir(),name);Uri uri=Uri.parse("content://"+info.authority+"/"+name);
        try{
            try(FileOutputStream stream=new FileOutputStream(file)){stream.write("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));}
            try(android.os.ParcelFileDescriptor descriptor=provider.openFile(uri,"r")){assertNotNull(descriptor);}
            for(String suffix:new String[]{"?other=1","#fragment","/extra"}){
                try{provider.openFile(Uri.parse(uri+suffix),"r");fail();}catch(FileNotFoundException expected){}
            }
            try{provider.openFile(uri,"w");fail();}catch(FileNotFoundException expected){}
            try{provider.openFile(Uri.parse("content://"+info.authority+"/../identity"),"r");fail();}catch(FileNotFoundException expected){}
            assertTrue(file.setLastModified(System.currentTimeMillis()-3600001));
            try{provider.openFile(uri,"r");fail();}catch(FileNotFoundException expected){}
            try(RandomAccessFile output=new RandomAccessFile(file,"rw")){output.setLength(DiagnosticRing.EXPORT_LIMIT);}
            assertTrue(file.setLastModified(System.currentTimeMillis()));
            try(android.os.ParcelFileDescriptor descriptor=provider.openFile(uri,"r")){assertNotNull(descriptor);}
            try(RandomAccessFile output=new RandomAccessFile(file,"rw")){output.setLength(DiagnosticRing.EXPORT_LIMIT+1);}
            try{provider.openFile(uri,"r");fail();}catch(FileNotFoundException expected){}
        }finally{file.delete();}
    }
}
