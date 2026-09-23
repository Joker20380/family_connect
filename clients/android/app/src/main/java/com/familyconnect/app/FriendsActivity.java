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
public final class FriendsActivity extends LocalizedActivity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private TextView status,detail,routeCaption,routeStatus,routeDetail;private Button check,activate;private TerminalToggle connect;private Spinner countries,transports;
    private boolean busy,reconnect,initializing=true;
    private TerminalUi.Dial dial;
    private final ExecutorService loadWorker=Executors.newSingleThreadExecutor();
    private TextView loadLabel;private ProgressBar loadBar;private ServerLoad loadSample;
    private boolean loadPending,loadResumed;private long loadNext;private String loadCountry;
    private final Runnable loadRefresh=new Runnable(){public void run(){refreshLoad();if(loadResumed)handler.postDelayed(this,3000);}};
    private AppUpdateUi appUpdate;
    private boolean motion;
    private String country,activeCountry;
    private LiveNetworkPanel telemetry;
    private RouteMapView routeMap, dashboardMap;
    private RouteLocation dashboardLocation;
    private android.location.Location mapOrigin;
    private TerminalUi.Dial routeDial;
    private RouteLocation routeLocation;
    private TextView locationStatus;
    private LinearLayout dashboardRoot;
    private int currentTab;
    private String transport;
    private final Runnable refresh=new Runnable(){public void run(){render();handler.postDelayed(this,500);}};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);transport=getPreferences(MODE_PRIVATE).getString("transport","awg");country=getPreferences(MODE_PRIVATE).getString("country","nl");
        motion=getPreferences(MODE_PRIVATE).getBoolean("motion",true);activeCountry=getPreferences(MODE_PRIVATE).getString("session_country",country);
        countries=new Spinner(this);TerminalUi.inlinePicker(countries,new String[]{getString(R.string.gateway_russia),getString(R.string.gateway_netherlands)});
        countries.setContentDescription(getString(R.string.terminal_country));countries.setSelection(country.equals("nl")?1:0);
        transports=new Spinner(this);TerminalUi.inlinePicker(transports,new String[]{"AWG 3.1","TCP REALITY"});
        transports.setContentDescription(getString(R.string.terminal_transport));transports.setSelection(transport.equals("awg")?0:1);
        countries.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){
                if(!parent.isShown())return;
                String next=position==1?"nl":"ru";if(next.equals(country))return;
                country=next;getPreferences(MODE_PRIVATE).edit().putString("country",country).apply();detail.setText("");
                if(!initializing&&!ConnectionService.status.equals("off")){reconnect=true;disconnect();}render();
            }
        });
        transports.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){
                if(!parent.isShown())return;
                String next=position==0?"awg":"tcp";if(next.equals(transport))return;
                transport=next;getPreferences(MODE_PRIVATE).edit().putString("transport",transport).apply();
                if(!initializing&&!ConnectionService.status.equals("off")){reconnect=true;disconnect();}render();
            }
        });
        appUpdate=new AppUpdateUi(this);buildDashboard();initializing=false;handleTabIntent();
        handleInvitation();
    }
    private void buildDashboard(){
        LinearLayout root=TerminalUi.dashboard(this);dashboardRoot=root;
        TerminalUi.dashboardHeader(root);
        LinearLayout panel=TerminalUi.dashboardPanel(root,1);
        dial=new TerminalUi.Dial(this);dial.setMotion(motion);
        dial.setOnClickListener(v->{if(busy)return;if(getPreferences(MODE_PRIVATE).getBoolean("activated",false))toggle();else register(true);});
        panel.addView(dial,new LinearLayout.LayoutParams(-1,0,1));
        status=TerminalUi.compactLabel(panel,"",18,TerminalUi.TEXT);status.setGravity(Gravity.CENTER);status.setMaxLines(2);
        connect=new TerminalToggle(this);connect.setControlled(true);connect.setMotion(motion);
        connect.setOnClickListener(v->{if(getPreferences(MODE_PRIVATE).getBoolean("activated",false))toggle();else register(true);});
        loadLabel=TerminalUi.compactLabel(panel,"",12,TerminalUi.MUTED);
        loadBar=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);loadBar.setMax(1000);
        loadBar.setProgressTintList(android.content.res.ColorStateList.valueOf(TerminalUi.MINT));
        loadBar.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(16,46,36)));
        LinearLayout.LayoutParams loadLayout=new LinearLayout.LayoutParams(-1,TerminalUi.dp(this,8));loadLayout.bottomMargin=TerminalUi.dp(this,12);panel.addView(loadBar,loadLayout);
        routeCaption=TerminalUi.compactLabel(root,"",12,TerminalUi.MUTED);routeCaption.setGravity(Gravity.CENTER);routeCaption.setMaxLines(2);routeCaption.setVisibility(android.view.View.GONE);
        telemetry=new LiveNetworkPanel(this);telemetry.selectors(countries,transports);LinearLayout.LayoutParams telemetryLayout=new LinearLayout.LayoutParams(-1,TerminalUi.dp(this,150));telemetryLayout.topMargin=TerminalUi.dp(this,8);root.addView(telemetry,telemetryLayout);
        activate=new Button(this);activate.setOnClickListener(v->{
            if(getPreferences(MODE_PRIVATE).getBoolean("activated",false))startActivity(new Intent(this,ReferralActivity.class));else activate();
        });
        TerminalUi.actionStyle(activate);
        detail=TerminalUi.compactLabel(panel,"",12,TerminalUi.MUTED);detail.setMaxLines(2);detail.setVisibility(android.view.View.GONE);
        detail.setEllipsize(android.text.TextUtils.TruncateAt.END);detail.setGravity(Gravity.CENTER);
        detail.addTextChangedListener(new android.text.TextWatcher(){
            public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            public void onTextChanged(CharSequence s,int start,int before,int count){detail.setVisibility(s.length()==0?android.view.View.GONE:android.view.View.VISIBLE);}
            public void afterTextChanged(android.text.Editable value){}
        });
        check=new Button(this);check.setText(R.string.check_ip);TerminalUi.actionStyle(check);check.setOnClickListener(v->checkIp());
        TerminalUi.tabs(root,this,0);
        dashboardMap=new RouteMapView(this,code->{});dashboardMap.compactPreview();
        dashboardMap.setOnClickListener(v->navigate(2));
        dashboardLocation=new RouteLocation(this,location->{mapOrigin=location;dashboardMap.locate(location);if(routeMap!=null)routeMap.locate(location);},resource->{});
        TerminalUi.compactDashboardDial(root,panel,dial,telemetry,dashboardMap);
        render();
    }
    void navigate(int tab){
        if(routeLocation!=null){routeLocation.stop();routeLocation=null;}
        locationStatus=null;routeMap=null;routeDial=null;routeStatus=null;routeDetail=null;currentTab=tab;
        if(tab==1)startActivity(new Intent(this,ChatActivity.class).addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|Intent.FLAG_ACTIVITY_SINGLE_TOP));
        else if(tab==2)showRoute();else if(tab==3)showSettings();else {setContentView(dashboardRoot);render();}
    }
    @Override public void onBackPressed(){if(currentTab!=0){navigate(0);return;}super.onBackPressed();}
    private void handleTabIntent(){if(getIntent().hasExtra("tab")){int tab=getIntent().getIntExtra("tab",0);getIntent().removeExtra("tab");handler.post(()->{if(!isDestroyed())navigate(tab);});}}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);handleTabIntent();handleInvitation();}
    private void attach(LinearLayout parent,android.view.View view){
        if(view.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)view.getParent()).removeView(view);
        parent.addView(view,new LinearLayout.LayoutParams(-1,-2));
    }
    private LinearLayout dialogContent(){
        LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);
        int p=TerminalUi.dp(this,18);panel.setPadding(p,p,p,p);panel.setBackground(TerminalUi.backdrop(this));return panel;
    }
    private void showRoute(){

        countries.setSelection(country.equals("nl")?1:0);transports.setSelection(transport.equals("awg")?0:1);

        LinearLayout page=dialogContent();page.setPadding(TerminalUi.dp(this,12),TerminalUi.dp(this,8),TerminalUi.dp(this,12),TerminalUi.dp(this,8));
        TerminalUi.dashboardHeader(page);
        LinearLayout heading=new LinearLayout(this);heading.setGravity(Gravity.CENTER_VERTICAL);
        TextView title=new TextView(this);TerminalUi.textStyle(title,20,TerminalUi.AMBER);title.setText(R.string.dashboard_route);heading.addView(title);page.addView(heading);
        ScrollView scroll=new ScrollView(this);LinearLayout panel=dialogContent();panel.setPadding(0,0,0,0);scroll.addView(panel);page.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        TextView regionInfo=new TextView(this);TerminalUi.textStyle(regionInfo,12,TerminalUi.MUTED);regionInfo.setText(R.string.route_gestures);
        routeMap=new RouteMapView(this,code->regionInfo.setText(getString(R.string.route_preview,getString(code.equals("nl")?R.string.gateway_netherlands:R.string.gateway_russia))));
        if(mapOrigin!=null)routeMap.locate(mapOrigin);
        panel.addView(routeMap,new LinearLayout.LayoutParams(-1,TerminalUi.dp(this,250)));panel.addView(regionInfo);
        locationStatus=TerminalUi.label(panel,getString(R.string.route_location_permission),12,TerminalUi.MUTED);
        routeLocation=new RouteLocation(this,location->{mapOrigin=location;if(dashboardMap!=null)dashboardMap.locate(location);if(routeMap!=null)routeMap.locate(location);},resource->{if(locationStatus!=null)locationStatus.setText(resource);});
        TerminalUi.button(panel,R.string.route_locate,()->{if(routeLocation.permitted())routeLocation.start();else requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION},31);});
        TerminalUi.label(panel,getString(R.string.route_note),11,TerminalUi.MUTED);
        routeStatus=TerminalUi.label(panel,"",14,TerminalUi.TEXT);
        routeDial=new TerminalUi.Dial(this);routeDial.setMotion(motion);
        routeDial.setBackground(TerminalUi.frame(this,TerminalUi.BACKGROUND,TerminalUi.FRAME));
        routeDial.setOnClickListener(v->{if(!busy)connect.performClick();});
        panel.addView(routeDial,new LinearLayout.LayoutParams(-1,TerminalUi.dp(this,250)));

        attach(panel,check);routeDetail=TerminalUi.label(panel,detail.getText().toString(),12,TerminalUi.MUTED);
        TerminalUi.tabs(page,this,2);
        setContentView(page);
        if(routeLocation.permitted())routeLocation.start();render();
    }
    private void showSettings(){


        LinearLayout page=dialogContent();page.setPadding(TerminalUi.dp(this,12),TerminalUi.dp(this,8),TerminalUi.dp(this,12),TerminalUi.dp(this,8));TerminalUi.dashboardHeader(page);
        LinearLayout panel=dialogContent();
        TerminalUi.label(panel,getString(R.string.dashboard_settings),20,TerminalUi.AMBER);
        TerminalUi.label(panel,getString(R.string.dashboard_motion),14,TerminalUi.TEXT);
        TerminalToggle toggle=new TerminalToggle(this);toggle.setMotion(motion);toggle.setChecked(motion);
        toggle.setText(R.string.dashboard_motion);toggle.setContentDescription(getString(R.string.dashboard_motion));
        panel.addView(toggle,new LinearLayout.LayoutParams(-1,TerminalUi.dp(this,52)));
        toggle.setOnCheckedChangeListener((button,checked)->{
            motion=checked;toggle.setMotion(motion);getPreferences(MODE_PRIVATE).edit().putBoolean("motion",motion).apply();dial.setMotion(motion);connect.setMotion(motion);
        });
        String selectedLanguage=AppLanguage.selected(this);
        String languageName=selectedLanguage.equals("ru")?"Русский":selectedLanguage.equals("en")?"English":getString(R.string.language_system);
        TerminalUi.label(panel,getString(R.string.language),12,TerminalUi.AMBER);
        Spinner languagePicker=new Spinner(this);TerminalUi.picker(languagePicker,new String[]{getString(R.string.language_system),"Русский","English"});
        String[] languageCodes={"system","ru","en"};languagePicker.setSelection(java.util.Arrays.asList(languageCodes).indexOf(selectedLanguage));panel.addView(languagePicker);
        languagePicker.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(AdapterView<?> parent){}
            public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){
                if(!parent.isShown()||languageCodes[position].equals(AppLanguage.selected(FriendsActivity.this)))return;
                AppLanguage.select(FriendsActivity.this,languageCodes[position]);getIntent().putExtra("tab",3);recreate();
            }
        });
        String device=getPreferences(MODE_PRIVATE).getString("device","");
        if(!device.isEmpty())TerminalUi.label(panel,"ID · "+device,12,TerminalUi.MUTED);
        TerminalUi.label(panel,getString(R.string.product_version,TerminalUi.version(this)),12,TerminalUi.MUTED);
        appUpdate.attach(panel);
        TerminalUi.label(panel,getString(R.string.friends_hint),12,TerminalUi.MUTED);
        attach(panel,activate);
        ScrollView scroll=new ScrollView(this);scroll.addView(panel);
        page.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));TerminalUi.tabs(page,this,3);
        setContentView(page);
    }
    private TextView label(LinearLayout parent,String text,int size){return TerminalUi.label(parent,text,size,TerminalUi.TEXT);}
    private Button button(LinearLayout parent,int title,Runnable action){return TerminalUi.button(parent,title,action);}
    private void text(TextView view,String value){if(!value.contentEquals(view.getText()))view.setText(value);}
    private void render(){
        if(connect==null)return;String value=ConnectionService.status;boolean on=value.equals("on"),off=value.equals("off");
        dial.update(value,ConnectionService.healthStatus);dial.setEnabled(!busy);
        text(status,getString(off?R.string.off:on?(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:ConnectionService.healthStatus.equals("unavailable")?R.string.health_unavailable:R.string.health_checking):R.string.connecting));
        text(connect,getString(off?R.string.connect:R.string.disconnect));connect.setChecked(on);connect.setPending(!off&&!on);boolean enabled=getPreferences(MODE_PRIVATE).getBoolean("activated",false);connect.setEnabled(!busy);text(activate,getString(enabled?R.string.referral_title:R.string.friends_activate));activate.setEnabled(!busy);
        String shownCountry=off?country:activeCountry;
        String shownTransport=off?transport:ConnectionService.activeTransport;
        String summary=getString(shownCountry.equals("nl")?R.string.gateway_netherlands:R.string.gateway_russia)+"  /  "+(shownTransport.equals("awg")?"AWG 3.1":"TCP REALITY");
        text(routeCaption,summary);telemetry.connection(getString(shownCountry.equals("nl")?R.string.gateway_netherlands:R.string.gateway_russia),shownTransport.equals("awg")?"AWG 3.1":"TCP REALITY",getString(off?R.string.off:on?(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:ConnectionService.healthStatus.equals("unavailable")?R.string.health_unavailable:R.string.health_checking):R.string.connecting));telemetry.sample();renderLoad();
        if(routeDial!=null){routeDial.setMotion(motion);routeDial.update(value,ConnectionService.healthStatus);routeDial.setEnabled(!busy);}
        if(dashboardMap!=null)dashboardMap.update(shownCountry,value,ConnectionService.healthStatus,false);
        if(routeMap!=null){routeMap.update(shownCountry,value,ConnectionService.healthStatus,motion);text(routeStatus,getString(off?R.string.route_selected:R.string.route_active)+" · "+summary+"\n"+getString(R.string.route_core)+": "+getString(off?R.string.route_waiting:on?R.string.on:R.string.connecting)+"\n"+getString(R.string.route_check)+": "+getString(ConnectionService.healthStatus.equals("ok")?R.string.health_ok:ConnectionService.healthStatus.equals("unavailable")?R.string.health_unavailable:off?R.string.route_waiting:R.string.health_checking));text(routeDetail,detail.getText().toString());}
        countries.setEnabled(!busy&&(off||on));check.setEnabled(!busy&&on);transports.setEnabled(!busy&&(off||on));
        if(ConnectionService.failed)text(detail,getString(R.string.failed));
        if(reconnect&&off&&!busy){reconnect=false;toggle();}
    }
    private String pendingInvitation="";
    private void handleInvitation(){
        String uri=getIntent().getDataString();getIntent().setData(null);
        if(uri==null)return;
        if(!uri.matches("familyconnect://invite/[0-9a-f]{64}")){detail.setText(R.string.friends_invite_rejected);return;}
        pendingInvitation=uri.substring("familyconnect://invite/".length());navigate(0);activate();
    }
    private void activate(){navigate(0);register(false);}
    private void register(boolean connectAfter){
        if(busy)return;
        if(pendingInvitation.isEmpty()&&!getPreferences(MODE_PRIVATE).getBoolean("activated",false)){detail.setText(R.string.friends_invite_hint);return;}
        final String invitation=pendingInvitation;
        busy=true;detail.setText(R.string.checking);render();
        worker.execute(()->{
            int message=R.string.friends_unavailable;String device="";
            try{device=new FriendsAccessAndroid(this).register(invitation);message=R.string.friends_activated;}
            catch(FriendsAccessAndroid.Denied denied){message=R.string.friends_invite_rejected;}catch(Exception failure){}
            final String registered=device;final int result=message;
            runOnUiThread(()->{if(isDestroyed())return;busy=false;
                if(!registered.isEmpty()){pendingInvitation="";getPreferences(MODE_PRIVATE).edit().putBoolean("activated",true).putString("device",registered).apply();}
                detail.setText(result);render();if(connectAfter&&!registered.isEmpty())toggle();
            });
        });
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
                activeCountry=chosen;getPreferences(MODE_PRIVATE).edit().putString("session_country",chosen).apply();detail.setText("");ConnectionService.status="connecting";ConnectionService.activeTransport=chosenTransport;ConnectionService.requestedTransport=chosenTransport;
                startForegroundService(new Intent(this,ConnectionService.class).setAction("connect").putExtra("transport",chosenTransport));render();
            });
        });
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==11){if(result==RESULT_OK)prepareConnect();else detail.setText(R.string.permission_denied);}}
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){super.onRequestPermissionsResult(request,permissions,results);if(request==31&&routeLocation!=null)routeLocation.start();if(request==12)connectNow();}
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
    private String loadTarget(){return ConnectionService.status.equals("off")?country:activeCountry;}
    private void renderLoad(){
        if(loadLabel==null)return;
        ServerLoad sample=loadSample;
        if(sample!=null&&(!sample.country.equals(loadTarget())||!sample.fresh(System.currentTimeMillis()/1000.0)))sample=null;
        boolean ru=getResources().getConfiguration().getLocales().get(0).getLanguage().equals("ru");
        String text=(ru?"Нагрузка сервера":"Server load")+" · ";
        Double percent=sample==null?null:sample.percent;
        text+=percent==null?(ru?"Нет данных":"No data"):(sample.estimated?"≈ ":"")+Math.round(percent)+"%";
        loadLabel.setText(text);loadBar.setContentDescription(text);loadBar.setProgress(percent==null?0:(int)Math.round(percent*10));
        loadBar.setProgressTintList(android.content.res.ColorStateList.valueOf(percent!=null&&percent>=90?Color.rgb(239,132,116):percent!=null&&percent>=70?TerminalUi.AMBER:TerminalUi.MINT));
        loadLabel.setTooltipText(sample==null?text:String.format(java.util.Locale.ROOT,"CPU %.0f%% · ↓ %.1f / ↑ %.1f Mbps",sample.cpu,sample.rx,sample.tx)+(sample.estimated?(ru?" · расчёт по исходящему каналу 200 Мбит/с":" · estimated using 200 Mbps egress"):""));
    }
    private void refreshLoad(){
        if(!loadResumed||isDestroyed())return;String target=loadTarget();
        if(!target.equals(loadCountry)){loadCountry=target;loadSample=null;loadNext=0;}renderLoad();
        if(loadPending||SystemClock.elapsedRealtime()<loadNext)return;loadPending=true;
        loadWorker.execute(()->{ServerLoad result=null;try{result=ServerLoad.fetch(target);}catch(Exception ignored){}final ServerLoad value=result;
            handler.post(()->{if(isDestroyed())return;loadPending=false;loadNext=SystemClock.elapsedRealtime()+15000;
                if(target.equals(loadTarget()))loadSample=value;renderLoad();});});
    }
    @Override protected void onResume(){super.onResume();if(getPreferences(MODE_PRIVATE).getBoolean("activated",false)){ChatNotifications.request(this);ChatDeliveryService.start(this);}if(dashboardLocation!=null&&dashboardLocation.permitted())dashboardLocation.start();if(appUpdate!=null)appUpdate.render();loadResumed=true;handler.post(loadRefresh);handler.post(refresh);if(routeLocation!=null&&routeLocation.permitted())routeLocation.start();}
    @Override protected void onPause(){if(dashboardLocation!=null)dashboardLocation.stop();loadResumed=false;handler.removeCallbacks(loadRefresh);handler.removeCallbacks(refresh);if(telemetry!=null)telemetry.pause();if(routeLocation!=null)routeLocation.stop();super.onPause();}
    @Override protected void onDestroy(){handler.removeCallbacks(refresh);if(routeLocation!=null)routeLocation.stop();loadResumed=false;handler.removeCallbacks(loadRefresh);loadWorker.shutdownNow();if(appUpdate!=null)appUpdate.close();worker.shutdownNow();super.onDestroy();}
}
