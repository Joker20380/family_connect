package com.familyconnect.app;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

public final class OrchestratorDiagnosticActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String mode=getIntent().getStringExtra("mode");
        if("failure".equals(mode)) {
            getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).edit().putBoolean("fail_active",true).apply();finish();return;
        }
        if(!"prepare".equals(mode)||!ConnectionService.status.equals("off")) { finish();return; }
        new Thread(()->{
            try {
                if(ControlMutationGate.managed(this))throw new IllegalStateException();
                for(Transport type:Transport.values()) {
                    File file=new File(getNoBackupFilesDir(),"auto-"+type.id+".profile");
                    if(file.isFile()) {
                        if(file.length()>ProfileValidator.LIMIT)throw new IllegalArgumentException();
                        new ProfileStore(this,type).save(ProfileValidator.validate(new String(Files.readAllBytes(file.toPath()),StandardCharsets.UTF_8),type));
                        Files.delete(file.toPath());
                    }
                }
                boolean committed=getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).edit().clear()
                    .putBoolean("deny_awg",getIntent().getBooleanExtra("deny_normal",false)||getIntent().getBooleanExtra("deny_primary",false))
                    .putBoolean("deny_wg",getIntent().getBooleanExtra("deny_normal",false))
                    .putBoolean("deny_tcp",getIntent().getBooleanExtra("deny_normal",false)).commit();
                if(!committed)throw new IllegalStateException();
                if(getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).getBoolean("deny_awg",false)!=(getIntent().getBooleanExtra("deny_normal",false)||getIntent().getBooleanExtra("deny_primary",false))
                    ||getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).getBoolean("deny_wg",false)!=getIntent().getBooleanExtra("deny_normal",false)
                    ||getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).getBoolean("deny_tcp",false)!=getIntent().getBooleanExtra("deny_normal",false))throw new IllegalStateException();
                if(getIntent().getBooleanExtra("reset_hint",false))getSharedPreferences("connectivity",MODE_PRIVATE).edit().remove("normal_hint").apply();
                getSharedPreferences("connectivity",MODE_PRIVATE).edit().putString("preferred","awg").apply();
                runOnUiThread(()->{
                    boolean opened=DiagnosticLauncher.open(new DiagnosticLauncher.Host<Intent>() {
                        public Intent resolve(){return getPackageManager().getLaunchIntentForPackage(getPackageName());}
                        public void start(Intent launch){startActivity(launch);}
                    });
                    if(!opened)getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).edit().clear().commit();
                    evidence(opened,opened?null:"LAUNCHER_UNAVAILABLE");finish();
                });
            }catch(Exception failure) { evidence(false,failure.getClass().getSimpleName());runOnUiThread(this::finish); }
        },"fc-auto-diagnostic").start();
    }
    private void evidence(boolean ready,String failure) {
        try(java.io.FileOutputStream output=openFileOutput("orchestrator-prepared.json",MODE_PRIVATE)) {
            org.json.JSONObject record=new org.json.JSONObject();record.put("ready",ready);record.put("failure",failure);
            boolean awg=getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).getBoolean("deny_awg",false);
            boolean wg=getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).getBoolean("deny_wg",false);
            boolean tcp=getSharedPreferences("orchestrator-diagnostic",MODE_PRIVATE).getBoolean("deny_tcp",false);
            record.put("acceptance_override",awg&&wg&&tcp?"ON":!awg&&!wg&&!tcp?"OFF":"PARTIAL");
            output.write(record.toString().getBytes(StandardCharsets.UTF_8));output.getFD().sync();
        }catch(Exception ignored){}
    }
}
