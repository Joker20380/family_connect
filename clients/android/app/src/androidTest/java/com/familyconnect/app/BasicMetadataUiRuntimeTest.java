package com.familyconnect.app;

import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import androidx.test.platform.app.InstrumentationRegistry;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.UUID;
import org.junit.Test;
import static org.junit.Assert.*;

public class BasicMetadataUiRuntimeTest {
    private boolean notice(Instrumentation instrumentation) {
        AccessibilityNodeInfo root = instrumentation.getUiAutomation().getRootInActiveWindow();
        return root != null && !root.findAccessibilityNodeInfosByText("Basic technical data").isEmpty();
    }
    private void requireNotice(Instrumentation instrumentation) {
        long deadline = SystemClock.elapsedRealtime() + 5000;
        while (!notice(instrumentation) && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(50);
        assertTrue("Disclosure must appear on foreground before sampling", notice(instrumentation));
    }
    @Test public void backAndForegroundKeepNoticeBeforeSampling() throws Exception {
        assertEquals("ranchu", Build.HARDWARE);
        assertTrue(BuildConfig.APPLICATION_ID.endsWith(".metadata"));
        Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();
        BasicMetadataStorageRuntimeTest.Storage storage = new BasicMetadataStorageRuntimeTest.Storage("metadata-ui-" + UUID.randomUUID());
        Constructor<TechnicalMetadataUpload> constructor = TechnicalMetadataUpload.class.getDeclaredConstructor(Context.class);
        constructor.setAccessible(true);
        TechnicalMetadataUpload upload = constructor.newInstance(storage);
        Field singleton = TechnicalMetadataUpload.class.getDeclaredField("instance");
        singleton.setAccessible(true);
        singleton.set(null, upload);
        Method changed = TechnicalMetadataUpload.class.getDeclaredMethod("changed");
        changed.setAccessible(true);
        changed.invoke(upload);
        assertFalse(storage.actual().contains("notice_policy"));
        assertEquals(1, storage.actual().getLong("sequence", 0));
        Intent intent = new Intent(instrumentation.getTargetContext(), FriendsActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        instrumentation.getTargetContext().startActivity(intent);
        requireNotice(instrumentation);
        assertEquals("NOTICE_PENDING", storage.actual().getString("mode", ""));
        assertEquals(1, storage.actual().getLong("sequence", 0));
        instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);
        long dismissed = SystemClock.elapsedRealtime() + 5000;
        while (notice(instrumentation) && SystemClock.elapsedRealtime() < dismissed) SystemClock.sleep(50);
        assertFalse("Back must dismiss the notice before leaving", notice(instrumentation));
        instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_HOME);
        long background = SystemClock.elapsedRealtime() + 5000;
        boolean launcher = false;
        while (!launcher && SystemClock.elapsedRealtime() < background) {
            AccessibilityNodeInfo root = instrumentation.getUiAutomation().getRootInActiveWindow();
            launcher = root != null && root.getPackageName() != null && root.getPackageName().toString().contains("launcher");
            if (!launcher) SystemClock.sleep(50);
        }
        assertTrue("Home transition must finish before reentry", launcher);
        instrumentation.getTargetContext().startActivity(intent);
        requireNotice(instrumentation);
        assertEquals(1, storage.actual().getLong("sequence", 0));
        assertFalse(storage.actual().contains("notice_policy"));
        assertFalse(storage.actual().getBoolean("enabled", true));
        String vpnStatus = ConnectionService.status;
        String vpnHealth = ConnectionService.healthStatus;
        AccessibilityNodeInfo root = instrumentation.getUiAutomation().getRootInActiveWindow();
        assertNotNull(root);
        assertTrue(root.findAccessibilityNodeInfosByText("Понятно / Understood").get(0)
            .performAction(AccessibilityNodeInfo.ACTION_CLICK));
        Field status = TechnicalMetadataUpload.class.getDeclaredField("status");
        status.setAccessible(true);
        long refused = SystemClock.elapsedRealtime() + 5000;
        while (!"AUTH_OR_CONTRACT_REFUSED".equals(status.get(upload)) && SystemClock.elapsedRealtime() < refused) SystemClock.sleep(50);
        assertEquals("AUTH_OR_CONTRACT_REFUSED", status.get(upload));
        assertEquals(TechnicalMetadataPolicy.POLICY, storage.actual().getString("notice_policy", ""));
        assertEquals(2, storage.actual().getLong("sequence", 0));
        changed.invoke(upload);
        assertEquals(2, storage.actual().getLong("sequence", 0));
        assertEquals(vpnStatus, ConnectionService.status);
        assertEquals(vpnHealth, ConnectionService.healthStatus);
    }
}
