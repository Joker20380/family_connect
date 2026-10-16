package com.familyconnect.app;

import android.app.Activity;
import android.app.Application;
import android.app.Instrumentation;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Binder;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

public final class UiFixtureInstrumentation extends Instrumentation {
    private Bundle arguments;
    private final JSONArray results=new JSONArray();
    private static final String PREFIX="com.familyconnect.app.";
    private static int serviceRequests;
    private static final class GuardContext extends ContextWrapper {
        GuardContext(Context context){super(context);}
        @Override public Context createConfigurationContext(Configuration config){return new GuardContext(super.createConfigurationContext(config));}
        @Override public android.content.ComponentName startService(Intent intent){serviceRequests++;throw new AssertionError("UI attempted startService");}
        @Override public android.content.ComponentName startForegroundService(Intent intent){serviceRequests++;throw new AssertionError("UI attempted startForegroundService");}
        @Override public boolean bindService(Intent intent,android.content.ServiceConnection connection,int flags){serviceRequests++;throw new AssertionError("UI attempted bindService");}
    }
    @Override public void onCreate(Bundle value){arguments=value;start();}
    private Class<?> type(String name)throws Exception{return Class.forName(PREFIX+name);}
    private Field field(Class<?> owner,String name)throws Exception{
        for(Class<?> current=owner;current!=null;current=current.getSuperclass()){
            try{Field result=current.getDeclaredField(name);result.setAccessible(true);return result;}
            catch(NoSuchFieldException ignored){}
        }
        throw new NoSuchFieldException(name);
    }
    private Object get(Object target,String name)throws Exception{return field(target.getClass(),name).get(target);}
    private void set(Object target,String name,Object value)throws Exception{field(target.getClass(),name).set(target,value);}
    private Object invoke(Object target,String name,Class<?>[] parameters,Object...values)throws Exception{
        Method method=target.getClass().getDeclaredMethod(name,parameters);method.setAccessible(true);return method.invoke(target,values);
    }
    private Activity activity(String name,String language,float font)throws Exception{
        Context target=getTargetContext();
        target.getSharedPreferences("appearance",0).edit().putString("language",language).commit();
        target.getSharedPreferences(PREFIX+"FriendsActivity",0).edit().putBoolean("motion",false).apply();
        Configuration config=new Configuration(target.getResources().getConfiguration());
        config.fontScale=font;config.densityDpi=160;config.setLocale(Locale.forLanguageTag(language));
        Context context=new GuardContext(target.createConfigurationContext(config));
        ActivityInfo info=new ActivityInfo();info.name=PREFIX+name;info.packageName=target.getPackageName();info.applicationInfo=target.getApplicationInfo();
        Application application=new Application();
        Activity result=newActivity(type(name),context,new Binder(),application,new Intent().setClassName(target.getPackageName(),PREFIX+name),info,"UI fixture",null,null,null);
        int theme=context.getResources().getIdentifier("ExitTheme","style",target.getPackageName());
        result.setTheme(theme==0?android.R.style.Theme_Material_NoActionBar:theme);
        result.getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        return result;
    }
    private Activity home(String language,float font,String state)throws Exception{
        Activity activity=activity("FriendsActivity",language,font);
        set(activity,"country","nl");set(activity,"activeCountry","nl");set(activity,"transport","telemost");set(activity,"motion",false);
        Spinner countries=new Spinner(activity),transports=new Spinner(activity);
        Constructor<?> adapter=type("FriendsActivity$ServerAdapter").getDeclaredConstructor(type("FriendsActivity"));adapter.setAccessible(true);
        Object countryAdapter=adapter.newInstance(activity);set(activity,"serverAdapter",countryAdapter);
        countries.setAdapter((android.widget.SpinnerAdapter)countryAdapter);countries.setSelection(1);
        countries.setBackgroundColor(android.graphics.Color.TRANSPARENT);countries.setPadding(0,0,0,0);
        Class<?> terminal=type("TerminalUi");
        Method picker=terminal.getDeclaredMethod("inlinePicker",Spinner.class,String[].class);picker.setAccessible(true);
        boolean legacy="beta60".equals(arguments.getString("label"));
        if(legacy)set(activity,"transport","auto");
        picker.invoke(null,transports,legacy?new String[]{"Auto","AWG 3.1","TCP REALITY"}:new String[]{"Auto","AWG 3.1","TCP REALITY","Telemost"});transports.setSelection(legacy?0:3);
        set(activity,"countries",countries);set(activity,"transports",transports);
        Constructor<?> updater=type("AppUpdateUi").getDeclaredConstructor(Activity.class);updater.setAccessible(true);set(activity,"appUpdate",updater.newInstance(activity));
        Class<?> service=type("ConnectionService");field(service,"status").set(null,state);field(service,"activeTransport").set(null,"restricted");
        field(service,"healthStatus").set(null,state.equals("on")?"ok":"off");field(service,"failed").set(null,state.equals("failed"));
        if(!legacy){
            Class<?> terminalModel=type("ConnectionTerminal"),stage=type("ConnectionTerminal$Stage");
            Object model=field(terminalModel,"VPN").get(null);set(model,"attempt",0L);set(model,"finished",false);set(model,"success",false);((java.util.List<?>)get(model,"lines")).clear();
            if(!state.equals("off")){
                Object preparing=field(stage,"PREPARING").get(null),transport=field(stage,"TELEMOST").get(null);
                long attempt=(Long)invoke(model,"begin",new Class<?>[]{stage},preparing);invoke(model,"add",new Class<?>[]{long.class,stage},attempt,transport);
                if(state.equals("on")||state.equals("failed"))invoke(model,"end",new Class<?>[]{long.class,stage,boolean.class},attempt,field(stage,state.equals("on")?"VPN_READY":"FAILED").get(null),state.equals("on"));
                else if(state.equals("restoring"))invoke(model,"add",new Class<?>[]{long.class,stage},attempt,field(stage,"RESTORING").get(null));
            }
        }
        invoke(activity,"buildDashboard",new Class<?>[0]);
        return activity;
    }
    private Object json(String value)throws Exception{
        Class<?> parser=Class.forName("com.google.gson.JsonParser");return parser.getMethod("parseString",String.class).invoke(null,value);
    }
    private void callback(Activity activity,String prefix,Object payload)throws Exception{
        for(Method method:activity.getClass().getDeclaredMethods()){
            Class<?>[] parameters=method.getParameterTypes();
            if(!method.getName().startsWith(prefix)||parameters.length==0||!parameters[parameters.length-1].getName().equals("com.google.gson.JsonElement"))continue;
            if(prefix.equals("lambda$conversation$")&&parameters.length!=3)continue;
            Object[] values=new Object[parameters.length];values[values.length-1]=payload;
            for(int index=0;index<parameters.length-1;index++){
                if(parameters[index]==String.class)values[index]="00000000000000000000000000000001";
                else if(parameters[index].getName().equals("com.google.gson.JsonObject")){
                    Object request=json("{\"offset\":0,\"limit\":50}");values[index]=request.getClass().getMethod("getAsJsonObject").invoke(request);
                }else throw new AssertionError("Unexpected presentation callback binding");
            }
            method.setAccessible(true);method.invoke(activity,values);return;
        }
        throw new NoSuchMethodException(prefix);
    }
    private Activity chat(String language,float font,String screen)throws Exception{
        Activity activity=activity("ChatActivity",language,font);set(activity,"screen","contacts");
        int title=activity.getResources().getIdentifier("chat_dialogs","string",activity.getPackageName());
        invoke(activity,"shell",new Class<?>[]{String.class,Runnable.class,Runnable.class},activity.getString(title),null,null);
        String card="{\"address\":\"00000000000000000000000000000001\",\"name\":\""+(language.equals("ru")?"Тестовый контакт":"Fixture contact")+"\",\"unread\":2}";
        if(screen.equals("conversation")){
            set(activity,"peer",json(card));set(activity,"offset",0);set(activity,"draft","");
            callback(activity,"lambda$conversation$",json("{\"total\":1,\"offset\":0,\"next_offset\":null,\"messages\":[{\"id\":\"fixture-1\",\"text\":\""+(language.equals("ru")?"Синтетический пример. Личной переписки нет.":"Synthetic example. No private messages.")+"\",\"outgoing\":true,\"timestamp\":1792108800,\"status\":\"delivered\",\"kind\":\"text\"}]}"));
            if(get(activity,"thread")==null)throw new AssertionError("Actual conversation projection was not reached");
        }else callback(activity,"lambda$refreshContacts$",json(screen.equals("empty")?"[]":"["+card+"]"));
        return activity;
    }
    private void save(Activity activity,String name,int width,int height)throws Exception{
        ViewGroup content=activity.findViewById(android.R.id.content);View root=content.getChildAt(0);
        root.setAlpha(1);root.setTranslationY(0);
        root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));root.layout(0,0,width,height);
        if(activity.getClass().getSimpleName().equals("FriendsActivity")&&!"beta60".equals(arguments.getString("label"))){for(String field:new String[]{"vpnTerminal","chatTerminal"})invoke(get(activity,field),"refresh",new Class<?>[0]);root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));root.layout(0,0,width,height);}
        Bitmap bitmap=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);root.draw(new Canvas(bitmap));
        File directory=activity.getExternalFilesDir("ui60-fixtures");
        try(FileOutputStream output=new FileOutputStream(new File(directory,name+".png"))){bitmap.compress(Bitmap.CompressFormat.PNG,100,output);}finally{bitmap.recycle();}
        JSONObject row=new JSONObject();row.put("name",name);row.put("width",width);row.put("height",height);row.put("locale",activity.getResources().getConfiguration().getLocales().get(0).toLanguageTag());row.put("fontScale",activity.getResources().getConfiguration().fontScale);row.put("density",activity.getResources().getDisplayMetrics().density);row.put("secure",(activity.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_SECURE)!=0);results.put(row);
        JSONArray views=new JSONArray();inspect(root,views,"",0,0);row.put("views",views);row.put("serviceRequests",serviceRequests);
        try(FileOutputStream output=new FileOutputStream(new File(directory,"receipt-"+arguments.getString("label")+"-"+width+"-"+height+"-"+arguments.getString("language","ru")+"-"+arguments.getString("font","1")+".json"))){output.write(results.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    }
    private void inspect(View view,JSONArray output,String parent,int x,int y)throws Exception{
        if(view.getVisibility()!=View.VISIBLE)return;
        JSONObject row=new JSONObject();String kind=view.getClass().getSimpleName();row.put("kind",kind);row.put("parent",parent);row.put("tag",String.valueOf(view.getTag()));
        row.put("left",x+view.getLeft());row.put("top",y+view.getTop());row.put("width",view.getWidth());row.put("height",view.getHeight());
        if(view instanceof android.widget.TextView){android.widget.TextView text=(android.widget.TextView)view;row.put("text",text.getText().toString());android.text.Layout layout=text.getLayout();if(layout!=null){int ellipsized=0;for(int index=0;index<layout.getLineCount();index++)ellipsized+=layout.getEllipsisCount(index);row.put("ellipsizedCharacters",ellipsized);row.put("lineCount",layout.getLineCount());}}
        if(view instanceof android.widget.Button&&"candidate".equals(arguments.getString("label"))&&view.getHeight()<48)throw new AssertionError("Button target below 48px: "+row);
        output.put(row);
        if(view instanceof ViewGroup){ViewGroup group=(ViewGroup)view;for(int index=0;index<group.getChildCount();index++)inspect(group.getChildAt(index),output,kind,x+view.getLeft(),y+view.getTop());}
    }
    private void navigation(String language,float font)throws Exception{
        Activity activity=home(language,font,"off");Object root=get(activity,"dashboardRoot"),dial=get(activity,"dial"),countries=get(activity,"countries"),telemetry=get(activity,"telemetry");
        Class<?> service=type("ConnectionService");Object session=field(service,"sessionId").get(null);
        for(int cycle=0;cycle<2;cycle++)for(int tab:new int[]{2,3,0})invoke(activity,"navigate",new Class<?>[]{int.class},tab);
        if(root!=get(activity,"dashboardRoot")||dial!=get(activity,"dial")||countries!=get(activity,"countries")||telemetry!=get(activity,"telemetry"))throw new AssertionError("Navigation rebuilt live controls");
        if(!session.equals(field(service,"sessionId").get(null))||!"off".equals(field(service,"status").get(null))||serviceRequests!=0)throw new AssertionError("Navigation changed session");
        JSONObject row=new JSONObject();row.put("navigationCycles",2);row.put("liveControlsPreserved",true);row.put("sessionPreserved",true);row.put("serviceRequests",serviceRequests);results.put(row);
    }
    private void networkPresentation(String language,float font,int width,int height,String prefix)throws Exception{
        Activity activity=home(language,font,"off");Object panel=get(activity,"telemetry");
        Class<?>[] sampleTypes={String.class,int.class,int.class,long.class,long.class,long.class};
        invoke(panel,"acceptSample",sampleTypes,"Wi-Fi",-54,64,1000L,1024L,1024L);
        invoke(panel,"acceptSample",sampleTypes,"Wi-Fi",-54,64,2000L,5120L,3072L);
        save(activity,prefix+"-home-network-fixture",width,height);
        android.widget.TextView[] fields=(android.widget.TextView[])get(panel,"fields");
        if(font>1&&fields[1].getLayout().getLineBottom(1)<Math.round(26*font))throw new AssertionError("Telemetry text ignored system font scale");
        View countries=(View)get(activity,"countries"),heading=(View)get(panel,"connectionHeading");
        if(fields[0].getLeft()>=fields[1].getLeft()||fields[4].getLeft()>=countries.getLeft()||heading.getBottom()>countries.getTop())throw new AssertionError("Beta60 telemetry grouping changed");
        if(!fields[1].getText().toString().contains("64%")||!((View)panel).getContentDescription().toString().contains(((android.widget.TextView)get(activity,"messageRoute")).getText()))throw new AssertionError("Telemetry value or retained details missing");
        Method factory=type("TerminalUi").getDeclaredMethod("frame",Context.class,int.class,int.class);factory.setAccessible(true);
        android.graphics.drawable.Drawable frame=(android.graphics.drawable.Drawable)factory.invoke(null,activity,0xff102321,0xff416861);
        Bitmap bitmap=Bitmap.createBitmap(48,48,Bitmap.Config.ARGB_8888);frame.setBounds(0,0,48,48);frame.draw(new Canvas(bitmap));
        boolean rectangular=bitmap.getPixel(2,2)==0xff102321&&bitmap.getPixel(45,2)==0xff102321&&bitmap.getPixel(2,45)==0xff102321&&bitmap.getPixel(45,45)==0xff102321;bitmap.recycle();
        if(!rectangular)throw new AssertionError("Frame still has cut or rounded corners");
        JSONObject row=new JSONObject();row.put("beta60TelemetryGrouping",true);row.put("rectangularFrameCorners",true);row.put("messageRouteDetailsPreserved",true);row.put("syntheticTelemetry",true);results.put(row);
    }
    private void keyboard()throws Exception{
        Activity host=startActivitySync(new Intent(getTargetContext(),FixtureHostActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        final android.widget.EditText[] composer={null};
        runOnMainSync(()->{try{
            Constructor<?> constructor=type("ChatThreadView").getDeclaredConstructor(Context.class,String.class,java.util.function.Consumer.class,java.util.function.Consumer.class);constructor.setAccessible(true);
            View thread=(View)constructor.newInstance(host,"",(java.util.function.Consumer<String>)value->{},(java.util.function.Consumer<String>)value->{throw new AssertionError("No messages may be sent by renderer");});host.setContentView(thread);
            composer[0]=(android.widget.EditText)get(thread,"composer");composer[0].setText("Синтетический черновик");composer[0].setSelection(5);composer[0].requestFocus();
        }catch(Exception failure){throw new RuntimeException(failure);}});
        waitForIdleSync();Thread.sleep(500);
        runOnMainSync(()->((android.view.inputmethod.InputMethodManager)host.getSystemService(Context.INPUT_METHOD_SERVICE)).showSoftInput(composer[0],android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT));
        Thread.sleep(8000);waitForIdleSync();
        final Throwable[] keyboardFailure={null};
        runOnMainSync(()->{try{
            ViewGroup content=host.findViewById(android.R.id.content);View root=content.getChildAt(0);android.view.WindowInsets insets=root.getRootWindowInsets();
            if(insets==null||!insets.isVisible(android.view.WindowInsets.Type.ime()))throw new AssertionError("Real IME not visible; focus="+composer[0].hasFocus()+" windowFocus="+composer[0].hasWindowFocus()+" attached="+composer[0].isAttachedToWindow());
            if(composer[0].getSelectionStart()!=5||!composer[0].getText().toString().equals("Синтетический черновик"))throw new AssertionError("IME lost draft/selection");
            save(host,"candidate-real-ime-chat-component",root.getWidth(),root.getHeight());
            JSONObject row=new JSONObject();row.put("realImeVisible",true);row.put("systemBars",insets.getInsets(android.view.WindowInsets.Type.systemBars()).toString());row.put("imeInsets",insets.getInsets(android.view.WindowInsets.Type.ime()).toString());row.put("draftSelectionPreserved",true);results.put(row);
            ((android.view.inputmethod.InputMethodManager)host.getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(composer[0].getWindowToken(),0);host.finish();
        }catch(Throwable failure){keyboardFailure[0]=failure;host.finish();}});
        if(keyboardFailure[0]!=null)throw new RuntimeException(keyboardFailure[0]);
    }
    @Override public void onStart(){
        Bundle report=new Bundle();
        try{
            if("keyboard".equals(arguments.getString("screens"))){keyboard();report.putString("result",results.toString());finish(Activity.RESULT_OK,report);return;}
            final Throwable[] failure={null};
            runOnMainSync(()->{try{
                String language=arguments.getString("language","ru");float font=Float.parseFloat(arguments.getString("font","1"));
                int width=Integer.parseInt(arguments.getString("width","392")),height=Integer.parseInt(arguments.getString("height","780"));
                String prefix=arguments.getString("label","fixture")+"-"+language+"-"+width+"-"+height+"-"+font;
                if(!"chat".equals(arguments.getString("screens"))){
                    for(String state:"home-off".equals(arguments.getString("screens"))?new String[]{"off"}:new String[]{"off","connecting","on","disconnecting","failed","restoring","cleanup-required"}){
                        Activity scene=home(language,font,state);save(scene,prefix+"-home-"+state,width,height);
                        if("candidate".equals(arguments.getString("label"))&&state.equals("off")&&(width<360||width>height)){
                            View body=((View)get(scene,"dashboardRoot")).findViewWithTag("ui60_body");android.widget.ScrollView scroll=(android.widget.ScrollView)body.getParent();scroll.scrollTo(0,body.getHeight());save(scene,prefix+"-home-scrolled",width,height);
                        }
                    }
                    if(!"home-off".equals(arguments.getString("screens"))){Activity activity=home(language,font,"off");invoke(activity,"showRoute",new Class<?>[0]);save(activity,prefix+"-route",width,height);
                    invoke(activity,"showSettings",new Class<?>[0]);save(activity,prefix+"-settings",width,height);}
                }
                if(!"home-off".equals(arguments.getString("screens")))for(String screen:new String[]{"empty","list","conversation"})save(chat(language,font,screen),prefix+"-chat-"+screen,width,height);
                if("candidate".equals(arguments.getString("label"))){navigation(language,font);networkPresentation(language,font,width,height,prefix);}
            }catch(Throwable error){failure[0]=error;}});
            if(failure[0]!=null)throw new RuntimeException(failure[0]);
            report.putString("result",results.toString());finish(Activity.RESULT_OK,report);
        }catch(Throwable error){android.util.Log.e("UI60Fixture","Fixture rendering failed",error);report.putString("error",android.util.Log.getStackTraceString(error));finish(Activity.RESULT_CANCELED,report);}
    }
}
