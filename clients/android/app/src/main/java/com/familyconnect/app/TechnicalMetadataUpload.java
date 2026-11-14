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
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;
import com.google.gson.JsonObject;

final class TechnicalMetadataUpload {
    private static TechnicalMetadataUpload instance;
    private final Context context;
    private final SharedPreferences prefs;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final TechnicalMetadataSchedule schedule=new TechnicalMetadataSchedule();
    private final Runnable flush=this::flush;
    private FriendsAccessAndroid request;
    private ConnectivityManager.NetworkCallback callback;
    private boolean dirty;
    private String status="OFF";
    private TechnicalMetadataUpload(Context context){this.context=context.getApplicationContext();prefs=context.getSharedPreferences("technical-metadata-v1",Context.MODE_PRIVATE);}
    private static synchronized TechnicalMetadataUpload get(Context context){if(instance==null)instance=new TechnicalMetadataUpload(context);return instance;}
    static void start(Context context){get(context).changed();}
    static void changed(Context context){get(context).changed();}
    private synchronized boolean enabled(){return prefs.getBoolean("enabled",false);}
    private synchronized void changed(){
        boolean enabled=enabled(),revoke=prefs.getBoolean("revoke_pending",false);
        ConnectionTerminal.VPN.observeTechnical(enabled);
        if(!enabled&&!revoke){detach();return;}
        if(callback==null){
            ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
            if(manager!=null){
                ConnectivityManager.NetworkCallback candidate=new ConnectivityManager.NetworkCallback(){
                    @Override public void onAvailable(Network network){changed();}
                    @Override public void onLost(Network network){changed();}
                    @Override public void onCapabilitiesChanged(Network network,NetworkCapabilities capabilities){changed();}
                };
                try{manager.registerDefaultNetworkCallback(candidate);callback=candidate;}catch(RuntimeException ignored){}
            }
        }
        dirty=true;main.removeCallbacks(flush);main.postDelayed(flush,schedule.delay(SystemClock.elapsedRealtime(),revoke));
    }
    private synchronized void detach(){
        main.removeCallbacks(flush);dirty=false;
        if(callback!=null){try{context.getSystemService(ConnectivityManager.class).unregisterNetworkCallback(callback);}catch(RuntimeException ignored){}callback=null;}
    }
    private synchronized boolean consent(boolean enabled){
        long epoch=prefs.getLong("epoch",0)+1;
        if(!prefs.edit().putLong("epoch",epoch).putBoolean("enabled",enabled).putBoolean("revoke_pending",!enabled).commit())return false;
        if(request!=null)request.cancel();status=enabled?"PENDING":"REVOCATION_PENDING";
        schedule.revoke();changed();return true;
    }
    private synchronized void flush(){
        boolean enabled=enabled(),revoke=prefs.getBoolean("revoke_pending",false);
        if(!enabled&&!revoke){detach();return;}
        if(!schedule.begin(SystemClock.elapsedRealtime(),revoke)){main.postDelayed(flush,schedule.delay(SystemClock.elapsedRealtime(),revoke));return;}
        long epoch=prefs.getLong("epoch",0),sequence=prefs.getLong("sequence",0)+1;
        if(!prefs.edit().putLong("sequence",sequence).commit()){schedule.finish(SystemClock.elapsedRealtime(),false);changed();return;}
        status=revoke?"REVOCATION_PENDING":"SENDING";dirty=false;
        new Thread(()->send(epoch,sequence,enabled),"technical-metadata-upload").start();
    }
    private void send(long epoch,long sequence,boolean enabled){
        boolean success=false;String result="UNAVAILABLE";
        try{
            JsonObject report;
            FriendsAccessAndroid client;
            synchronized(this){
                if(epoch!=prefs.getLong("epoch",0)||enabled!=enabled())return;
                report=TechnicalMetadataSnapshot.report(epoch,sequence,enabled,enabled?TechnicalMetadataAndroid.sample(context):new JsonObject());
                client=new FriendsAccessAndroid(context);request=client;
            }
            client.technicalMetadata(report);success=true;result=enabled?"STORED":"REVOKED";
        }catch(FriendsAccessAndroid.SupportRateLimited limited){result="RATE_LIMITED";}
        catch(FriendsAccessAndroid.Denied denied){result="AUTH_REJECTED";}
        catch(Exception unavailable){result="UNAVAILABLE";}
        finally{
            synchronized(this){
                request=null;schedule.finish(SystemClock.elapsedRealtime(),success);
                if(epoch==prefs.getLong("epoch",0)){
                    status=!enabled&&!success?"REVOCATION_PENDING":result;
                    if(!enabled&&success)prefs.edit().putBoolean("revoke_pending",false).commit();
                    dirty=dirty||!success;
                }else schedule.revoke();
                if(!enabled()&&!prefs.getBoolean("revoke_pending",false)){detach();return;}
                main.removeCallbacks(flush);main.postDelayed(flush,dirty||prefs.getBoolean("revoke_pending",false)?schedule.delay(SystemClock.elapsedRealtime(),prefs.getBoolean("revoke_pending",false)):6L*3600000);
            }
        }
    }
    static void controls(Activity activity,LinearLayout panel){
        TechnicalMetadataUpload upload=get(activity);Switch toggle=new Switch(activity);
        toggle.setText("Технические сведения для поддержки / Support technical information");toggle.setChecked(upload.enabled());panel.addView(toggle);
        TextView status=new TextView(activity);panel.addView(status);
        Runnable render=()->status.setText(upload.enabled()?"ON · до выключения / until disabled · "+upload.status:upload.prefs.getBoolean("revoke_pending",false)?"OFF · отзыв ожидает связи / revocation pending":"OFF");render.run();
        toggle.setOnCheckedChangeListener((button,checked)->{
            if(!checked){if(upload.enabled())upload.consent(false);render.run();return;}
            new android.app.AlertDialog.Builder(activity).setTitle("Технические сведения / Technical information")
                .setMessage("Модель, Android и версия приложения; тип связи, доступный оператор SIM и зарегистрированной сети, радио; фактическая VPN-сессия, gateway, ограниченная ошибка/readiness; приблизительные страна/регион/город и ASN по подходящему IP-наблюдению. IP-география не GPS и не доказывает местонахождение. Без номера, IMEI, SSID/BSSID, cell ID, приложений, сайтов, сообщений и ключей. Только последние сведения, включая аппаратный профиль, до 7 дней. Сбор действует ДО ВЫКЛЮЧЕНИЯ, отдельно от прежней 7-дневной диагностики. Выключение останавливает сбор немедленно; сервер удаляет данные после получения отзыва. В офлайне отзыв ожидает связи. Отказ не ограничивает VPN, оплату, обновления или поддержку.\nModel/OS/app, connection/operator/radio, VPN/session/error, approximate IP geography/ASN. Latest only, hardware included: up to 7 days. Enabled until switched off; offline revocation remains pending. No GPS or traffic content; optional for all services.")
                .setNegativeButton(android.R.string.cancel,(dialog,which)->toggle.setChecked(false))
                .setOnCancelListener(dialog->toggle.setChecked(false))
                .setPositiveButton(android.R.string.ok,(dialog,which)->{if(!upload.consent(true))toggle.setChecked(false);render.run();}).show();
        });
    }
}
