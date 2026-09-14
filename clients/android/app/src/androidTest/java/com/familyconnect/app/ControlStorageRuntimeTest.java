package com.familyconnect.app;

import android.content.Context;
import android.os.Bundle;
import android.util.AtomicFile;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.google.gson.JsonObject;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.security.KeyStore;
import java.util.Arrays;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Disposable emulator only. Runner also executes prepare/recover in separate processes.
 * No fixture or generated private material is exported to the host or test output.
 */
@RunWith(AndroidJUnit4.class)
public class ControlStorageRuntimeTest {
    private final Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
    private File file(String name){return new File(context.getNoBackupFilesDir(),"control-"+name+".enc");}
    private KeyStore keys()throws Exception{KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);return keys;}
    private void disposable()throws Exception{
        assertTrue("Disposable emulator required",android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        assertEquals("Runner must explicitly authorize storage tests","true",InstrumentationRegistry.getArguments().getString("fc_disposable"));
        ControlOperations.APP.requireIdle();
        assertEquals("off",ConnectionService.status);
        for(Transport t:Transport.values())assertFalse("Existing VPN profile",new ProfileStore(context,t).present());
    }
    private void absent()throws Exception{
        for(String name:new String[]{"identity","journal","enrollment"}){
            for(String suffix:new String[]{"",".bak",".new"})assertFalse("Existing managed storage",new File(file(name)+suffix).exists());
            assertFalse("Existing managed key",keys().containsAlias("family-connect-control-"+name+"-v1"));
        }
    }
    private ControlJournal journal(ControlIdentity identity)throws Exception{
        return new ControlJournal(new ControlJournalVault(context),identity,ControlTrust.anchor(context),"0.1.2");
    }
    private static final ControlTransaction.Application NO_APPLY=new ControlTransaction.Application(){
        public JsonObject snapshot(JsonObject previous){throw new AssertionError("Invalid envelope reached snapshot");}
        public void apply(ControlProtocol.Verified v,JsonObject baseline){throw new AssertionError("Invalid envelope applied");}
        public boolean healthy(ControlProtocol.Verified v){throw new AssertionError("Invalid envelope reached health");}
        public void rollback(ControlProtocol.Verified c,ControlProtocol.Verified p,JsonObject b,boolean restore){throw new AssertionError("Unexpected rollback");}
    };
    private void prepare()throws Exception{
        absent();
        try(ControlIdentity identity=new ControlIdentityVault(context).create()){
            ControlJournal journal=journal(identity);journal.initialize();
            assertNull("Wrapping key must be nonexportable",keys().getKey("family-connect-control-identity-v1",null).getEncoded());
            assertNull("Wrapping key must be nonexportable",keys().getKey("family-connect-control-journal-v1",null).getEncoded());
            assertThrows(IOException.class,()->new ControlIdentityVault(context).create());
            assertThrows(IOException.class,journal::initialize);
            assertEquals("REJECTED",new ControlTransaction(journal,NO_APPLY,()->1000).receive(new byte[]{'{','}'}));
            JsonObject state=journal.read();assertEquals(1,state.getAsJsonArray("outbox").size());
            assertEquals(identity.reference(),journal.receipt(state.getAsJsonArray("outbox").get(0)).get("device").getAsString());
            // Android AtomicFile must retain the previous base after an interrupted write.
            AtomicFile disk=new AtomicFile(file("journal"));
            try(FileOutputStream pending=disk.startWrite()){pending.write(new byte[]{1,2,3});pending.getFD().sync();}
            assertTrue(new File(file("journal")+".new").exists());
        }
    }
    private void recover()throws Exception{
        try(ControlIdentity identity=new ControlIdentityVault(context).load()){
            ControlJournal journal=journal(identity);JsonObject before=journal.read();
            assertEquals(1000,before.get("last_now").getAsLong());
            assertEquals(1,before.getAsJsonArray("outbox").size());
            assertFalse("Interrupted temporary file retained",new File(file("journal")+".new").exists());
            ControlTransaction core=new ControlTransaction(journal,NO_APPLY,()->1000);
            assertEquals("IDLE",core.recover());
            assertEquals(before,journal.read());
            assertThrows(ControlProtocol.Rejected.class,()->new ControlTransaction(journal,NO_APPLY,()->999).recover());
            assertEquals(before,journal.read());
            assertFalse(core.flush(raw->{throw new IOException("relay offline");}));
            assertEquals(before,journal.read());
            // Fresh vault/core instances reload the same signed durable ACK after a lost send.
            ControlJournal reopened=journal(identity);
            assertTrue(new ControlTransaction(reopened,NO_APPLY,()->1000).flush(raw->{
                JsonObject body=ControlProtocol.verifyAck(raw);
                assertEquals(identity.reference(),body.get("device").getAsString());
                assertEquals("REJECTED",body.get("status").getAsString());return true;
            }));
            assertEquals(0,reopened.read().getAsJsonArray("outbox").size());
            assertEquals(1000,reopened.read().get("last_now").getAsLong());
            // Authenticated storage refuses corruption without silently recreating identity/state.
            for(String name:new String[]{"journal","identity"}){
                byte[] original=Files.readAllBytes(file(name).toPath()),bad=original.clone();bad[bad.length-1]^=1;
                Files.write(file(name).toPath(),bad);
                try{
                    if(name.equals("identity"))assertThrows(Exception.class,()->new ControlIdentityVault(context).load());
                    else assertThrows(Exception.class,()->new ControlJournalVault(context).write(new byte[]{'{','}'}));
                    assertArrayEquals(bad,Files.readAllBytes(file(name).toPath()));
                    assertThrows(IOException.class,()->new ControlIdentityVault(context).create());
                }finally{Files.write(file(name).toPath(),original);Arrays.fill(original,(byte)0);Arrays.fill(bad,(byte)0);}
            }
        }
    }
    private void cleanup()throws Exception{
        for(String name:new String[]{"identity","journal","enrollment"}){
            new AtomicFile(file(name)).delete();keys().deleteEntry("family-connect-control-"+name+"-v1");
        }
        absent();
    }
    @Test public void keystoreJournalAndOutboxSurviveRestart()throws Exception{
        disposable();Bundle args=InstrumentationRegistry.getArguments();String phase=args.getString("fc_storage_phase","roundtrip");
        assertTrue(Arrays.asList("roundtrip","prepare","recover").contains(phase));
        Bundle progress=new Bundle();progress.putString("fc_storage_pid",Integer.toString(android.os.Process.myPid()));
        InstrumentationRegistry.getInstrumentation().sendStatus(2,progress);
        if(phase.equals("prepare")){prepare();return;}
        if(phase.equals("roundtrip"))prepare();
        try{recover();}finally{cleanup();}
    }
}
