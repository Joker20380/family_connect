package com.familyconnect.app;

import java.io.File;
import java.io.IOException;

/** Read-only admission check for legacy operations, including interrupted enrollment. */
final class ControlStatePresence {
    interface Keys { boolean contains(String alias) throws Exception; }
    static boolean present(File directory, Keys keys) throws Exception {
        for (String name : new String[]{"control-identity.enc", "control-journal.enc", "control-enrollment.enc"})
            for (String suffix : new String[]{"", ".bak", ".new"})
                if (new File(directory, name+suffix).exists()) return true;
        if (keys.contains("family-connect-control-enrollment-v1") || keys.contains("family-connect-control-identity-v1") || keys.contains("family-connect-control-journal-v1"))
            return true;
        return false;
    }
    static void requireUnmanaged(File directory, Keys keys) throws Exception {
        if(present(directory,keys))throw new IOException("Managed control recovery required");
    }
}
