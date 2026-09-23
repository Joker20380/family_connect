package com.familyconnect.app;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AppUpdateRuntimeTest {
    @org.junit.Before public void friendsVariantOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }
    private Context context(){return InstrumentationRegistry.getInstrumentation().getTargetContext();}
    private AppUpdate metadata(File file)throws Exception{
        android.content.pm.PackageInfo info=context().getPackageManager().getPackageInfo(context().getPackageName(),0);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)digest.update(b,0,n);}
        String json="{\"schema\":1,\"package\":\"com.familyconnect.app.friends\",\"abi\":\"arm64-v8a\",\"version_code\":"+info.versionCode+",\"version\":\""+info.versionName+"\",\"size\":"+file.length()+",\"sha256\":\""+AppUpdate.hex(digest.digest())+"\",\"url\":\""+AppUpdate.BASE+"/downloads/FamilyConnect-Test-"+info.versionName+".apk\"}";
        return AppUpdate.parse(json.getBytes(StandardCharsets.UTF_8));
    }
    @Test public void verifiesInstalledSignerAndRejectsDowngradeAndInvalidArchive()throws Exception{
        Context c=context();File source=new File(c.getApplicationInfo().sourceDir);AppUpdate update=metadata(source);
        AppUpdateUi.verifyApk(c,source,update,update.code-1);
        try{AppUpdateUi.verifyApk(c,source,update,update.code);fail("Same version accepted");}catch(SecurityException expected){}
        File invalid=File.createTempFile("invalid-update-",".apk",c.getCacheDir());try{try(FileOutputStream out=new FileOutputStream(invalid)){out.write(new byte[2048]);}try{AppUpdateUi.verifyApk(c,invalid,update,update.code-1);fail("Invalid archive accepted");}catch(SecurityException expected){}}finally{invalid.delete();}
        File foreign=new File(InstrumentationRegistry.getInstrumentation().getContext().getApplicationInfo().sourceDir);
        try{AppUpdateUi.verifyApk(c,foreign,update,update.code-1);fail("Wrong package accepted");}catch(SecurityException expected){}
    }
    @Test public void providerOnlyAllowsExactReadOnlyCacheApk()throws Exception{
        Context c=context();String name="update-"+new String(new char[64]).replace('\0','a')+".apk";File file=new File(c.getCacheDir(),name);try{
            try(FileOutputStream out=new FileOutputStream(file)){out.write(new byte[]{80,75,3,4});}
            Uri uri=Uri.parse("content://"+c.getPackageName()+".updates/"+name);
            try(ParcelFileDescriptor fd=c.getContentResolver().openFileDescriptor(uri,"r")){assertNotNull(fd);assertEquals(4,fd.getStatSize());}
            try{c.getContentResolver().openFileDescriptor(uri,"w");fail("Write accepted");}catch(FileNotFoundException expected){}
            try{c.getContentResolver().openFileDescriptor(Uri.parse("content://"+c.getPackageName()+".updates/../files/identity"),"r");fail("Traversal accepted");}catch(FileNotFoundException expected){}
        }finally{file.delete();}
    }
    @Test public void rejectsSamePackageWithUntrustedSigner()throws Exception{
        org.junit.Assume.assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcLiveUpdateCheck")));
        File file=new File(context().getExternalFilesDir(null),"wrong-signer.apk");assertTrue("Test-only signed fixture required",file.isFile());AppUpdate update=metadata(new File(context().getApplicationInfo().sourceDir));
        try{AppUpdateUi.verifyApk(context(),file,update,update.code-1);fail("Untrusted signer accepted");}catch(SecurityException expected){assertEquals("APK signer",expected.getMessage());}
    }
    @Test public void downloadsPublishedApkChecksHashAndBlocksReinstall()throws Exception{
        org.junit.Assume.assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcLiveUpdateCheck")));
        AppUpdate update=AppUpdate.check();File file=File.createTempFile("download-check-",".apk",context().getCacheDir());javax.net.ssl.HttpsURLConnection connection=AppUpdate.open(update.url);
        try{try(InputStream in=connection.getInputStream();OutputStream out=new FileOutputStream(file)){update.receive(in,out,p->{});}
            AppUpdateUi.verifyApk(context(),file,update,update.code-1);
            try{AppUpdateUi.verifyApk(context(),file,update,update.code);fail("Reinstall/downgrade accepted");}catch(SecurityException expected){}
        }finally{connection.disconnect();file.delete();}
    }
    private Button button(View view,String text){if(view instanceof Button&&text.contentEquals(((Button)view).getText()))return (Button)view;if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){Button b=button(((ViewGroup)view).getChildAt(i),text);if(b!=null)return b;}return null;}
    private boolean contains(View view,String text){if(view instanceof TextView&&text.contentEquals(((TextView)view).getText()))return true;if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)if(contains(((ViewGroup)view).getChildAt(i),text))return true;return false;}
    @Test public void settingsCheckUsesLiveCatalogAndKeepsNavigation()throws Exception{
        org.junit.Assume.assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcLiveUpdateCheck")));
        Instrumentation ins=InstrumentationRegistry.getInstrumentation();Context c=context();
        try(ParcelFileDescriptor command=ins.getUiAutomation().executeShellCommand("am start -W -n "+c.getPackageName()+"/com.familyconnect.app.FriendsActivity")){try(InputStream in=new FileInputStream(command.getFileDescriptor())){while(in.read()!=-1){}}}
        SystemClock.sleep(1000);AtomicReference<View> page=new AtomicReference<>();
        ins.runOnMainSync(()->{try{
            FriendsActivity a=(FriendsActivity)ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED).iterator().next();a.navigate(3);
            View view=a.getWindow().getDecorView();page.set(view);Button check=button(view,c.getString(R.string.update_check));assertNotNull(check);check.performClick();
        }catch(Exception e){throw new AssertionError(e);}});
        long until=SystemClock.elapsedRealtime()+25000;AtomicReference<Boolean> done=new AtomicReference<>(false);
        while(SystemClock.elapsedRealtime()<until){ins.runOnMainSync(()->done.set(contains(page.get(),c.getString(R.string.update_current))));if(done.get())break;SystemClock.sleep(200);}
        assertTrue("Live check should report current version",done.get());
        ins.runOnMainSync(()->{View view=page.get();Bitmap image=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(image));File dir=c.getExternalFilesDir("ui-acceptance");try(FileOutputStream out=new FileOutputStream(new File(dir,"settings-update.png"))){image.compress(Bitmap.CompressFormat.PNG,100,out);}catch(Exception e){throw new AssertionError(e);}finally{image.recycle();}});
    }
}
