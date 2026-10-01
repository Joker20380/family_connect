package com.familyconnect.app;

import android.content.Context;

final class FriendsReadiness {
    static String inspect(Context context, boolean activated) {
        String identity="UNAVAILABLE", provisioning="UNAVAILABLE";
        try(ControlIdentity loaded=new FriendsIdentityVault(context).load()) { identity="PRESENT"; }
        catch(Exception ignored) {}
        try { provisioning=new FriendsAccessAndroid(context).cachedProvisioningUsable()?"PRESENT_VALID":"ABSENT"; }
        catch(Exception ignored) {}
        return "activated: "+activated+"\nidentity: "+identity+"\nnormal_provisioning: "+provisioning+"\n"
            +"Production restricted recovery: "+FriendsRestricted.summary(context);
    }
}
