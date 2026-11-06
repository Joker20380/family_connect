package com.familyconnect.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.widget.LinearLayout;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.time.ZoneId;

final class SubscriptionUi {
    static SubscriptionPresentation.Text text(Context context){
        Context localized=AppLanguage.wrap(context);
        return (name,arguments)->localized.getString(localized.getResources().getIdentifier(name,"string",localized.getPackageName()),arguments);
    }

    static Intent intent(Context context){
        return new Intent(context,FriendsActivity.class).setAction("subscription-access")
            .putExtra("subscription_access",true).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
    }

    static void attach(Activity activity,LinearLayout panel){
        TerminalUi.button(panel,R.string.subscription_title,()->show(activity));
    }

    static void show(Activity activity){
        AlertDialog dialog=new AlertDialog.Builder(activity).setTitle(R.string.subscription_title)
            .setMessage(R.string.subscription_loading).setPositiveButton(android.R.string.ok,null)
            .setNeutralButton(R.string.subscription_refresh,null).show();
        var pending=new java.util.concurrent.atomic.AtomicReference<SubscriptionRefreshGate.Request>();
        JsonObject[] displayed={new JsonObject()};
        java.util.function.Consumer<JsonObject> render=saved->{
            if(activity.isFinishing()||activity.isDestroyed()||!dialog.isShowing())return;
            displayed[0]=saved;
            boolean connected=false;
            try{connected=new ChatNetworkAndroid(activity).available();}catch(SecurityException unavailable){}
            try{
                dialog.setMessage(SubscriptionPresentation.summary(saved,connected,activity.getResources().getConfiguration().getLocales().get(0),ZoneId.systemDefault(),System.currentTimeMillis()/1000,text(activity)));
                if(saved.has("notice")&&!saved.get("notice").isJsonNull()){
                    JsonArray ids=new JsonArray();ids.add(saved.getAsJsonObject("notice").get("id"));
                    ChatNotifications.cancel(activity,"subscription");
                    ChatRuntime.WORKER.execute(()->{try{ChatRuntime.mark(ChatRuntime.open(activity,false),"mark_events",ids,"read");}catch(Exception unavailable){}});
                }
            }catch(Exception invalid){dialog.setMessage(activity.getString(R.string.subscription_unknown));}
        };
        Runnable refresh=()->{
            if(activity.isFinishing()||activity.isDestroyed()||!dialog.isShowing())return;
            SubscriptionRefreshGate.Request request=ChatRuntime.SUBSCRIPTION_REFRESH.begin();
            JsonObject loading=displayed[0].deepCopy();
            if(request==null){loading.addProperty("refresh_status","busy");render.accept(loading);return;}
            pending.set(request);dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setEnabled(false);
            loading.addProperty("refresh_status","refreshing");render.accept(loading);
            ChatRuntime.refreshSubscription(activity,request,result->activity.runOnUiThread(()->{
                if(!pending.compareAndSet(request,null)||!dialog.isShowing())return;
                dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setEnabled(true);render.accept(result);
            }));
        };
        dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setEnabled(false);
        dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(view->refresh.run());
        dialog.setOnDismissListener(ignored->{var request=pending.getAndSet(null);if(request!=null)request.cancel();});
        ChatRuntime.WORKER.execute(()->{
            JsonObject cached=new JsonObject();
            try{cached=ChatRuntime.subscription(activity,ChatRuntime.open(activity,false));}catch(Exception unavailable){}
            JsonObject saved=cached;
            activity.runOnUiThread(()->{dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setEnabled(true);render.accept(saved);refresh.run();});
        });
    }
}
