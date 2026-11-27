package com.familyconnect.app;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.AtomicFile;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.google.gson.JsonObject;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

final class TechnicalMetadataUpload {
    private static TechnicalMetadataUpload instance;
    private final Context context;
    private final SharedPreferences prefs;
    private final TechnicalMetadataPolicy policy;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final TechnicalMetadataSchedule schedule=new TechnicalMetadataSchedule();
    private final Runnable flush=this::flush;
    private FriendsAccessAndroid request;
    private ConnectivityManager.NetworkCallback callback;
    private boolean dirty,noticeOpen;
    private String status="WAITING";
    private TechnicalMetadataUpload(Context owner){
        context=owner.getApplicationContext();prefs=context.getSharedPreferences("technical-metadata-v1",Context.MODE_PRIVATE);
        policy=new TechnicalMetadataPolicy(new TechnicalMetadataPolicy.Store(){
            public Map<String,Object> read(){return new HashMap<>(prefs.getAll());}
            public boolean commit(Map<String,Object> values){
                SharedPreferences.Editor edit=prefs.edit();
                for(Map.Entry<String,Object> item:values.entrySet()){
                    Object value=item.getValue();String name=item.getKey();
                    if(value instanceof String)edit.putString(name,(String)value);
                    else if(value instanceof Long)edit.putLong(name,(Long)value);
                    else if(value instanceof Integer)edit.putInt(name,(Integer)value);
                    else if(value instanceof Boolean)edit.putBoolean(name,(Boolean)value);
                    else return false;
                }
                if(!values.containsKey("notice_policy"))edit.remove("notice_policy");
                boolean saved=edit.commit();if(!saved)persistFault();return saved;
            }
        });
        try{
            if(new File(context.getNoBackupFilesDir(),"technical-storage-fault").exists()){policy.failStorage();return;}
            File file=new File(context.getNoBackupFilesDir(),"technical-installation");
            AtomicFile binding=new AtomicFile(file);String identity;
            boolean absent=!file.exists();
            if(absent){
                identity=UUID.randomUUID().toString();FileOutputStream output=binding.startWrite();
                try{output.write(identity.getBytes(StandardCharsets.US_ASCII));binding.finishWrite(output);}
                catch(Exception error){binding.failWrite(output);throw error;}
            }else identity=new String(binding.readFully(),StandardCharsets.US_ASCII);
            if(!identity.matches("[0-9a-f-]{36}"))throw new IllegalStateException("Metadata installation binding");
            android.content.pm.PackageInfo installed=context.getPackageManager().getPackageInfo(context.getPackageName(),0);
            boolean fresh=absent&&prefs.getAll().isEmpty()&&installed.firstInstallTime==installed.lastUpdateTime
                &&!new File(context.getFilesDir(),"friends-identity.enc").exists();
            policy.initialize(fresh,identity);
        }catch(Exception refused){policy.failStorage();persistFault();}
    }
    private void persistFault(){
        AtomicFile file=new AtomicFile(new File(context.getNoBackupFilesDir(),"technical-storage-fault"));
        try{FileOutputStream output=file.startWrite();try{output.write(1);file.finishWrite(output);}catch(Exception failure){file.failWrite(output);}}
        catch(Exception unavailable){}
    }
    private static synchronized TechnicalMetadataUpload get(Context context){if(instance==null)instance=new TechnicalMetadataUpload(context);return instance;}
    static void start(Context context){get(context).changed();}
    static void changed(Context context){get(context).changed();}
    static void foreground(Activity activity){activity.runOnUiThread(()->get(activity).disclose(activity));}
    private synchronized boolean enabled(){return BuildConfig.BASIC_METADATA_APPROVED&&policy.enabled();}
    private synchronized void changed(){
        boolean enabled=enabled(),revoke=policy.pending();ConnectionTerminal.VPN.observeTechnical(enabled);
        if(policy.faulted()||!enabled&&!revoke){detach();return;}
        if(callback==null){
            ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
            if(manager!=null){
                ConnectivityManager.NetworkCallback candidate=new ConnectivityManager.NetworkCallback(){
                    @Override public void onAvailable(Network network){changed();}
                    @Override public void onLost(Network network){changed();}
                    @Override public void onCapabilitiesChanged(Network network,NetworkCapabilities capabilities){changed();}
                };
                try{manager.registerDefaultNetworkCallback(candidate);callback=candidate;}catch(RuntimeException unavailable){}
            }
        }
        dirty=true;main.removeCallbacks(flush);main.postDelayed(flush,schedule.delay(SystemClock.elapsedRealtime(),revoke));
    }
    private synchronized void detach(){
        main.removeCallbacks(flush);dirty=false;
        if(callback!=null){try{context.getSystemService(ConnectivityManager.class).unregisterNetworkCallback(callback);}catch(RuntimeException unavailable){}callback=null;}
    }
    private synchronized void object(){
        if(request!=null)request.cancel();ConnectionTerminal.VPN.observeTechnical(false);
        policy.object();schedule.revoke();changed();
    }
    private synchronized void flush(){
        if(policy.faulted()||!enabled()&&!policy.pending()){detach();return;}
        if(!schedule.begin(SystemClock.elapsedRealtime(),policy.pending())){changed();return;}
        TechnicalMetadataPolicy.Ticket ticket=policy.reserve();
        if(ticket==null){schedule.finish(SystemClock.elapsedRealtime(),false);changed();return;}
        status=ticket.sample?"SENDING_BASIC":"REVOKING";dirty=false;
        new Thread(()->send(ticket),"technical-metadata-upload").start();
    }
    private void send(TechnicalMetadataPolicy.Ticket ticket){
        boolean success=false;String result="UNAVAILABLE";
        try{
            JsonObject report;FriendsAccessAndroid client;
            synchronized(this){
                if(!policy.current(ticket)||ticket.sample&&!enabled())return;
                report=ticket.sample?TechnicalMetadataSnapshot.basicReport(ticket.epoch,ticket.sequence,TechnicalMetadataAndroid.sample(context,true))
                    :TechnicalMetadataSnapshot.report(ticket.epoch,ticket.sequence,false,new JsonObject());
                client=new FriendsAccessAndroid(context);request=client;
            }
            client.technicalMetadata(report);success=true;result=ticket.sample?"BASIC_STORED_NO_CONSENT_CLAIM":"REVOKED";
        }catch(FriendsAccessAndroid.SupportRateLimited limited){result="RATE_LIMITED";}
        catch(FriendsAccessAndroid.Denied denied){result="AUTH_OR_CONTRACT_REFUSED";}
        catch(Exception unavailable){result="UNAVAILABLE";}
        finally{
            synchronized(this){
                request=null;schedule.finish(SystemClock.elapsedRealtime(),success);
                if(policy.current(ticket)){status=result;if(success)policy.acknowledge(ticket);dirty=dirty||!success;}else schedule.revoke();
                if(policy.faulted()||!enabled()&&!policy.pending()){detach();return;}
                main.removeCallbacks(flush);main.postDelayed(flush,dirty||policy.pending()?schedule.delay(SystemClock.elapsedRealtime(),policy.pending()):6L*3600000);
            }
        }
    }
    private synchronized void disclose(Activity activity){
        if(!BuildConfig.BASIC_METADATA_APPROVED||!policy.needsNotice()||noticeOpen||activity.isFinishing())return;
        noticeOpen=true;
        new android.app.AlertDialog.Builder(activity).setTitle("Базовые технические сведения / Basic technical data")
            .setMessage("Автоматически: ОС и версия приложения, тип связи, доступные SIM/зарегистрированный оператор (отдельные источники), фактические transport/gateway и категория ошибки. Сервер определяет ASN/организацию по подтверждённому временному IP-наблюдению, не по VPN/relay IP. Цель — диагностика совместимости и подключения. Только последнее наблюдение, до 7 дней. Без модели, города, географии и истории IP. Это уведомление, не согласие. Возражение и дополнительная диагностика: Поддержка → Конфиденциальность. Отказ не ограничивает VPN, оплату, обновления и поддержку.\nAutomatic basic data, latest only up to 7 days; no model, location or IP history. Privacy/objection in Support → Privacy. Acknowledgment is not consent.")
            .setNegativeButton("Возражаю / Object",(dialog,which)->object())
            .setPositiveButton("Понятно / Understood",(dialog,which)->{synchronized(this){policy.noticeShown(BuildConfig.BASIC_METADATA_APPROVED);changed();}})
            .setOnDismissListener(dialog->{synchronized(this){noticeOpen=false;}}).show();
    }
    static void controls(Activity activity,LinearLayout panel){
        TechnicalMetadataUpload upload=get(activity);
        TextView heading=new TextView(activity);heading.setText("Конфиденциальность / Privacy · basic-2026-11-v1");panel.addView(heading);
        TextView status=new TextView(activity);panel.addView(status);
        Runnable render=()->status.setText(upload.policy.mode()+" · "+upload.status+(upload.policy.pending()?" · offline revocation pending":"")
            +(BuildConfig.BASIC_METADATA_APPROVED?"":" · public activation blocked pending processing-basis review"));render.run();
        Button stop=new Button(activity);stop.setText("Отключить / возразить против технических сведений");panel.addView(stop);
        stop.setOnClickListener(view->{upload.object();render.run();});
        Button resume=new Button(activity);resume.setText("Пересмотреть базовый режим / Review basic mode");panel.addView(resume);
        resume.setOnClickListener(view->{synchronized(upload){upload.policy.resumeBasic(BuildConfig.BASIC_METADATA_APPROVED);upload.disclose(activity);render.run();}});
    }
}
