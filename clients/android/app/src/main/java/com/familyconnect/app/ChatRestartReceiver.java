package com.familyconnect.app;

import android.content.*;

/** Resume only an activated account and preserve the user's background setting. */
public final class ChatRestartReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context,Intent intent){
        if(!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())&&!Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction()))return;
        if(context.getSharedPreferences(FriendsActivity.class.getName(),Context.MODE_PRIVATE).getBoolean("activated",false))ChatDeliveryService.start(context);
    }
}
