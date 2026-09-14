package com.familyconnect.app;

import android.content.Context;
import com.google.gson.JsonObject;
import java.io.*;
import java.security.KeyStore;
import java.util.Arrays;

/** App worker only. Existing owner serializes enrollment against service/profile operations. */
final class ControlEnrollmentAndroid implements ControlEnrollment.Local {
    private final Context context;private final ControlEnrollmentVault vault;
    ControlEnrollmentAndroid(Context context){this.context=context.getApplicationContext();vault=new ControlEnrollmentVault(this.context);}
    private boolean marker(String name)throws Exception {
        for(String suffix:new String[]{"",".bak",".new"})if(new File(context.getNoBackupFilesDir(),"control-"+name+".enc"+suffix).exists())return true;
        KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);return keys.containsAlias("family-connect-control-"+name+"-v1");
    }
    public boolean present()throws Exception{return marker("enrollment");}
    public boolean otherState()throws Exception{return marker("identity")||marker("journal");}
    public JsonObject read()throws Exception {byte[] raw=vault.read();try{return ControlJson.parse(raw).getAsJsonObject();}finally{Arrays.fill(raw,(byte)0);}}
    public void create(JsonObject r)throws Exception {byte[] raw=ControlJournal.encode(r);try{vault.create(raw);}finally{Arrays.fill(raw,(byte)0);}}
    public void save(JsonObject r)throws Exception {byte[] raw=ControlJournal.encode(r);try{vault.write(raw);}finally{Arrays.fill(raw,(byte)0);}}
    public ControlIdentity prepare(boolean initializing)throws Exception {
        boolean identityPresent=marker("identity"),journalPresent=marker("journal");
        if(!identityPresent&&(!initializing||journalPresent))throw new IOException("Identity recovery required");
        ControlIdentityVault identities=new ControlIdentityVault(context);ControlIdentity identity=identityPresent?identities.load():identities.create();
        try {
            String version=context.getPackageManager().getPackageInfo(context.getPackageName(),0).versionName;
            if(version==null)throw new IOException("Missing application version");version=version.split("-",2)[0];ControlProtocol.version(version);
            ControlJournal journal=new ControlJournal(new ControlJournalVault(context),identity,ControlTrust.anchor(context),version);
            if(!journalPresent){if(!initializing)throw new IOException("Journal recovery required");journal.initialize();}
            JsonObject record=journal.read();
            if(initializing&&(record.get("floor").getAsLong()!=0||!record.get("committed").isJsonNull()||!record.get("staged").isJsonNull()))
                throw new IOException("Existing journal requires recovery");
            if(!record.get("staged").isJsonNull())throw new IOException("VPN recovery required");
            return identity;
        }catch(Exception|LinkageError failure){identity.close();throw failure;}
    }
}
