package com.familyconnect.app;

import android.content.Context;
import com.google.gson.JsonObject;
import java.io.File;

final class FriendsReadiness {
    static String inspect(Context context, boolean activated) {
        String identity="UNAVAILABLE", provisioning="UNAVAILABLE";
        try(ControlIdentity loaded=new FriendsIdentityVault(context).load()) { identity="PRESENT"; }
        catch(Exception ignored) {}
        try { provisioning=new FriendsAccessAndroid(context).cachedProvisioningUsable()?"PRESENT_VALID":"ABSENT"; }
        catch(Exception ignored) {}
        JsonObject restricted=new JsonObject();
        try {
            NativeRestricted.load();
            restricted=ControlJson.parse(NativeRestricted.readiness(new File(context.getNoBackupFilesDir(),"restricted").getPath()).getBytes(java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        } catch(Exception | LinkageError ignored) {}
        return "activated: "+activated+"\nidentity: "+identity+"\nnormal_provisioning: "+provisioning+"\n"
            +ReadinessSummary.restricted(restricted)
            +"refresh: NOT_ATTEMPTED\nProduction Friends BOOT-1 provisioning/delivery is not configured. Normal access is not restricted readiness.";
    }
}
