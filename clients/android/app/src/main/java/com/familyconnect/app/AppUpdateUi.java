package com.familyconnect.app;

import android.app.Activity;
import android.content.*;
import android.content.pm.*;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import javax.net.ssl.HttpsURLConnection;

final class AppUpdateUi {
    private final Activity activity;private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private volatile boolean closed,cancelled;private boolean busy;private AppUpdate candidate;private File ready;
    private TextView status;private Button action,cancel;private ProgressBar progress;private int message=R.string.update_hint,percent;
    AppUpdateUi(Activity activity){this.activity=activity;}
    void attach(LinearLayout panel){
        status=TerminalUi.label(panel,activity.getString(message),12,TerminalUi.MUTED);
        progress=new ProgressBar(activity,null,android.R.attr.progressBarStyleHorizontal);progress.setMax(100);progress.setProgressTintList(android.content.res.ColorStateList.valueOf(TerminalUi.MINT));panel.addView(progress,new LinearLayout.LayoutParams(-1,TerminalUi.dp(activity,6)));
        action=TerminalUi.button(panel,R.string.update_check,this::act);cancel=TerminalUi.button(panel,R.string.update_cancel,()->{cancelled=true;});render();
    }
    void render(){if(status==null||closed)return;String text=activity.getString(message);if(message==R.string.update_available&&candidate!=null)text=activity.getString(R.string.update_available,candidate.version,(int)Math.ceil(candidate.size/1e6));else if(message==R.string.update_downloading)text=activity.getString(R.string.update_downloading,percent);status.setText(text);action.setEnabled(!busy);action.setText(ready!=null?R.string.update_install:candidate!=null?R.string.update_download:R.string.update_check);cancel.setVisibility(busy?android.view.View.VISIBLE:android.view.View.GONE);progress.setVisibility(busy?android.view.View.VISIBLE:android.view.View.GONE);progress.setIndeterminate(busy&&message!=R.string.update_downloading);progress.setProgress(percent);}
    private void post(Runnable action){main.post(()->{if(!closed)action.run();});}
    private void act(){if(busy)return;if(ready!=null){install();return;}if(candidate==null)check();else download();}
    private long installedCode()throws Exception{PackageInfo p=activity.getPackageManager().getPackageInfo(activity.getPackageName(),0);return code(p);}
    private static long code(PackageInfo p){return Build.VERSION.SDK_INT>=28?p.getLongVersionCode():p.versionCode;}
    private void check(){busy=true;cancelled=false;message=R.string.update_checking;render();worker.execute(()->{
        try{AppUpdate found=AppUpdate.check();long current=installedCode();boolean supported=Arrays.asList(Build.SUPPORTED_ABIS).contains("arm64-v8a")&&activity.getPackageName().equals("com.familyconnect.app.friends");post(()->{busy=false;if(cancelled){message=R.string.update_cancelled;}else if(!supported){message=R.string.update_unsupported;}else if(found.code<=current){message=R.string.update_current;}else{candidate=found;message=R.string.update_available;}render();});}
        catch(Exception e){post(()->{busy=false;message=cancelled?R.string.update_cancelled:R.string.update_check_failed;render();});}
    });}
    private void download(){busy=true;cancelled=false;percent=0;message=R.string.update_downloading;render();AppUpdate update=candidate;worker.execute(()->{
        File part=null;HttpsURLConnection connection=null;
        try{
            part=File.createTempFile("update-",".part",activity.getCacheDir());connection=AppUpdate.open(update.url);
            long length=connection.getContentLengthLong();if(length!=-1&&length!=update.size)throw new IOException();
            try(InputStream in=connection.getInputStream();FileOutputStream out=new FileOutputStream(part)){
                update.receive(in,out,p->{if(cancelled||closed)throw new InterruptedIOException();post(()->{percent=p;render();});});out.getFD().sync();
            }
            if(cancelled||closed)throw new InterruptedIOException();verifyApk(activity,part,update,installedCode());
            File target=new File(activity.getCacheDir(),"update-"+update.sha256+".apk");if(!part.renameTo(target))throw new IOException();part=null;
            post(()->{busy=false;ready=target;message=R.string.update_ready;render();});
        }catch(Exception e){post(()->{busy=false;message=cancelled?R.string.update_cancelled:R.string.update_download_failed;render();});}
        finally{if(connection!=null)connection.disconnect();if(part!=null)part.delete();}
    });}
    static void verifyApk(Context context,File file,AppUpdate update,long installed)throws Exception{
        PackageManager pm=context.getPackageManager();int flags=Build.VERSION.SDK_INT>=28?PackageManager.GET_SIGNING_CERTIFICATES:PackageManager.GET_SIGNATURES;
        PackageInfo apk=pm.getPackageArchiveInfo(file.getAbsolutePath(),flags),own=pm.getPackageInfo(context.getPackageName(),flags);
        if(apk==null||!context.getPackageName().equals(apk.packageName)||code(apk)!=update.code||code(apk)<=installed||!update.version.equals(apk.versionName))throw new SecurityException("APK identity");
        android.content.pm.Signature[] a=signatures(apk),b=signatures(own);
        if(a==null||b==null||a.length!=1||b.length!=1||!a[0].equals(b[0]))throw new SecurityException("APK signer");
    }
    private static android.content.pm.Signature[] signatures(PackageInfo p){return Build.VERSION.SDK_INT>=28?(p.signingInfo==null?null:p.signingInfo.getApkContentsSigners()):p.signatures;}
    private void install(){
        if(!ConnectionService.status.equals("off")){message=R.string.update_disconnect;render();return;}
        if(!ready.isFile()){ready=null;message=R.string.update_download_failed;render();return;}
        try{
            if(!activity.getPackageManager().canRequestPackageInstalls()){
                message=R.string.update_allow;render();activity.startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,Uri.parse("package:"+activity.getPackageName())));return;
            }
            Uri uri=new Uri.Builder().scheme("content").authority(activity.getPackageName()+".updates").appendPath(ready.getName()).build();
            Intent intent=new Intent(Intent.ACTION_INSTALL_PACKAGE).setDataAndType(uri,"application/vnd.android.package-archive").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);intent.setClipData(ClipData.newRawUri("APK",uri));activity.startActivity(intent);message=R.string.update_ready;render();
        }catch(Exception e){message=R.string.update_install_failed;render();}
    }
    void close(){closed=true;cancelled=true;worker.shutdownNow();main.removeCallbacksAndMessages(null);}
}
