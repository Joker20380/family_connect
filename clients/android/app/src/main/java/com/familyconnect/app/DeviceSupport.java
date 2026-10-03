package com.familyconnect.app;

import android.app.Activity;
import android.content.*;
import android.widget.*;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

final class DeviceSupport {
    private static final AtomicBoolean running=new AtomicBoolean();
    private static volatile String observed;
    static String observed(){return observed;}
    static String cached(Context context){
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            android.content.SharedPreferences prefs=context.getSharedPreferences("device-support",Context.MODE_PRIVATE);
            String value=prefs.getString("support_id",null);
            observed=identity.reference().equals(prefs.getString("registration",null))&&SupportId.valid(value)?value:null;
            return observed;
        }catch(Exception failure){observed=null;return null;}
    }
    static void store(Context context,String registration,String support){
        if(!context.getSharedPreferences("device-support",Context.MODE_PRIVATE).edit().putString("registration",registration)
            .putString("support_id",SupportId.require(support)).commit())throw new IllegalStateException("Support storage");
        observed=support;
    }
    static void refresh(Context source,boolean force,Consumer<String> completed){
        Context context=source.getApplicationContext();
        android.content.SharedPreferences prefs=context.getSharedPreferences("device-support",Context.MODE_PRIVATE);
        long age=System.currentTimeMillis()-prefs.getLong("checked_at",0);
        if(!running.compareAndSet(false,true)){completed.accept(cached(context));return;}
        new Thread(()->{
            try{
                if(force||age<0||age>=6*3600000L){
                    prefs.edit().putLong("checked_at",System.currentTimeMillis()).apply();
                    new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+15000).supportId();
                }
            }catch(Exception ignored){}finally{running.set(false);completed.accept(cached(context));}
        },"device-support").start();
    }
    static void attach(Activity activity,LinearLayout panel,Executor worker){
        TerminalUi.label(panel,activity.getString(R.string.support_title),16,TerminalUi.AMBER);
        TextView label=TerminalUi.label(panel,activity.getString(R.string.support_unavailable),14,TerminalUi.TEXT);
        Button copy=TerminalUi.button(panel,R.string.support_copy,()->{
            String value=(String)label.getTag();if(!SupportId.valid(value))return;
            activity.getSystemService(ClipboardManager.class).setPrimaryClip(ClipData.newPlainText("Family Connect Support ID",value));
            Toast.makeText(activity,R.string.support_copied,Toast.LENGTH_SHORT).show();
        });copy.setEnabled(false);
        Consumer<String> render=value->activity.runOnUiThread(()->{
            if(activity.isFinishing()||activity.isDestroyed())return;
            label.setTag(value);label.setText(SupportId.valid(value)?activity.getString(R.string.support_value,value):activity.getString(R.string.support_unavailable));copy.setEnabled(SupportId.valid(value));
        });
        worker.execute(()->render.accept(cached(activity)));
        TerminalUi.button(panel,R.string.support_refresh,()->refresh(activity,true,render));
        refresh(activity,false,render);
    }
}
