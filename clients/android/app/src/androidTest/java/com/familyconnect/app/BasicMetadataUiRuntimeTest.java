package com.familyconnect.app;

import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.UUID;
import org.junit.Test;
import org.junit.After;
import org.junit.Before;
import static org.junit.Assert.*;

public class BasicMetadataUiRuntimeTest {
    final Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();
    @Before @After public void finishOwnedActivities() {
        java.util.concurrent.atomic.AtomicBoolean remaining = new java.util.concurrent.atomic.AtomicBoolean(true);
        long deadline = SystemClock.elapsedRealtime() + 5000;
        while (remaining.get() && SystemClock.elapsedRealtime() < deadline) {
            instrumentation.runOnMainSync(() -> {
                remaining.set(false);
                for (Stage stage : Stage.values()) if (stage != Stage.DESTROYED) {
                    for (android.app.Activity activity : new java.util.ArrayList<>(ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(stage))) {
                        remaining.set(true);
                        activity.finish();
                    }
                }
            });
            if (remaining.get()) SystemClock.sleep(50);
        }
        assertFalse("Previous test activity must finish", remaining.get());
    }
    private Object field(TechnicalMetadataUpload upload, String name) throws Exception {
        Field value = TechnicalMetadataUpload.class.getDeclaredField(name);
        value.setAccessible(true);
        return value.get(upload);
    }
    private void invoke(TechnicalMetadataUpload upload, String name) throws Exception {
        Method method = TechnicalMetadataUpload.class.getDeclaredMethod(name);
        method.setAccessible(true);
        method.invoke(upload);
    }
    private boolean notice() {
        AccessibilityNodeInfo root = instrumentation.getUiAutomation().getRootInActiveWindow();
        return root != null && !root.findAccessibilityNodeInfosByText("Basic technical data").isEmpty();
    }
    private TechnicalMetadataUpload install(BasicMetadataStorageRuntimeTest.Storage storage) throws Exception {
        assertEquals("ranchu", Build.HARDWARE);
        assertEquals(BuildConfig.BASIC_METADATA_APPROVED, BuildConfig.APPLICATION_ID.endsWith(".metadata"));
        Field singleton = TechnicalMetadataUpload.class.getDeclaredField("instance");
        singleton.setAccessible(true);
        TechnicalMetadataUpload old = (TechnicalMetadataUpload) singleton.get(null);
        if (old != null) invoke(old, "detach");
        if (notice()) instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);
        Constructor<TechnicalMetadataUpload> constructor = TechnicalMetadataUpload.class.getDeclaredConstructor(Context.class);
        constructor.setAccessible(true);
        TechnicalMetadataUpload upload = constructor.newInstance(storage);
        singleton.set(null, upload);
        invoke(upload, "changed");
        return upload;
    }
    private void foreground() throws Exception {
        instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_HOME);
        long deadline = SystemClock.elapsedRealtime() + 5000;
        boolean background = false;
        while (!background && SystemClock.elapsedRealtime() < deadline) {
            AccessibilityNodeInfo root = instrumentation.getUiAutomation().getRootInActiveWindow();
            background = root != null && root.getPackageName() != null && root.getPackageName().toString().contains("launcher");
            if (!background) SystemClock.sleep(50);
        }
        assertTrue("Home must complete before foreground reentry", background);
        Intent intent = instrumentation.getTargetContext().getPackageManager().getLaunchIntentForPackage(BuildConfig.APPLICATION_ID);
        assertNotNull(intent);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        instrumentation.getTargetContext().startActivity(intent);
        instrumentation.waitForIdleSync();
    }
    private void awaitNotice() {
        long deadline = SystemClock.elapsedRealtime() + 5000;
        while (!notice() && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(50);
        assertTrue("Disclosure actually displayed before sampling", notice());
    }
    @Test public void displayedNoticeAutomaticallyStartsBasicWithoutClick() throws Exception {
        BasicMetadataStorageRuntimeTest.Storage storage = new BasicMetadataStorageRuntimeTest.Storage("metadata-ui-" + UUID.randomUUID());
        TechnicalMetadataUpload upload = install(storage);
        TechnicalMetadataPolicy policy = (TechnicalMetadataPolicy) field(upload, "policy");
        assertFalse(storage.actual().contains("notice_policy"));
        assertEquals(1, storage.actual().getLong("sequence", 0));
        try {
            foreground();
            if (!BuildConfig.BASIC_METADATA_APPROVED) {
                assertFalse(notice());
                assertTrue(policy.noticeShown(true));
                invoke(upload, "changed");
                assertEquals(1, storage.actual().getLong("sequence", 0));
                assertNull(field(upload, "callback"));
                return;
            }
            awaitNotice();
            long deadline = SystemClock.elapsedRealtime() + 5000;
            while (storage.actual().getLong("sequence", 0) == 1 && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(50);
            assertEquals(TechnicalMetadataPolicy.POLICY, storage.actual().getString("notice_policy", ""));
            assertEquals(2, storage.actual().getLong("sequence", 0));
            assertTrue("No enabling button was pressed", notice());
            assertTrue(policy.enabled());
            AccessibilityNodeInfo root = instrumentation.getUiAutomation().getRootInActiveWindow();
            assertNotNull(root);
            assertTrue(root.findAccessibilityNodeInfosByText("Возражаю / Object").get(0).performAction(AccessibilityNodeInfo.ACTION_CLICK));
            long stopped = SystemClock.elapsedRealtime() + 5000;
            while (policy.enabled() && SystemClock.elapsedRealtime() < stopped) SystemClock.sleep(50);
            assertFalse(policy.enabled());
            assertTrue(policy.pending());
            foreground();
            assertFalse("Reentry must not undo objection", notice());
            assertFalse(policy.enabled());
        } finally { invoke(upload, "detach"); }
    }
    @Test public void drawnNoticeStorageFailureDoesNotStartCollection() throws Exception {
        BasicMetadataStorageRuntimeTest.Storage storage = new BasicMetadataStorageRuntimeTest.Storage("metadata-ui-fault-" + UUID.randomUUID());
        TechnicalMetadataUpload upload = install(storage);
        storage.fail = true;
        try {
            foreground();
            if (BuildConfig.BASIC_METADATA_APPROVED) {
                awaitNotice();
                TechnicalMetadataPolicy policy = (TechnicalMetadataPolicy) field(upload, "policy");
                long deadline = SystemClock.elapsedRealtime() + 5000;
                while (!policy.faulted() && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(50);
                assertTrue(policy.faulted());
                assertFalse(policy.enabled());
            }
            assertEquals(1, storage.actual().getLong("sequence", 0));
            assertFalse(storage.actual().contains("notice_policy"));
            assertNull(field(upload, "callback"));
        } finally {
            invoke(upload, "detach");
            if (notice()) instrumentation.sendKeyDownUpSync(KeyEvent.KEYCODE_BACK);
        }
    }
    @Test public void existingOffNeverShowsEnablingNotice() throws Exception {
        BasicMetadataStorageRuntimeTest.Storage storage = new BasicMetadataStorageRuntimeTest.Storage("metadata-ui-off-" + UUID.randomUUID());
        assertTrue(storage.actual().edit().putBoolean("enabled", false).putLong("epoch", 7).putLong("sequence", 9).commit());
        TechnicalMetadataUpload upload = install(storage);
        try {
            foreground();
            assertFalse(notice());
            assertFalse(((TechnicalMetadataPolicy) field(upload, "policy")).enabled());
            assertEquals(9, storage.actual().getLong("sequence", 0));
            assertNull(field(upload, "callback"));
        } finally { invoke(upload, "detach"); }
    }
}
