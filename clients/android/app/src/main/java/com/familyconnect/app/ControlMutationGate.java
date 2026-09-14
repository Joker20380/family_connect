package com.familyconnect.app;

import android.content.Context;
import java.security.KeyStore;

/** Legacy profile edits cannot bypass managed state, even after recovery.
 * Called under OWNER on workers only; never initializes, deletes, or rotates state.
 */
final class ControlMutationGate {
    static boolean managed(Context context) throws Exception {
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null);
        return ControlStatePresence.present(context.getNoBackupFilesDir(), keys::containsAlias);
    }
    static void legacy(Context context) throws Exception {
        if(managed(context))throw new java.io.IOException("Managed control recovery required");
    }
}
