package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.function.BooleanSupplier;

/** Service worker policy: admission, recovery, explicit selection and verified reconnect. */
final class ControlSelection {
    static String select(ControlTransaction core,ControlIdentity identity,JsonObject enrollment,
                         String gateway,BooleanSupplier connected)throws Exception {
        if(gateway==null||!gateway.matches("[a-zA-Z0-9_-]{1,64}"))throw new IOException("Invalid gateway");
        ControlIntake.authorize(identity,enrollment);
        String recovery=core.recover();
        if(!"IDLE".equals(recovery)&&!"ROLLED_BACK".equals(recovery))return "FAILED";
        String result=core.selectGateway(gateway);
        if("SELECTED".equals(result)&&!connected.getAsBoolean())core.resume();
        return result;
    }
}
