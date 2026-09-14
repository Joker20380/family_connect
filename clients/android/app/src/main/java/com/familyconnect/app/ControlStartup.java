package com.familyconnect.app;

import java.io.IOException;

/** Service startup policy; invoked under the existing operation owner. */
final class ControlStartup {
    interface Presence { boolean managed() throws Exception; }
    interface Recovery { String recover() throws Exception; }
    interface Connect { void run() throws Exception; }
    static void run(boolean connectRequested, Presence presence, Recovery recovery,
                    Connect resume, Connect legacy) throws Exception {
        if(presence.managed()) {
            String outcome=recovery.recover();
            if(!"IDLE".equals(outcome)&&!"ROLLED_BACK".equals(outcome))
                throw new IOException("Control recovery required");
            // Recovery may have restored a baseline. Never overwrite it with legacy/Auto.
            if(connectRequested&&"IDLE".equals(outcome))resume.run();
            return;
        }
        if(connectRequested)legacy.run();
    }
}
