package com.familyconnect.app;

import android.app.Activity;
import android.content.*;
import android.os.*;
import android.widget.*;
import com.google.gson.*;
import java.util.concurrent.*;

final class SupportAutomation {
    interface Host { String command(String method,String argument); }
    static final SupportAccess ACCESS=new SupportAccess();
    private static Host host;
    private static final SupportUploadSchedule UPLOAD=new SupportUploadSchedule();
    private static volatile String uploadState="OFF";
    private static volatile FriendsAccessAndroid request;
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    static void attach(Host current){host=current;}
    static void detach(){host=null;}
    static void controls(Activity activity,LinearLayout panel){
        Button usb=new Button(activity);usb.setText("USB: разрешить поддержку на 1 час / allow support for 1 hour");panel.addView(usb);
        usb.setOnClickListener(view->{
            if(ACCESS.active(SystemClock.elapsedRealtime())){ACCESS.disable();Toast.makeText(activity,"USB support OFF",Toast.LENGTH_SHORT).show();return;}
            new android.app.AlertDialog.Builder(activity).setTitle("USB support")
                .setMessage("Только доверенный ADB-компьютер: диагностика, подключение/отключение и P0/P1/P2 для новой сессии. Не root. На 1 час, до перезапуска приложения; повторное нажатие отключает.\nTrusted USB ADB only; no network remote control.")
                .setNegativeButton(android.R.string.cancel,null).setPositiveButton(android.R.string.ok,(dialog,which)->{ACCESS.enable(SystemClock.elapsedRealtime());Toast.makeText(activity,"USB support ON · 1h",Toast.LENGTH_LONG).show();}).show();
        });
        Switch online=new Switch(activity);online.setText("Онлайн-диагностика (7 дней) / Online diagnostics (7 days)");online.setChecked(consented(activity));panel.addView(online);
        online.setOnCheckedChangeListener((button,checked)->{
            if(!checked){activity.getSharedPreferences("support-upload",Context.MODE_PRIVATE).edit().remove("until").commit();FriendsAccessAndroid active=request;if(active!=null)active.cancel();uploadState="OFF";return;}
            new android.app.AlertDialog.Builder(activity).setTitle("Online diagnostics")
                .setMessage("Раз в минуту: версия, состояние VPN, случайный ID сессии и счётчики ошибок/байтов. Без сайтов, IP, сообщений, ключей и полных журналов. Привязка к Support ID. Только последний снимок, сервер до 7 дней; выключить здесь в любой момент. Не включает удалённое управление.\nLatest technical snapshot only; no traffic content. Opt-in expires in 7 days.")
                .setNegativeButton(android.R.string.cancel,(dialog,which)->online.setChecked(false)).setOnCancelListener(dialog->online.setChecked(false))
                .setPositiveButton(android.R.string.ok,(dialog,which)->{activity.getSharedPreferences("support-upload",Context.MODE_PRIVATE).edit().putLong("until",System.currentTimeMillis()+7L*86400000).commit();tick(activity);}).show();
        });
        TextView status=new TextView(activity);status.setText("Upload: "+uploadState+" · no VPN fallback");panel.addView(status);
    }
    static boolean consented(Context context){long remaining=context.getSharedPreferences("support-upload",Context.MODE_PRIVATE).getLong("until",0)-System.currentTimeMillis();return remaining>0&&remaining<=7L*86400000;}
    static Bundle command(Context context,String method,String argument){
        if(!java.util.Arrays.asList("status","connect","disconnect","profile","disable").contains(method))throw new IllegalArgumentException("Unsupported support operation");
        if("profile".equals(method)&&!java.util.Arrays.asList("P0","P1","P2").contains(argument))throw new IllegalArgumentException("Profile required");
        if(!"profile".equals(method)&&argument!=null)throw new IllegalArgumentException("Unexpected argument");
        Bundle result=new Bundle();
        if("disable".equals(method)){ACCESS.disable();result.putString("result","DISABLED");return result;}
        if("status".equals(method)){result.putString("result",ConnectionService.status);result.putString("upload",uploadState);return result;}
        FutureTask<String> task=new FutureTask<>(()->{
            if(!ACCESS.active(SystemClock.elapsedRealtime()))return "DISABLED";
            return host==null?"FOREGROUND_REQUIRED":host.command(method,argument);
        });MAIN.post(task);
        try{result.putString("result",task.get(3,TimeUnit.SECONDS));}
        catch(Exception failure){task.cancel(false);result.putString("result","UNKNOWN_READ_STATUS_BEFORE_RETRY");}
        return result;
    }
    static synchronized void tick(Context supplied){
        Context context=supplied.getApplicationContext();long now=SystemClock.elapsedRealtime();
        if(!UPLOAD.start(now,consented(context)))return;
        uploadState="SENDING";
        new Thread(()->{
            boolean success=false;
            try{
                JsonObject report=SupportSnapshot.project(Diagnostics.supportSnapshot(context),BuildConfig.VERSION_CODE,System.currentTimeMillis());
                FriendsAccessAndroid client=new FriendsAccessAndroid(context);request=client;
                if(!consented(context)){uploadState="OFF";return;}
                client.supportDiagnostics(report);success=true;uploadState="STORED";
            }catch(FriendsAccessAndroid.SupportRateLimited failure){uploadState="RATE_LIMITED";}
            catch(FriendsAccessAndroid.Denied failure){uploadState="AUTH_REJECTED";}
            catch(java.net.SocketTimeoutException failure){uploadState="TIMEOUT";}
            catch(Exception failure){uploadState="UNAVAILABLE";}
            finally{request=null;UPLOAD.finish(SystemClock.elapsedRealtime(),success);}
        },"support-upload").start();
    }
}
