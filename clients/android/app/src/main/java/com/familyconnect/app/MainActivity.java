package com.familyconnect.app;

import android.Manifest;
import android.app.Activity;
import android.content.*;
import android.graphics.Color;
import android.net.VpnService;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.amnezia.awg.config.Config;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.net.URL;
import javax.net.ssl.HttpsURLConnection;
import java.util.concurrent.*;

public final class MainActivity extends LocalizedActivity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private TextView state,detail;
    private TerminalUi.Dial dial;
    private Button toggle,importButton,checkButton,forgetButton,enrollButton,controlButton,rnsButton;
    private boolean pendingRns;
    private byte[] pendingControl;
    private long seenControlResult=-1;
    private volatile ControlEnrollmentHttp enrollmentHttp;
    private ProfileStore store;
    private Spinner transportPicker;
    private Button gatewayButton;
    private String pendingGateway;
    private TerminalToggle autoMode;
    private Transport selected=Transport.WG;
    private String pendingTransport="wg";
    private boolean busy=false;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,500);}};
    private TextView healthLabel;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        try{selected=Transport.parse(getPreferences(MODE_PRIVATE).getString("transport","wg"));}catch(IllegalArgumentException ignored){}
        pendingTransport=saved==null?selected.id:saved.getString("pendingTransport",selected.id);
        store=new ProfileStore(this,selected);
        LinearLayout content=TerminalUi.screen(this,getString(R.string.terminal_tagline));
        TerminalUi.button(content,R.string.chat_title,()->startActivity(new Intent(this,ChatActivity.class)));
        LinearLayout connection=TerminalUi.section(content,getString(R.string.terminal_status));
        dial=new TerminalUi.Dial(this);connection.addView(dial,new LinearLayout.LayoutParams(-1,dp(188)));
        state=label(connection,"",23,TerminalUi.TEXT);
        healthLabel=label(connection,"",14,TerminalUi.MUTED);
        LinearLayout route=TerminalUi.section(content,getString(R.string.terminal_route));
        gatewayButton=button(route,R.string.choose_gateway,this::chooseGateway);
        label(route,getString(R.string.route),13,TerminalUi.MUTED);
        autoMode=new TerminalToggle(this);autoMode.setText("Auto · WG → AWG → TCP");TerminalUi.textStyle(autoMode,14,TerminalUi.TEXT);autoMode.setMinHeight(dp(48));autoMode.setChecked(getPreferences(MODE_PRIVATE).getBoolean("auto",false));route.addView(autoMode);
        autoMode.setOnCheckedChangeListener((v,on)->{getPreferences(MODE_PRIVATE).edit().putBoolean("auto",on).apply();render();});
        transportPicker=new Spinner(this);TerminalUi.picker(transportPicker,new String[]{"WireGuard","AmneziaWG","TCP · REALITY"});transportPicker.setContentDescription(getString(R.string.terminal_transport));
        transportPicker.setSelection(selected.ordinal());route.addView(transportPicker,new LinearLayout.LayoutParams(-1,-2));
        transportPicker.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id){
                if(!ConnectionService.status.equals("off"))return;
                selected=Transport.values()[position];store=new ProfileStore(MainActivity.this,selected);getPreferences(MODE_PRIVATE).edit().putString("transport",selected.id).apply();render();
            }
        });
        toggle=button(connection,R.string.connect,()->toggle());
        LinearLayout settings=TerminalUi.section(content,getString(R.string.terminal_settings));
        importButton=button(settings,R.string.import_profile,()->{
            if(!ConnectionService.status.equals("off")){detail.setText(R.string.disconnect_first);return;}
            Intent picker=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(picker,10);
        });
        enrollButton=button(settings,R.string.enroll_device,()->enrollDevice());
        rnsButton=button(settings,R.string.rns_connect,()->{
            if(busy||!ConnectionService.status.equals("off"))return;
            new android.app.AlertDialog.Builder(this).setTitle(R.string.rns_connect).setMessage(R.string.rns_hint)
                .setNegativeButton(android.R.string.cancel,null).setPositiveButton(android.R.string.ok,(d,w)->{
                    pendingRns=true;Intent permission=VpnService.prepare(this);
                    if(permission!=null)startActivityForResult(permission,18);else continueRns();
                }).show();
        });
        controlButton=button(settings,R.string.control_file,()->{
            if(busy||!ConnectionService.status.equals("off"))return;
            new android.app.AlertDialog.Builder(this).setTitle(R.string.control_file).setMessage(R.string.control_file_hint)
                .setNegativeButton(android.R.string.cancel,null).setPositiveButton(android.R.string.ok,(d,w)->
                    startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE),15)).show();
        });
        checkButton=button(settings,R.string.check_ip,()->checkIp());
        forgetButton=button(settings,R.string.forget,()->{
            if(!ConnectionService.status.equals("off"))return;
            busy=true;render();final ProfileStore removing=store;
            worker.execute(()->{
                int message=R.string.no_profile;
                try{removing.clear();}catch(Exception e){message=R.string.failed;}
                final int result=message;
                runOnUiThread(()->{if(isDestroyed())return;busy=false;detail.setText(result);render();});
            });
        });
        label(settings,getString(R.string.hint),13,TerminalUi.MUTED);detail=label(settings,"",14,TerminalUi.AMBER);
        TerminalUi.label(content,getString(R.string.terminal_footer),11,TerminalUi.MUTED);
    }
    private int dp(int value){return (int)(getResources().getDisplayMetrics().density*value);}
    private TextView label(LinearLayout parent,String text,int size,int color){return TerminalUi.label(parent,text,size,color);}
    private Button button(LinearLayout parent,int resource,Runnable action){return TerminalUi.button(parent,resource,action);}
    private static void textIfChanged(TextView view,CharSequence text){
        if(!android.text.TextUtils.equals(view.getText(),text))view.setText(text);
    }
    private void render(){
        if(toggle==null||detail==null)return;
        String value=ConnectionService.status;
        gatewayButton.setEnabled(!busy&&!value.equals("connecting")&&!value.equals("cleanup-required"));
        textIfChanged(gatewayButton,getString(R.string.choose_gateway)+": "+gatewayName(getSharedPreferences("gateway-selection",MODE_PRIVATE).getString("gateway","")));
        if(!value.equals("off")&&!"auto".equals(ConnectionService.requestedTransport)){
            Transport active=Transport.parse(ConnectionService.activeTransport);
            if(selected!=active){selected=active;store=new ProfileStore(this,active);transportPicker.setSelection(active.ordinal());getPreferences(MODE_PRIVATE).edit().putString("transport",active.id).apply();}
        }
        boolean on=value.equals("on"),waiting=value.equals("connecting")||value.equals("cleanup-required");
        textIfChanged(state,getString(on?R.string.on:waiting?R.string.connecting:R.string.off));
        textIfChanged(healthLabel,!on?"":getString(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:ConnectionService.healthStatus.equals("unavailable")?R.string.health_unavailable:R.string.health_checking));
        dial.update(value,ConnectionService.healthStatus);textIfChanged(toggle,getString(on||waiting?R.string.disconnect:R.string.connect));
        boolean available=store.exists();if(autoMode.isChecked()){available=false;for(Transport t:Transport.values())available|=new ProfileStore(this,t).exists();}
        autoMode.setEnabled(!busy&&!on&&!waiting);toggle.setEnabled(!busy&&(on||waiting||available));transportPicker.setEnabled(!busy&&!on&&!waiting);importButton.setEnabled(!busy&&!on&&!waiting);
        enrollButton.setEnabled(!busy&&!on&&!waiting);controlButton.setEnabled(!busy&&!on&&!waiting);rnsButton.setEnabled(!busy&&!on&&!waiting);
        forgetButton.setEnabled(!busy&&!on&&!waiting&&store.exists());checkButton.setEnabled(!busy&&on);
        if(ConnectionService.failed)textIfChanged(detail,getString(R.string.failed));
        else if(!value.equals("off")&&"auto".equals(ConnectionService.requestedTransport))textIfChanged(detail,"Auto · "+ConnectionService.activeTransport.toUpperCase(java.util.Locale.ROOT));
        showControlResult();
    }
    private void showControlResult(){
        long id=ConnectionService.controlResultId;if(id==seenControlResult)return;seenControlResult=id;
        String outcome=ConnectionService.controlOutcome;if(outcome==null)return;
        int message="SELECTED".equals(outcome)?R.string.gateway_selected:"COMMITTED".equals(outcome)?R.string.control_committed:"REJECTED".equals(outcome)?R.string.control_rejected:
            "ROLLED_BACK".equals(outcome)?R.string.control_rolled_back:"BUSY".equals(outcome)?R.string.disconnect_first:"UNAVAILABLE".equals(outcome)?R.string.rns_unavailable:R.string.control_failed;
        detail.setText(message);
    }
    private String gatewayName(String id){
        if(id.equals("tcp-android-pilot"))return getString(R.string.gateway_russia);
        if(id.equals("amsterdam"))return getString(R.string.gateway_netherlands);
        return id.isEmpty()?getString(R.string.gateway_default):id;
    }
    private void chooseGateway(){
        if(busy)return;busy=true;render();
        worker.execute(()->{
            java.util.ArrayList<String> ids=new java.util.ArrayList<>();
            try{
                synchronized(ControlJournal.OWNER){
                    try(ControlIdentity identity=new ControlIdentityVault(this).load()){
                        String version=getPackageManager().getPackageInfo(getPackageName(),0).versionName.split("-",2)[0];
                        ControlJournal journal=new ControlJournal(new ControlJournalVault(this),identity,ControlTrust.anchor(this),version);
                        com.google.gson.JsonObject record=journal.read();long now=System.currentTimeMillis()/1000;
                        if(record.has("selected_gateway"))getSharedPreferences("gateway-selection",MODE_PRIVATE).edit()
                            .putString("gateway",record.get("selected_gateway").isJsonNull()?"":ControlJson.text(record.get("selected_gateway"))).apply();
                        if(now<ControlJson.integer(record.get("last_now"),0)||!record.get("staged").isJsonNull())throw new IOException();
                        ControlProtocol.Verified config=journal.unpack(record.getAsJsonObject("committed"),now);
                        for(com.google.gson.JsonElement item:config.state().getAsJsonArray("transport_profiles")){
                            String id=ControlJson.text(item.getAsJsonObject().get("gateway_id"));if(!ids.contains(id))ids.add(id);
                        }
                    }
                }
            }catch(Exception failure){ids.clear();}
            runOnUiThread(()->{
                if(isDestroyed())return;busy=false;render();
                if(ids.isEmpty()){detail.setText(R.string.gateway_unavailable);return;}
                String[] names=new String[ids.size()];for(int i=0;i<names.length;i++)names[i]=gatewayName(ids.get(i));
                new android.app.AlertDialog.Builder(this).setTitle(R.string.choose_gateway).setItems(names,(d,index)->{
                    pendingGateway=ids.get(index);busy=true;render();
                    Intent permission=VpnService.prepare(this);
                    if(permission!=null)startActivityForResult(permission,20);else continueGateway();
                }).setNegativeButton(android.R.string.cancel,null).show();
            });
        });
    }
    private void continueRns(){
        if(!pendingRns)return;
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},19);
        else startRns();
    }
    private void continueGateway(){
        if(pendingGateway==null)return;
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},21);
        else startGateway();
    }
    private void startGateway(){
        String id=pendingGateway;pendingGateway=null;busy=false;
        if(id!=null&&!isDestroyed())try{
            startForegroundService(new Intent(this,ConnectionService.class).setAction("select-gateway").putExtra("gateway",id));
            detail.setText(R.string.control_applying);
        }catch(Exception failure){detail.setText(R.string.control_failed);}
        render();
    }
    private void startRns(){
        if(!pendingRns)return;pendingRns=false;
        startForegroundService(new Intent(this,ConnectionService.class).setAction("sync-control"));
    }
    private void continueControl(){
        if(pendingControl==null){busy=false;render();return;}
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},16);
        else startControl();
    }
    private void startControl(){
        byte[] raw=pendingControl;pendingControl=null;busy=false;
        if(raw==null||isDestroyed()){render();return;}
        try{startForegroundService(new Intent(this,ConnectionService.class).setAction("apply-control").putExtra("envelope",raw));detail.setText(R.string.control_applying);}
        catch(Exception e){detail.setText(R.string.control_failed);}
        render();
    }
    private void readControl(Intent data){
        if(data==null||data.getData()==null)return;
        busy=true;render();android.net.Uri uri=data.getData();
        worker.execute(()->{
            byte[] raw=null;try(InputStream input=getContentResolver().openInputStream(uri)){raw=ControlIntake.read(input);}catch(Exception e){}
            final byte[] envelope=raw;runOnUiThread(()->{
                if(isDestroyed())return;
                if(envelope==null){busy=false;detail.setText(R.string.control_failed);render();return;}
                pendingControl=envelope;Intent permission=VpnService.prepare(this);
                if(permission!=null)startActivityForResult(permission,17);else continueControl();
            });
        });
    }
    private void enrollDevice(){
        if(busy||!ConnectionService.status.equals("off"))return;
        LinearLayout form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),0,dp(20),0);
        EditText server=new EditText(this);server.setHint(R.string.enroll_server);server.setSingleLine(true);
        server.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_VARIATION_URI);server.setSaveEnabled(false);server.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);form.addView(server);
        EditText invitation=new EditText(this);invitation.setHint(R.string.enroll_invitation);invitation.setSingleLine(true);
        invitation.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);invitation.setSaveEnabled(false);invitation.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);
        invitation.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(64)});form.addView(invitation);
        android.app.AlertDialog dialog=new android.app.AlertDialog.Builder(this).setTitle(R.string.enroll_device)
            .setMessage(R.string.enroll_explanation).setView(form).setNegativeButton(android.R.string.cancel,null)
            .setPositiveButton(R.string.enroll_continue,(d,w)->{
                String origin=server.getText().toString().trim(),token=invitation.getText().toString();invitation.setText("");
                busy=true;ConnectionService.failed=false;detail.setText(R.string.enroll_working);render();
                ControlEnrollmentHttp http=new ControlEnrollmentHttp();enrollmentHttp=http;
                worker.execute(()->{
                    String identity=null;
                    try{identity=new ControlEnrollment(new ControlEnrollmentAndroid(this),http,()->System.currentTimeMillis()/1000).enroll(origin,token);}
                    catch(Exception|LinkageError failure){/* No tokens, proofs or private state in logs/UI. */}
                    finally{http.close();enrollmentHttp=null;}
                    final String result=identity;runOnUiThread(()->{
                        if(isDestroyed())return;busy=false;detail.setText(result==null?getString(R.string.enroll_failed):getString(R.string.enroll_done,result));render();
                    });
                });
            }).create();
        dialog.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);dialog.show();
    }
    private void toggle(){
        if(!ConnectionService.status.equals("off")){startService(new Intent(this,ConnectionService.class).setAction("disconnect"));return;}
        pendingTransport=autoMode.isChecked()?"auto":selected.id;Intent permission=VpnService.prepare(this);
        if(permission!=null)startActivityForResult(permission,11);else continueStart();
    }
    private void continueStart(){
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},12);
        else startVpn();
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){
        super.onRequestPermissionsResult(request,permissions,results);if(request==12)startVpn();else if(request==16)startControl();else if(request==19)startRns();else if(request==21)startGateway();
    }
    private void startVpn(){ConnectionService.requestedTransport=pendingTransport;if(!pendingTransport.equals("auto"))ConnectionService.activeTransport=pendingTransport;ConnectionService.status="connecting";startForegroundService(new Intent(this,ConnectionService.class).setAction("connect").putExtra("transport",pendingTransport));render();}
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request==20){if(result==RESULT_OK)continueGateway();else{pendingGateway=null;busy=false;detail.setText(R.string.permission_denied);render();}return;}
        if(request==11){if(result==RESULT_OK)continueStart();else detail.setText(R.string.permission_denied);return;}
        if(request==18){if(result==RESULT_OK)continueRns();else{pendingRns=false;detail.setText(R.string.permission_denied);}return;}
        if(request==15){if(result==RESULT_OK)readControl(data);return;}
        if(request==17){if(result==RESULT_OK)continueControl();else{pendingControl=null;busy=false;detail.setText(R.string.permission_denied);render();}return;}
        if(request!=10||result!=RESULT_OK||data==null||data.getData()==null)return;
        busy=true;render();android.net.Uri uri=data.getData();final Transport importing=selected;final ProfileStore importingStore=store;
        worker.execute(()->{
            int message=R.string.profile_ready;
            try(InputStream input=getContentResolver().openInputStream(uri)) {
                if(input==null)throw new IOException();ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[1024];int count;
                while((count=input.read(buffer))!=-1){if(bytes.size()+count>ProfileValidator.LIMIT)throw new IOException();bytes.write(buffer,0,count);}
                String profile=ProfileValidator.validate(bytes.toString(StandardCharsets.UTF_8.name()),importing);
                if(importing!=Transport.TCP)Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8)));
                importingStore.save(profile);ConnectionService.failed=false;
            }catch(Exception e){message=R.string.import_failed;}
            int finalMessage=message;runOnUiThread(()->{busy=false;detail.setText(finalMessage);render();});
        });
    }
    private void checkIp(){
        busy=true;detail.setText(R.string.checking);render();
        final long session=ConnectionService.sessionId;final String source=ConnectionService.vpnSource;
        worker.execute(()->{
            String result=getString(R.string.failed);
            HttpsURLConnection connection=null;
            try {
                if(!ConnectionService.status.equals("on"))throw new IOException();
                VpnHealth binding=new VpnHealth(this);
                android.net.Network network=binding.find(source);
                if(network==null||session!=ConnectionService.sessionId)throw new IOException();
                connection=(HttpsURLConnection)network.openConnection(new URL("https://www.cloudflare.com/cdn-cgi/trace"));
                connection.setConnectTimeout(10000);connection.setReadTimeout(10000);connection.setInstanceFollowRedirects(false);
                if(connection.getResponseCode()!=200)throw new IOException();
                String ip="?",region="?";int total=0;
                try(BufferedReader reader=new BufferedReader(new InputStreamReader(connection.getInputStream(),StandardCharsets.UTF_8))){
                    String line;while((line=reader.readLine())!=null){total+=line.length();if(total>4096)throw new IOException();if(line.startsWith("ip="))ip=line.substring(3);if(line.startsWith("loc="))region=line.substring(4);}
                }
                if(!ConnectionService.status.equals("on")||session!=ConnectionService.sessionId||!network.equals(binding.find(source)))throw new IOException();result="IP: "+ip+" · "+region;
            }catch(Exception ignored){}finally{if(connection!=null)connection.disconnect();}
            String message=result;runOnUiThread(()->{busy=false;detail.setText(session==ConnectionService.sessionId&&ConnectionService.status.equals("on")?message:getString(R.string.failed));render();});
        });
    }
    @Override protected void onSaveInstanceState(Bundle saved){saved.putString("pendingTransport",pendingTransport);super.onSaveInstanceState(saved);}
    private void refreshGatewayChoice(){
        worker.execute(()->{
            synchronized(ControlJournal.OWNER){
                try(ControlIdentity identity=new ControlIdentityVault(this).load()){
                    String version=getPackageManager().getPackageInfo(getPackageName(),0).versionName.split("-",2)[0];
                    var journal=new ControlJournal(new ControlJournalVault(this),identity,ControlTrust.anchor(this),version);
                    var record=journal.read();
                    if(record.has("selected_gateway"))getSharedPreferences("gateway-selection",MODE_PRIVATE).edit()
                        .putString("gateway",record.get("selected_gateway").isJsonNull()?"":ControlJson.text(record.get("selected_gateway"))).apply();
                }catch(Exception unavailable){/* No creation/reset of managed state on a UI read. */}
            }
            runOnUiThread(()->{if(!isDestroyed())render();});
        });
    }
    @Override protected void onResume(){super.onResume();handler.post(refresh);refreshGatewayChoice();}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
    @Override protected void onDestroy(){pendingRns=false;pendingControl=null;handler.removeCallbacks(refresh);ControlEnrollmentHttp e=enrollmentHttp;if(e!=null)e.close();worker.shutdownNow();super.onDestroy();}
}
