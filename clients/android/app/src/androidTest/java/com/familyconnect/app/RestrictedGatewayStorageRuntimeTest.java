package com.familyconnect.app;

import android.content.Context;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.KeyStore;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

@RunWith(AndroidJUnit4.class)
public class RestrictedGatewayStorageRuntimeTest {
    private static final byte[] PRIMARY="synthetic-primary-readiness".getBytes(StandardCharsets.US_ASCII);
    private static final byte[] SECONDARY="synthetic-secondary-readiness".getBytes(StandardCharsets.US_ASCII);
    private static final byte[] OWNER="disposable-mesh-storage-v1".getBytes(StandardCharsets.US_ASCII);
    private final Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();

    private File file(String name){return new File(context.getNoBackupFilesDir(),name);}
    private KeyStore keys()throws Exception{KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);return keys;}
    private String alias(String gateway){return "family-connect-restricted-readiness-v1"+RestrictedGateway.namespace(gateway);}
    private File vault(String gateway){return file("restricted-readiness"+RestrictedGateway.namespace(gateway)+".enc");}
    private File receipt(String gateway){return file("restricted-readiness-result-v1"+RestrictedGateway.namespace(gateway)+".json");}
    private File marker(){return file("disposable-mesh-storage-test.owner");}

    private void guard()throws Exception{
        assumeTrue("Explicit disposable storage opt-in", "true".equals(InstrumentationRegistry.getArguments().getString("fc_mesh_storage")));
        assertEquals("true",InstrumentationRegistry.getArguments().getString("fc_disposable"));
        assertTrue("Disposable emulator only",android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        assertEquals("off",ConnectionService.status);ControlOperations.APP.requireIdle();
        for(Transport transport:Transport.values())assertFalse("Existing VPN profile",new ProfileStore(context,transport).present());
    }

    private void prepare()throws Exception{
        assertFalse("Existing test owner",marker().exists());
        for(String gateway:new String[]{RestrictedGateway.PRIMARY,RestrictedGateway.SECONDARY}){
            assertFalse("Existing readiness key",keys().containsAlias(alias(gateway)));
            for(File path:new File[]{vault(gateway),receipt(gateway)})for(String suffix:new String[]{"",".new",".bak"})
                assertFalse("Existing readiness state",new File(path+suffix).exists());
        }
        Files.write(marker().toPath(),OWNER);
        RestrictedVault primary=new RestrictedVault(context);
        RestrictedVault secondary=new RestrictedVault(context,RestrictedGateway.SECONDARY);
        assertNull(primary.read());assertNull(secondary.read());
        primary.write(PRIMARY);assertNull(secondary.read());secondary.write(SECONDARY);
        new ReadinessReceiptStore(context).write(PRIMARY);
        new ReadinessReceiptStore(context,RestrictedGateway.SECONDARY).write(SECONDARY);
        assertArrayEquals(PRIMARY,new RestrictedVault(context,RestrictedGateway.PRIMARY).read());
        assertArrayEquals(SECONDARY,new RestrictedVault(context,RestrictedGateway.SECONDARY).read());
    }

    private void recover()throws Exception{
        assertArrayEquals(OWNER,Files.readAllBytes(marker().toPath()));
        try{
            RestrictedVault primary=new RestrictedVault(context);
            RestrictedVault secondary=new RestrictedVault(context,RestrictedGateway.SECONDARY);
            assertArrayEquals(PRIMARY,primary.read());assertArrayEquals(SECONDARY,secondary.read());
            assertArrayEquals(PRIMARY,new ReadinessReceiptStore(context,RestrictedGateway.PRIMARY).read());
            assertArrayEquals(SECONDARY,new ReadinessReceiptStore(context,RestrictedGateway.SECONDARY).read());
            byte[] original=Files.readAllBytes(vault(RestrictedGateway.SECONDARY).toPath());
            byte[] retainedPrimary=Files.readAllBytes(vault(RestrictedGateway.PRIMARY).toPath());
            Files.write(vault(RestrictedGateway.SECONDARY).toPath(),retainedPrimary);
            assertThrows(Exception.class,secondary::read);
            assertArrayEquals(PRIMARY,primary.read());
            Files.write(vault(RestrictedGateway.SECONDARY).toPath(),original);
            assertArrayEquals(SECONDARY,secondary.read());
            Files.delete(vault(RestrictedGateway.SECONDARY).toPath());
            assertThrows(Exception.class,secondary::read);
            assertThrows(Exception.class,()->secondary.write(SECONDARY));
            Files.write(vault(RestrictedGateway.SECONDARY).toPath(),original);
            keys().deleteEntry(alias(RestrictedGateway.SECONDARY));
            assertThrows(Exception.class,secondary::read);
            assertThrows(Exception.class,()->secondary.write(SECONDARY));
            assertFalse(keys().containsAlias(alias(RestrictedGateway.SECONDARY)));
            assertArrayEquals(retainedPrimary,Files.readAllBytes(vault(RestrictedGateway.PRIMARY).toPath()));
            assertArrayEquals(PRIMARY,primary.read());
        }finally{
            for(String gateway:new String[]{RestrictedGateway.PRIMARY,RestrictedGateway.SECONDARY}){
                for(File path:new File[]{vault(gateway),receipt(gateway)})for(String suffix:new String[]{"",".new",".bak"})
                    Files.deleteIfExists(new File(path+suffix).toPath());
                keys().deleteEntry(alias(gateway));
            }
            Files.delete(marker().toPath());
        }
    }

    @Test public void scopedReadinessSurvivesProcessRestartAndRejectsCrossNodeCiphertext()throws Exception{
        guard();String stage=InstrumentationRegistry.getArguments().getString("fc_mesh_stage");
        assertTrue("Explicit prepare/recover stage", "prepare".equals(stage)||"recover".equals(stage));
        if("prepare".equals(stage))prepare();else recover();
    }
}
