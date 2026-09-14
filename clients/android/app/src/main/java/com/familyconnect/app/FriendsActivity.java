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

/** Separate open-test launcher: one-use invitation, no accounts or billing; separate from managed journal. */
public final class FriendsActivity extends Activity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private TextView status,detail;private Button connect,check,activate;private Spinner countries,transports;
    private boolean busy,reconnect,initializing=true;
    private String country;
    private String transport;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,500);}};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);transport=getPreferences(MODE_PRIVATE).getString("transport","tcp");country=getPreferences(MODE_PRIVATE).getString("country","ru");
        LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setGravity(Gravity.CENTER);
        int padding=(int)(24*getResources().getDisplayMetrics().density);content.setPadding(padding,padding,padding,padding);content.setBackgroundColor(Color.rgb(16,25,35));
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(content);setContentView(scroll);
        label(content,"FAMILY CONNECT",27);label(content,getString(R.string.friends_access),16);
        countries=new Spinner(this);countries.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{getString(R.string.gateway_russia),getString(R.string.gateway_netherlands)}));
        countries.setSelection(country.equals("nl")?1:0);content.addView(countries);
        transports=new Spinner(this);transports.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"AWG 3.1","TCP REALITY"}));
        transports.setSelection(transport.equals("awg")?0:1);content.addView(transports);
        transports.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){
                String next=position==0?"awg":"tcp";if(next.equals(transport))return;
                transport=next;getPreferences(MODE_PRIVATE).edit().putString("transport",transport).apply();
                if(!initializing&&!ConnectionService.status.equals("off")){reconnect=true;disconnect();}
            }
        });
        status=label(content,"",22);activate=button(content,R.string.friends_activate,this::activate);connect=button(content,R.string.connect,this::toggle);check=button(content,R.string.check_ip,this::checkIp);
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
        text(status,getString(off?R.string.off:on?(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:ConnectionService.healthStatus.equals("unavailable")?R.string.health_unavailable:R.string.health_checking):R.string.connecting));
        text(connect,getString(off?R.string.connect:R.string.disconnect));boolean enabled=getPreferences(MODE_PRIVATE).getBoolean("activated",false);connect.setEnabled(!busy&&enabled);activate.setVisibility(enabled?android.view.View.GONE:android.view.View.VISIBLE);activate.setEnabled(!busy);countries.setEnabled(!busy&&(off||on));check.setEnabled(!busy&&on);transports.setEnabled(!busy&&(off||on));
        if(ConnectionService.failed)text(detail,getString(R.string.failed));
        if(reconnect&&off&&!busy){reconnect=false;toggle();}
    }
    private void activate(){
        EditText code=new EditText(this);code.setSingleLine(true);code.setHint("FC-…");code.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);
        new android.app.AlertDialog.Builder(this).setTitle(R.string.friends_activate).setMessage(R.string.friends_invite_hint).setView(code)
            .setNegativeButton(android.R.string.cancel,null).setPositiveButton(R.string.friends_activate,(dialog,which)->{
                String invitation=code.getText().toString();code.setText("");busy=true;detail.setText(R.string.checking);render();
                worker.execute(()->{
                    int message=R.string.friends_unavailable;boolean accepted=false;
                    try{new FriendsAccessAndroid(this).activate(invitation);accepted=true;message=R.string.friends_activated;}
                    catch(FriendsAccessAndroid.Denied denied){message=R.string.friends_invite_rejected;}catch(Exception failure){}
                    final int result=message;final boolean success=accepted;
                    runOnUiThread(()->{if(isDestroyed())return;busy=false;if(success)getPreferences(MODE_PRIVATE).edit().putBoolean("activated",true).apply();detail.setText(result);render();});
                });
            }).show();
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
        busy=true;ConnectionService.failed=false;detail.setText(R.string.checking);render();final String chosen=country,chosenTransport=transport;
        worker.execute(()->{
            boolean ready=false;
            try{String raw=new FriendsAccessAndroid(this).profile(chosen,chosenTransport);if(raw==null)throw new IOException();new ProfileStore(this,Transport.parse(chosenTransport)).save(raw);ready=true;}catch(Exception failure){}
            final boolean result=ready;runOnUiThread(()->{
                if(isDestroyed())return;busy=false;if(!result){detail.setText(R.string.friends_unavailable);render();return;}
                detail.setText("");ConnectionService.status="connecting";ConnectionService.activeTransport=chosenTransport;ConnectionService.requestedTransport=chosenTransport;
                startForegroundService(new Intent(this,ConnectionService.class).setAction("connect").putExtra("transport",chosenTransport));render();
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
