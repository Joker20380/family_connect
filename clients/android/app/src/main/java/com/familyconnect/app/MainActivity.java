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

public final class MainActivity extends Activity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private TextView state,dot,detail;
    private Button toggle,importButton,checkButton,forgetButton,enrollButton,controlButton,rnsButton;
    private boolean pendingRns;
    private byte[] pendingControl;
    private long seenControlResult=-1;
    private volatile ControlEnrollmentHttp enrollmentHttp;
    private ProfileStore store;
    private Spinner transportPicker;
    private Switch autoMode;
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
        LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setGravity(Gravity.CENTER);
        content.setPadding(dp(28),dp(28),dp(28),dp(28));content.setBackgroundColor(Color.rgb(16,25,35));
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(content);setContentView(scroll);
        label(content,"FAMILY CONNECT",25,Color.rgb(102,219,192));label(content,getString(R.string.tagline),15,Color.LTGRAY);
        dot=label(content,"●",88,Color.GRAY);state=label(content,"",27,Color.WHITE);
        healthLabel=label(content,"",14,Color.LTGRAY);
        label(content,getString(R.string.route),15,Color.LTGRAY);
        autoMode=new Switch(this);autoMode.setText("Auto · WG → AWG → TCP");autoMode.setTextColor(Color.WHITE);autoMode.setChecked(getPreferences(MODE_PRIVATE).getBoolean("auto",false));content.addView(autoMode);
        autoMode.setOnCheckedChangeListener((v,on)->{getPreferences(MODE_PRIVATE).edit().putBoolean("auto",on).apply();render();});
        transportPicker=new Spinner(this);transportPicker.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"WireGuard","AmneziaWG 3.1","TCP · REALITY"}));
        transportPicker.setSelection(selected.ordinal());content.addView(transportPicker);
        transportPicker.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id){
                if(!ConnectionService.status.equals("off"))return;
                selected=Transport.values()[position];store=new ProfileStore(MainActivity.this,selected);getPreferences(MODE_PRIVATE).edit().putString("transport",selected.id).apply();render();
            }
        });
        toggle=button(content,R.string.connect,()->toggle());
        importButton=button(content,R.string.import_profile,()->{
            if(!ConnectionService.status.equals("off")){detail.setText(R.string.disconnect_first);return;}
            Intent picker=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(picker,10);
        });
        enrollButton=button(content,R.string.enroll_device,()->enrollDevice());
        rnsButton=button(content,R.string.rns_connect,()->{
            if(busy||!ConnectionService.status.equals("off"))return;
            new android.app.AlertDialog.Builder(this).setTitle(R.string.rns_connect).setMessage(R.string.rns_hint)
                .setNegativeButton(android.R.string.cancel,null).setPositiveButton(android.R.string.ok,(d,w)->{
                    pendingRns=true;Intent permission=VpnService.prepare(this);
                    if(permission!=null)startActivityForResult(permission,18);else continueRns();
                }).show();
        });
        controlButton=button(content,R.string.control_file,()->{
            if(busy||!ConnectionService.status.equals("off"))return;
            new android.app.AlertDialog.Builder(this).setTitle(R.string.control_file).setMessage(R.string.control_file_hint)
                .setNegativeButton(android.R.string.cancel,null).setPositiveButton(android.R.string.ok,(d,w)->
                    startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE),15)).show();
        });
        checkButton=button(content,R.string.check_ip,()->checkIp());
        forgetButton=button(content,R.string.forget,()->{
            if(!ConnectionService.status.equals("off"))return;
            busy=true;render();final ProfileStore removing=store;
            worker.execute(()->{
                int message=R.string.no_profile;
                try{removing.clear();}catch(Exception e){message=R.string.failed;}
                final int result=message;
                runOnUiThread(()->{if(isDestroyed())return;busy=false;detail.setText(result);render();});
            });
        });
        label(content,getString(R.string.hint),13,Color.LTGRAY);detail=label(content,"",14,Color.rgb(232,205,164));
    }
    private int dp(int value){return (int)(getResources().getDisplayMetrics().density*value);}
    private TextView label(LinearLayout parent,String text,int size,int color){
        TextView view=new TextView(this);view.setText(text);view.setTextSize(size);view.setTextColor(color);view.setGravity(Gravity.CENTER);view.setPadding(0,dp(8),0,dp(8));parent.addView(view);return view;
    }
    private Button button(LinearLayout parent,int resource,Runnable action){
        Button view=new Button(this);view.setText(resource);view.setAllCaps(false);view.setOnClickListener(v->action.run());
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(55));params.topMargin=dp(8);parent.addView(view,params);return view;
    }
    private void render(){
        if(toggle==null||detail==null)return;
        String value=ConnectionService.status;
        if(!value.equals("off")&&!"auto".equals(ConnectionService.requestedTransport)){
            Transport active=Transport.parse(ConnectionService.activeTransport);
            if(selected!=active){selected=active;store=new ProfileStore(this,active);transportPicker.setSelection(active.ordinal());getPreferences(MODE_PRIVATE).edit().putString("transport",active.id).apply();}
        }
        boolean on=value.equals("on"),waiting=value.equals("connecting")||value.equals("cleanup-required");
        state.setText(on?R.string.on:waiting?R.string.connecting:R.string.off);
        healthLabel.setText(!on?"":getString(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:ConnectionService.healthStatus.equals("unavailable")?R.string.health_unavailable:R.string.health_checking));
        dot.setTextColor(on?(ConnectionService.healthStatus.equals("unavailable")?Color.rgb(232,180,80):Color.rgb(102,219,192)):Color.GRAY);toggle.setText(on||waiting?R.string.disconnect:R.string.connect);
        boolean available=store.exists();if(autoMode.isChecked()){available=false;for(Transport t:Transport.values())available|=new ProfileStore(this,t).exists();}
        autoMode.setEnabled(!busy&&!on&&!waiting);toggle.setEnabled(!busy&&(on||waiting||available));transportPicker.setEnabled(!busy&&!on&&!waiting);importButton.setEnabled(!busy&&!on&&!waiting);
        enrollButton.setEnabled(!busy&&!on&&!waiting);controlButton.setEnabled(!busy&&!on&&!waiting);rnsButton.setEnabled(!busy&&!on&&!waiting);
        forgetButton.setEnabled(!busy&&!on&&!waiting&&store.exists());checkButton.setEnabled(!busy&&on);
        if(ConnectionService.failed)detail.setText(R.string.failed);
        else if(!value.equals("off")&&"auto".equals(ConnectionService.requestedTransport))detail.setText("Auto · "+ConnectionService.activeTransport.toUpperCase(java.util.Locale.ROOT));
        showControlResult();
    }
    private void showControlResult(){
        long id=ConnectionService.controlResultId;if(id==seenControlResult)return;seenControlResult=id;
        String outcome=ConnectionService.controlOutcome;if(outcome==null)return;
        int message="COMMITTED".equals(outcome)?R.string.control_committed:"REJECTED".equals(outcome)?R.string.control_rejected:
            "ROLLED_BACK".equals(outcome)?R.string.control_rolled_back:"BUSY".equals(outcome)?R.string.disconnect_first:"UNAVAILABLE".equals(outcome)?R.string.rns_unavailable:R.string.control_failed;
        detail.setText(message);
    }
    private void continueRns(){
        if(!pendingRns)return;
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},19);
        else startRns();
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
        super.onRequestPermissionsResult(request,permissions,results);if(request==12)startVpn();else if(request==16)startControl();else if(request==19)startRns();
    }
    private void startVpn(){ConnectionService.requestedTransport=pendingTransport;if(!pendingTransport.equals("auto"))ConnectionService.activeTransport=pendingTransport;ConnectionService.status="connecting";startForegroundService(new Intent(this,ConnectionService.class).setAction("connect").putExtra("transport",pendingTransport));render();}
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
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
    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
    @Override protected void onDestroy(){pendingRns=false;pendingControl=null;handler.removeCallbacks(refresh);ControlEnrollmentHttp e=enrollmentHttp;if(e!=null)e.close();worker.shutdownNow();super.onDestroy();}
}
