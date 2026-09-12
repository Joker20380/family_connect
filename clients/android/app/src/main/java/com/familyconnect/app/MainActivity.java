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
    private Button toggle,importButton,checkButton,forgetButton;
    private ProfileStore store;
    private Spinner transportPicker;
    private Transport selected=Transport.WG;
    private String pendingTransport="wg";
    private boolean busy=false;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,500);}};
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
        label(content,getString(R.string.route),15,Color.LTGRAY);
        transportPicker=new Spinner(this);transportPicker.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"WireGuard","AmneziaWG 2","TCP · REALITY"}));
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
        checkButton=button(content,R.string.check_ip,()->checkIp());
        forgetButton=button(content,R.string.forget,()->{
            if(!ConnectionService.status.equals("off"))return;
            try{store.clear();detail.setText(R.string.no_profile);}catch(Exception e){detail.setText(R.string.failed);}
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
        if(!value.equals("off")){
            Transport active=Transport.parse(ConnectionService.activeTransport);
            if(selected!=active){selected=active;store=new ProfileStore(this,active);transportPicker.setSelection(active.ordinal());getPreferences(MODE_PRIVATE).edit().putString("transport",active.id).apply();}
        }
        boolean on=value.equals("on"),waiting=value.equals("connecting")||value.equals("cleanup-required");
        state.setText(on?R.string.on:waiting?R.string.connecting:R.string.off);
        dot.setTextColor(on?Color.rgb(102,219,192):Color.GRAY);toggle.setText(on||waiting?R.string.disconnect:R.string.connect);
        toggle.setEnabled(!busy&&(on||waiting||store.exists()));transportPicker.setEnabled(!busy&&!on&&!waiting);importButton.setEnabled(!busy&&!on&&!waiting);
        forgetButton.setEnabled(!busy&&!on&&!waiting&&store.exists());checkButton.setEnabled(!busy&&on);
        if(ConnectionService.failed)detail.setText(R.string.failed);
    }
    private void toggle(){
        if(!ConnectionService.status.equals("off")){startService(new Intent(this,ConnectionService.class).setAction("disconnect"));return;}
        pendingTransport=selected.id;Intent permission=VpnService.prepare(this);
        if(permission!=null)startActivityForResult(permission,11);else continueStart();
    }
    private void continueStart(){
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},12);
        else startVpn();
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){
        super.onRequestPermissionsResult(request,permissions,results);if(request==12)startVpn();
    }
    private void startVpn(){ConnectionService.activeTransport=pendingTransport;ConnectionService.status="connecting";startForegroundService(new Intent(this,ConnectionService.class).setAction("connect").putExtra("transport",pendingTransport));render();}
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request==11){if(result==RESULT_OK)continueStart();else detail.setText(R.string.permission_denied);return;}
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
        worker.execute(()->{
            String result=getString(R.string.failed);
            HttpsURLConnection connection=null;
            try {
                if(!ConnectionService.status.equals("on"))throw new IOException();
                connection=(HttpsURLConnection)new URL("https://www.cloudflare.com/cdn-cgi/trace").openConnection();
                connection.setConnectTimeout(10000);connection.setReadTimeout(10000);connection.setInstanceFollowRedirects(false);
                if(connection.getResponseCode()!=200)throw new IOException();
                String ip="?",region="?";int total=0;
                try(BufferedReader reader=new BufferedReader(new InputStreamReader(connection.getInputStream(),StandardCharsets.UTF_8))){
                    String line;while((line=reader.readLine())!=null){total+=line.length();if(total>4096)throw new IOException();if(line.startsWith("ip="))ip=line.substring(3);if(line.startsWith("loc="))region=line.substring(4);}
                }
                if(!ConnectionService.status.equals("on"))throw new IOException();result="IP: "+ip+" · "+region;
            }catch(Exception ignored){}finally{if(connection!=null)connection.disconnect();}
            String message=result;runOnUiThread(()->{busy=false;detail.setText(message);render();});
        });
    }
    @Override protected void onSaveInstanceState(Bundle saved){saved.putString("pendingTransport",pendingTransport);super.onSaveInstanceState(saved);}
    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
    @Override protected void onDestroy(){handler.removeCallbacks(refresh);worker.shutdownNow();super.onDestroy();}
}
