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
            .setMessage(R.string.subscription_loading).setPositiveButton(android.R.string.ok,null).show();
        ChatRuntime.WORKER.execute(()->{
            JsonObject result=new JsonObject();
            try{result=ChatRuntime.subscription(activity,ChatRuntime.open(activity,false));}catch(Exception unavailable){}
            JsonObject saved=result;
            boolean connected=false;
            try{connected=new ChatNetworkAndroid(activity).available();}catch(SecurityException unavailable){}
            boolean online=connected;
            activity.runOnUiThread(()->{
                if(activity.isFinishing()||activity.isDestroyed()||!dialog.isShowing())return;
                try{
                    dialog.setMessage(SubscriptionPresentation.summary(saved,online,activity.getResources().getConfiguration().getLocales().get(0),ZoneId.systemDefault(),System.currentTimeMillis()/1000,text(activity)));
                    if(saved.has("notice")&&!saved.get("notice").isJsonNull()){
                        JsonArray ids=new JsonArray();ids.add(saved.getAsJsonObject("notice").get("id"));
                        ChatNotifications.cancel(activity,"subscription");
                        ChatRuntime.WORKER.execute(()->{try{ChatRuntime.mark(ChatRuntime.open(activity,false),"mark_events",ids,"read");}catch(Exception unavailable){}});
                    }
                }catch(Exception invalid){dialog.setMessage(activity.getString(R.string.subscription_unknown));}
            });
        });
    }
}
