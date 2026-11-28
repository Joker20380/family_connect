package com.familyconnect.app;

import android.content.Context;
import android.content.ContextWrapper;
import android.content.SharedPreferences;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.File;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.UUID;
import org.junit.Test;
import static org.junit.Assert.*;

public class BasicMetadataStorageRuntimeTest {
    static final class Storage extends ContextWrapper {
        final String name;
        final File root;
        boolean fail, published;
        Storage(String name) {
            super(InstrumentationRegistry.getInstrumentation().getTargetContext());
            this.name = name;
            root = new File(super.getNoBackupFilesDir(), name);
            assertTrue(root.isDirectory() || root.mkdirs());
        }
        @Override public Context getApplicationContext() { return this; }
        @Override public File getNoBackupFilesDir() { return root; }
        @Override public File getFilesDir() { return root; }
        SharedPreferences actual() { return super.getSharedPreferences(name, MODE_PRIVATE); }
        @Override public SharedPreferences getSharedPreferences(String ignored, int mode) {
            SharedPreferences actual = actual();
            return (SharedPreferences) Proxy.newProxyInstance(getClassLoader(), new Class[]{SharedPreferences.class}, (proxy, method, args) -> {
                if (!method.getName().equals("edit")) return method.invoke(actual, args);
                SharedPreferences.Editor editor = actual.edit();
                return Proxy.newProxyInstance(getClassLoader(), new Class[]{SharedPreferences.Editor.class}, (target, call, values) -> {
                    if (call.getName().equals("commit") && fail) {
                        if (published) assertTrue(editor.commit());
                        return false;
                    }
                    Object result = call.invoke(editor, values);
                    return result == editor ? target : result;
                });
            });
        }
    }

    private TechnicalMetadataPolicy open(Storage storage) throws Exception {
        Constructor<TechnicalMetadataUpload> constructor = TechnicalMetadataUpload.class.getDeclaredConstructor(Context.class);
        constructor.setAccessible(true);
        TechnicalMetadataUpload upload = constructor.newInstance(storage);
        Field field = TechnicalMetadataUpload.class.getDeclaredField("policy");
        field.setAccessible(true);
        return (TechnicalMetadataPolicy) field.get(upload);
    }

    @Test public void nativeInitializationRefusalAndRestoredBinding() throws Exception {
        Storage storage = new Storage("metadata-native-" + UUID.randomUUID());
        TechnicalMetadataPolicy policy = open(storage);
        assertTrue(policy.needsNotice());
        assertNull(policy.reserve());
        assertTrue(storage.actual().getLong("epoch", 0) > 0);
        assertTrue(storage.actual().getLong("sequence", 0) > 0);
        assertFalse(storage.actual().getBoolean("enabled", true));
        assertTrue(policy.noticeShown(true));
        TechnicalMetadataPolicy.Ticket old = policy.reserve();
        assertNotNull(old);
        assertTrue(policy.object());
        assertFalse(policy.acknowledge(old));
        policy = open(storage);
        assertTrue(policy.pending());
        assertFalse(policy.enabled());
        assertTrue(new File(storage.root, "technical-installation").delete());
        policy = open(storage);
        assertEquals("RESTORED_BLOCKED", policy.mode());
        assertFalse(policy.enabled());
        assertTrue(policy.pending());
        assertFalse(policy.reserve().sample);
    }

    @Test public void oldOffAndPendingRevokeSurviveNativeReopen() throws Exception {
        for (boolean pending : new boolean[]{false, true}) {
            Storage storage = new Storage("metadata-off-" + UUID.randomUUID());
            assertTrue(storage.actual().edit().putBoolean("enabled", false).putLong("epoch", 7)
                .putLong("sequence", 9).putBoolean("revoke_pending", pending).commit());
            TechnicalMetadataPolicy policy = open(storage);
            assertFalse(policy.enabled());
            assertFalse(policy.needsNotice());
            assertEquals(pending, policy.pending());
            assertEquals(7, storage.actual().getLong("epoch", 0));
            assertFalse(open(storage).enabled());
        }
    }

    @Test public void storageFailureAcrossSeparateInstrumentationProcesses() throws Exception {
        String phase = InstrumentationRegistry.getArguments().getString("fc_metadata_phase", "prepare");
        for (String stage : new String[]{"init", "notice", "reserve", "ack"}) {
            for (boolean published : new boolean[]{false, true}) {
                Storage storage = new Storage("metadata-fault-" + stage + "-" + published);
                if (phase.equals("verify")) {
                    assertTrue(new File(storage.root, "technical-storage-fault").isFile());
                    TechnicalMetadataPolicy recovered = open(storage);
                    assertTrue(recovered.faulted());
                    assertNull(recovered.reserve());
                    assertFalse(recovered.enabled());
                    continue;
                }
                assertFalse(new File(storage.root, "technical-storage-fault").exists());
                storage.published = published;
                storage.fail = stage.equals("init");
                TechnicalMetadataPolicy policy = open(storage);
                if (!stage.equals("init")) {
                    if (!stage.equals("notice")) assertTrue(policy.noticeShown(true));
                    TechnicalMetadataPolicy.Ticket revoke = null;
                    if (stage.equals("ack")) { assertTrue(policy.object()); revoke = policy.reserve(); }
                    storage.fail = true;
                    if (stage.equals("notice")) assertFalse(policy.noticeShown(true));
                    if (stage.equals("reserve")) assertNull(policy.reserve());
                    if (stage.equals("ack")) assertFalse(policy.acknowledge(revoke));
                }
                assertTrue(policy.faulted());
                assertTrue(new File(storage.root, "technical-storage-fault").isFile());
                assertFalse(open(storage).enabled());
            }
        }
    }
}
