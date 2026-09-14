package com.familyconnect.app;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.VpnService;
import android.os.*;
import android.view.Gravity;
import android.widget.*;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import javax.net.ssl.HttpsURLConnection;

/** Separate open-test launcher: no accounts, billing, device enrollment or managed journal. */
public final class FriendsActivity extends Activity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private TextView status,detail;private Button connect,check;private Spinner countries;
    private boolean busy,reconnect,initializing=true;
    private String country;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,500);}};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);country=getPreferences(MODE_PRIVATE).getString("country","ru");
        LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setGravity(Gravity.CENTER);
        int padding=(int)(24*getResources().getDisplayMetrics().density);content.setPadding(padding,padding,padding,padding);content.setBackgroundColor(Color.rgb(16,25,35));
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(content);setContentView(scroll);
        label(content,"FAMILY CONNECT",27);label(content,getString(R.string.friends_access),16);
        countries=new Spinner(this);countries.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{getString(R.string.gateway_russia),getString(R.string.gateway_netherlands)}));
        countries.setSelection(country.equals("nl")?1:0);content.addView(countries);
        status=label(content,"",22);connect=button(content,R.string.connect,this::toggle);check=button(content,R.string.check_ip,this::checkIp);
        detail=label(content,getString(R.string.friends_hint),15);
        countries.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){
                String next=position==1?"nl":"ru";if(next.equals(country))return;
                country=next;getPreferences(MODE_PRIVATE).edit().putString("country",country).apply();detail.setText("");
                if(!initializing&&!ConnectionService.status.equals("off")){reconnect=true;disconnect();}
            }
        });initializing=false;
    }
    private TextView label(LinearLayout parent,String text,int size){TextView view=new TextView(this);view.setText(text);view.setTextSize(size);view.setTextColor(Color.WHITE);view.setGravity(Gravity.CENTER);view.setPadding(0,22,0,22);parent.addView(view);return view;}
    private Button button(LinearLayout parent,int title,Runnable action){Button view=new Button(this);view.setText(title);view.setAllCaps(false);view.setOnClickListener(v->action.run());parent.addView(view,new LinearLayout.LayoutParams(-1,-2));return view;}
    private void text(TextView view,String value){if(!value.contentEquals(view.getText()))view.setText(value);}
    private void render(){
        if(connect==null)return;String value=ConnectionService.status;boolean on=value.equals("on"),off=value.equals("off");
        text(status,getString(off?R.string.off:on?(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:R.string.health_checking):R.string.connecting));
        text(connect,getString(off?R.string.connect:R.string.disconnect));connect.setEnabled(!busy);countries.setEnabled(!busy&&(off||on));check.setEnabled(!busy&&on);
        if(ConnectionService.failed)text(detail,getString(R.string.failed));
        if(reconnect&&off&&!busy){reconnect=false;toggle();}
    }
    private void disconnect(){startService(new Intent(this,ConnectionService.class).setAction("disconnect"));}
    private void toggle(){
        if(busy)return;if(!ConnectionService.status.equals("off")){reconnect=false;disconnect();return;}
        Intent permission=VpnService.prepare(this);if(permission!=null)startActivityForResult(permission,11);else prepareConnect();
    }
    private void prepareConnect(){
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},12);return;}
        connectNow();
    }
    private void connectNow(){
        busy=true;ConnectionService.failed=false;detail.setText(R.string.checking);render();final String chosen=country;
        worker.execute(()->{
            boolean ready=false;
            try{ControlOpenCatalog catalog=new OpenCatalogStore(this).load();String raw=catalog.profiles.get(chosen);if(raw==null)throw new IOException();new ProfileStore(this,Transport.TCP).save(raw);ready=true;}catch(Exception failure){}
            final boolean result=ready;runOnUiThread(()->{
                if(isDestroyed())return;busy=false;if(!result){detail.setText(R.string.friends_unavailable);render();return;}
                detail.setText("");ConnectionService.status="connecting";ConnectionService.activeTransport="tcp";ConnectionService.requestedTransport="tcp";
                startForegroundService(new Intent(this,ConnectionService.class).setAction("connect").putExtra("transport","tcp"));render();
            });
        });
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==11){if(result==RESULT_OK)prepareConnect();else detail.setText(R.string.permission_denied);}}
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){super.onRequestPermissionsResult(request,permissions,results);if(request==12)connectNow();}
    private void checkIp(){
        busy=true;detail.setText(R.string.checking);render();final long session=ConnectionService.sessionId;final String source=ConnectionService.vpnSource;
        worker.execute(()->{
            String result=getString(R.string.failed);HttpsURLConnection connection=null;
            try{
                VpnHealth binding=new VpnHealth(this);android.net.Network network=binding.find(source);if(network==null)throw new IOException();
                connection=(HttpsURLConnection)network.openConnection(new URL("https://www.cloudflare.com/cdn-cgi/trace"));connection.setConnectTimeout(8000);connection.setReadTimeout(8000);connection.setInstanceFollowRedirects(false);
                if(connection.getResponseCode()!=200)throw new IOException();String ip="",region="";int size=0;
                try(BufferedReader input=new BufferedReader(new InputStreamReader(connection.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=input.readLine())!=null){size+=line.length();if(size>4096)throw new IOException();if(line.startsWith("ip="))ip=line.substring(3);if(line.startsWith("loc="))region=line.substring(4);}}
                if(ip.isEmpty()||session!=ConnectionService.sessionId||!network.equals(binding.find(source)))throw new IOException();result="IP: "+ip+" · "+region;
            }catch(Exception failure){}finally{if(connection!=null)connection.disconnect();}
            final String message=result;runOnUiThread(()->{if(isDestroyed())return;busy=false;detail.setText(session==ConnectionService.sessionId?message:getString(R.string.failed));render();});
        });
    }
    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
    @Override protected void onDestroy(){handler.removeCallbacks(refresh);worker.shutdownNow();super.onDestroy();}
}
