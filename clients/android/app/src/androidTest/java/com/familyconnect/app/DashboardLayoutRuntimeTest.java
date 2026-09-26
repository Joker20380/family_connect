package com.familyconnect.app;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ScrollView;
import android.app.Activity;
import android.app.Instrumentation;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import java.util.concurrent.atomic.AtomicReference;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.Before;
import static org.junit.Assume.assumeTrue;
import org.junit.runner.RunWith;
import java.io.File;
import java.io.FileOutputStream;
import static org.junit.Assert.*;

/** Measures and draws real app views; never activates accounts or changes VPN state. */
@RunWith(AndroidJUnit4.class)
public class DashboardLayoutRuntimeTest {
    @Before public void friendsVariantOnly(){
        assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }

    private void bounds(View root,View view){
        assertFalse("Dashboard must not scroll",view instanceof ScrollView);
        if(view.getVisibility()!=View.VISIBLE)return;
        if(view instanceof Button){
            Rect rect=new Rect();view.getDrawingRect(rect);((ViewGroup)root).offsetDescendantRectToMyCoords(view,rect);
            assertTrue("Control extends below viewport",rect.bottom<=root.getHeight());
            assertTrue("Control extends above viewport",rect.top>=0);
            assertTrue("Control extends outside width",rect.left>=0&&rect.right<=root.getWidth());
            assertTrue("Control touch height",view.getHeight()>=TerminalUi.dp(view.getContext(),48));
        }
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)bounds(root,((ViewGroup)view).getChildAt(i));
    }
    private void render(FriendsActivity activity,View root,int width,int height,String name){
        root.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(height,View.MeasureSpec.EXACTLY));
        root.layout(0,0,width,height);bounds(root,root);
        save(activity,root,width,height,name);
    }
    private void save(FriendsActivity activity,View root,int width,int height,String name){
        Bitmap image=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);root.draw(new Canvas(image));
        File dir=activity.getExternalFilesDir("ui-acceptance");assertNotNull(dir);
        try(FileOutputStream out=new FileOutputStream(new File(dir,name))){assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,out));}
        catch(Exception failure){throw new AssertionError("Could not save UI rendering",failure);}finally{image.recycle();}
    }
    @Test public void viewportHasNoScrollAndAllControlsFit() throws Exception {
        Instrumentation instrument=InstrumentationRegistry.getInstrumentation();
        String pkg=instrument.getTargetContext().getPackageName();
        android.content.SharedPreferences preferences=instrument.getTargetContext().getSharedPreferences(FriendsActivity.class.getName(),0);
        String priorCountry=preferences.getString("country","ru"),priorTransport=preferences.getString("transport","tcp");
        // MIUI may block startActivitySync from a background test runner. Launch through
        // the standard shell activity command, then inspect this instrumented process.
        try(android.os.ParcelFileDescriptor command=instrument.getUiAutomation().executeShellCommand(
                "am start -n "+pkg+"/com.familyconnect.app.FriendsActivity")){
            try(java.io.FileInputStream input=new java.io.FileInputStream(command.getFileDescriptor())){while(input.read()!=-1){}}
        }
        AtomicReference<FriendsActivity> found=new AtomicReference<>();
        long deadline=SystemClock.uptimeMillis()+15000;
        while(found.get()==null&&SystemClock.uptimeMillis()<deadline){
            instrument.runOnMainSync(()->{
                for(Activity activity:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED)){
                    if(activity instanceof FriendsActivity&&activity.findViewById(android.R.id.content).getWidth()>0)found.set((FriendsActivity)activity);
                }
            });
            if(found.get()==null)SystemClock.sleep(100);
        }
        assertNotNull("Friends dashboard did not resume within 15 seconds",found.get());
        instrument.runOnMainSync(()->found.get().navigate(0));
        SystemClock.sleep(1300);
        instrument.runOnMainSync(()->{
            FriendsActivity activity=found.get();
            View root=((ViewGroup)activity.findViewById(android.R.id.content)).getChildAt(0);
            int w=root.getWidth(),h=root.getHeight();assertTrue(w>0&&h>0);
            try{
                for(String fieldName:new String[]{"countries","transports"}){
                    java.lang.reflect.Field f=FriendsActivity.class.getDeclaredField(fieldName);f.setAccessible(true);
                    View selector=(View)f.get(activity);assertTrue("Selectors belong beside battery",selector.getParent() instanceof LiveNetworkPanel);
                    assertTrue("Inline selector must be visible",selector.isShown());
                    assertTrue("Inline selector must have usable width",selector.getWidth()>TerminalUi.dp(activity,80));
                    android.widget.Spinner picker=(android.widget.Spinner)selector;
                    assertNotNull("Selected label must exist",picker.getSelectedView());
                    assertTrue("Selected label must be measured",picker.getSelectedView().getMeasuredWidth()>TerminalUi.dp(activity,60));
                }
            }catch(ReflectiveOperationException e){throw new AssertionError(e);}

            assertNull("No duplicate route button",findButton(root,activity.getString(R.string.dashboard_route)));
            assertNull("Activation moved to settings",findButton(root,activity.getString(R.string.friends_activate)));
            assertFalse("Version belongs in settings",containsText(root,TerminalUi.version(activity)));
            try{
                render(activity,root,w,h,"dashboard-native.png");
                render(activity,root,TerminalUi.dp(activity,320),TerminalUi.dp(activity,512),"dashboard-320x512.png");
            }finally{root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);root.requestLayout();}
            // Draw both switch states without changing preferences or the real VPN.
            android.widget.LinearLayout states=new android.widget.LinearLayout(activity);states.setOrientation(1);states.setBackgroundColor(TerminalUi.BACKGROUND);
            for(boolean checked:new boolean[]{false,true}){
                TerminalToggle toggle=new TerminalToggle(activity);toggle.setText(R.string.dashboard_motion);toggle.setMotion(false);toggle.setChecked(checked);
                states.addView(toggle,new android.widget.LinearLayout.LayoutParams(-1,TerminalUi.dp(activity,52)));
            }
            render(activity,states,TerminalUi.dp(activity,360),TerminalUi.dp(activity,104),"switch-states.png");
            // Synthetic conversation only: never send messages to real contacts.
            java.util.concurrent.atomic.AtomicReference<String> sent=new java.util.concurrent.atomic.AtomicReference<>();
            ChatThreadView sample=new ChatThreadView(activity,"Привет ",ignored->{},sent::set);
            com.google.gson.JsonObject history=new com.google.gson.JsonObject();history.addProperty("offset",0);history.addProperty("total",2);history.add("next_offset",com.google.gson.JsonNull.INSTANCE);
            com.google.gson.JsonArray messages=new com.google.gson.JsonArray();
            for(boolean outgoing:new boolean[]{false,true}){com.google.gson.JsonObject m=new com.google.gson.JsonObject();m.addProperty("text",outgoing?"UI TEST: ICQ :) ;)":"UI TEST: Привет! :D");m.addProperty("timestamp",1_790_000_000);m.addProperty("status",outgoing?"delivered":"received");m.addProperty("outgoing",outgoing);messages.add(m);}history.add("messages",messages);
            sample.show(history,()->{},()->{});sample.insertSmiley(":)");assertEquals("Привет :)",sample.composer.getText().toString());
            sample.composer.setSelection(3);sample.show(history,()->{},()->{});assertEquals("Refresh must preserve cursor",3,sample.composer.getSelectionStart());
            assertEquals("Refresh must preserve draft","Привет :)",sample.composer.getText().toString());
            assertTrue("ICQ GIF spans must be bound",countSmileySpans(sample)>=3);
            // First and subsequent text lines must reserve the full animated frame.
            ChatSmileyTextView multiline=new ChatSmileyTextView(activity);TerminalUi.textStyle(multiline,24,TerminalUi.TEXT);multiline.setMessage(":)\n*DANCE*");multiline.setTextIsSelectable(true);
            multiline.measure(View.MeasureSpec.makeMeasureSpec(TerminalUi.dp(activity,200),View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(0,View.MeasureSpec.UNSPECIFIED));multiline.layout(0,0,multiline.getMeasuredWidth(),multiline.getMeasuredHeight());
            android.text.Spanned spanText=(android.text.Spanned)multiline.getText();
            for(android.text.style.ImageSpan span:spanText.getSpans(0,spanText.length(),android.text.style.ImageSpan.class)){int line=multiline.getLayout().getLineForOffset(spanText.getSpanStart(span));assertTrue("Full GIF top fits the line",multiline.getLayout().getLineBaseline(line)-span.getDrawable().getBounds().height()>=multiline.getLayout().getLineTop(line));}

            findButton(sample,"➤").performClick();assertEquals("Send preserves original token text","Привет :)",sent.get());
            for(int height:new int[]{512,320}){int width=TerminalUi.dp(activity,320),pixels=TerminalUi.dp(activity,height);sample.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(pixels,View.MeasureSpec.EXACTLY));sample.layout(0,0,width,pixels);Rect composerBounds=new Rect();sample.composer.getDrawingRect(composerBounds);sample.offsetDescendantRectToMyCoords(sample.composer,composerBounds);assertTrue("Composer fits resized viewport",composerBounds.bottom<=pixels&&composerBounds.top>=0);if(height==512)save(activity,sample,width,pixels,"conversation-synthetic.png");}
            sample.setForeground(false);
            if(android.os.Build.VERSION.SDK_INT>=29){
                Button settings=findButton(root,activity.getString(R.string.dashboard_settings_short));assertNotNull(settings);settings.performClick();
            }
        });
        if(android.os.Build.VERSION.SDK_INT>=29){
            SystemClock.sleep(400);
            instrument.runOnMainSync(()->{
                FriendsActivity activity=found.get();
                for(View window:android.view.inspector.WindowInspector.getGlobalWindowViews()){
                    if(window==activity.getWindow().getDecorView()&&window.isShown()&&window.getWidth()>0){
                        save(activity,window,window.getWidth(),window.getHeight(),"settings-native.png");
                        Button close=findButton(window,activity.getString(R.string.dashboard_status));if(close!=null)close.performClick();
                    }
                }
            });
            instrument.runOnMainSync(()->{
                FriendsActivity activity=found.get();View root=activity.findViewById(android.R.id.content);
                Button route=findButton(root,activity.getString(R.string.dashboard_route_short));assertNotNull(route);route.performClick();
            });
            SystemClock.sleep(400);
            instrument.runOnMainSync(()->{
                FriendsActivity activity=found.get();boolean captured=false;
                for(View window:android.view.inspector.WindowInspector.getGlobalWindowViews()){
                    RouteMapView visibleMap=findMap(window);
                    if(window==found.get().getWindow().getDecorView()&&window.isShown()&&visibleMap!=null){
                        assertTrue("Route must occupy the full viewport",window.getHeight()>=activity.findViewById(android.R.id.content).getHeight());
                        save(activity,window,window.getWidth(),window.getHeight(),"route-native.png");captured=true;
                        RouteMapView map=findMap(window);assertNotNull(map);
                        assertNull("Navigation replaces back button",findButton(window,activity.getString(R.string.route_back)));
                        long time=SystemClock.uptimeMillis();float x=map.getWidth()*185/360f,y=map.getHeight()*.78f*33/145f;
                        android.view.MotionEvent down=android.view.MotionEvent.obtain(time,time,0,x,y,0),up=android.view.MotionEvent.obtain(time,time+30,1,x,y,0);
                        map.dispatchTouchEvent(down);map.dispatchTouchEvent(up);down.recycle();up.recycle();
                    }
                }
                assertTrue("Route rendering missing",captured);
            });
            SystemClock.sleep(400);
            instrument.runOnMainSync(()->{
                FriendsActivity activity=found.get();
                for(View window:android.view.inspector.WindowInspector.getGlobalWindowViews()){
                    RouteMapView visibleMap=findMap(window);
                    if(window==found.get().getWindow().getDecorView()&&window.isShown()&&visibleMap!=null){
                        assertTrue("Tapping NL must display region information",containsText(window,activity.getString(R.string.route_preview,activity.getString(R.string.gateway_netherlands))));
                        findButton(window,activity.getString(R.string.dashboard_status)).performClick();
                    }
                }
            });
        }
        instrument.runOnMainSync(()->{
            FriendsActivity activity=found.get();
            assertTabs(activity.findViewById(android.R.id.content),activity,0);
            android.widget.ImageView icon=new android.widget.ImageView(activity);
            icon.setImageDrawable(activity.getApplicationInfo().loadIcon(activity.getPackageManager()));
            render(activity,icon,TerminalUi.dp(activity,144),TerminalUi.dp(activity,144),"launcher-icon.png");
            findButton(activity.findViewById(android.R.id.content),activity.getString(R.string.dashboard_chats)).performClick();
        });
        AtomicReference<ChatActivity> chat=new AtomicReference<>();
        long chatDeadline=SystemClock.uptimeMillis()+20000;
        while(chat.get()==null&&SystemClock.uptimeMillis()<chatDeadline){
            instrument.runOnMainSync(()->{for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))if(a instanceof ChatActivity&&a.findViewById(android.R.id.content).getWidth()>0)chat.set((ChatActivity)a);});
            if(chat.get()==null)SystemClock.sleep(100);
        }
        assertNotNull("Messenger tab must open",chat.get());SystemClock.sleep(500);
        instrument.runOnMainSync(()->{
            View root=chat.get().findViewById(android.R.id.content);assertTabs(root,chat.get(),1);
            save(found.get(),root,root.getWidth(),root.getHeight(),"messenger-native.png");
            findButton(root,chat.get().getString(R.string.dashboard_route_short)).performClick();
        });
        SystemClock.sleep(700);
        instrument.runOnMainSync(()->{
            boolean routeFound=false;
            for(View window:android.view.inspector.WindowInspector.getGlobalWindowViews()){
                RouteMapView visibleMap=findMap(window);
                if(window==found.get().getWindow().getDecorView()&&window.isShown()&&visibleMap!=null){assertTabs(window,found.get(),2);findButton(window,found.get().getString(R.string.dashboard_settings_short)).performClick();routeFound=true;}
            }
            assertTrue("Messenger must navigate directly to route",routeFound);
        });
        SystemClock.sleep(400);
        instrument.runOnMainSync(()->{
            boolean settingsFound=false;
            for(View window:android.view.inspector.WindowInspector.getGlobalWindowViews()){
                Button settings=findButton(window,found.get().getString(R.string.dashboard_settings_short));
                if(window.isShown()&&settings!=null&&settings.isSelected()){assertTabs(window,found.get(),3);findButton(window,found.get().getString(R.string.dashboard_status)).performClick();settingsFound=true;}
            }
            assertTrue("Settings must retain navigation",settingsFound);
        });
        // Real attached/focused selectable text: validate the animation clock before
        // taking software snapshots, so snapshots themselves cannot drive the test.
        AtomicReference<android.app.Dialog> animationDialog=new AtomicReference<>();
        AtomicReference<ChatSmileyTextView> animated=new AtomicReference<>();
        instrument.runOnMainSync(()->{
            FriendsActivity activity=found.get();android.app.Dialog dialog=new android.app.Dialog(activity);
            ChatSmileyTextView smiley=new ChatSmileyTextView(activity);TerminalUi.textStyle(smiley,30,TerminalUi.TEXT);smiley.setBackgroundColor(TerminalUi.BACKGROUND);smiley.setMessage("UI TEST *DANCE* :D");smiley.setTextIsSelectable(true);smiley.setForegroundActive(true);
            dialog.setContentView(smiley);dialog.show();dialog.getWindow().setLayout(TerminalUi.dp(activity,300),TerminalUi.dp(activity,100));animationDialog.set(dialog);animated.set(smiley);
        });
        try{
            SystemClock.sleep(400);long first=smileyTime(instrument,animated.get());SystemClock.sleep(500);long second=smileyTime(instrument,animated.get());assertTrue("Visible GIF clock must advance without external drawing",second>first);
            AtomicReference<Bitmap> firstFrame=new AtomicReference<>();instrument.runOnMainSync(()->firstFrame.set(smileyFrame(animated.get())));
            boolean different=false;
            for(int attempt=0;attempt<8&&!different;attempt++){SystemClock.sleep(250);AtomicReference<Bitmap> later=new AtomicReference<>();instrument.runOnMainSync(()->later.set(smileyFrame(animated.get())));different=!firstFrame.get().sameAs(later.get());later.get().recycle();}
            firstFrame.get().recycle();assertTrue("GIF pixels must change across frames",different);
            instrument.runOnMainSync(()->animated.get().setForegroundActive(false));long paused=smileyTime(instrument,animated.get());SystemClock.sleep(300);assertEquals("Inactive GIF clock must stop",paused,smileyTime(instrument,animated.get()));
            instrument.runOnMainSync(()->animated.get().setForegroundActive(true));SystemClock.sleep(400);assertTrue("GIF must resume",smileyTime(instrument,animated.get())>paused);
        }finally{instrument.runOnMainSync(()->animationDialog.get().dismiss());}
        assertEquals("Opening screens must preserve country",priorCountry,preferences.getString("country","ru"));
        assertEquals("Opening screens must preserve transport",priorTransport,preferences.getString("transport","tcp"));
    }
    private long smileyTime(Instrumentation instrument,ChatSmileyTextView view){
        java.util.concurrent.atomic.AtomicLong time=new java.util.concurrent.atomic.AtomicLong();instrument.runOnMainSync(()->{try{java.lang.reflect.Field field=ChatSmileyTextView.class.getDeclaredField("time");field.setAccessible(true);time.set(field.getLong(view));}catch(Exception failure){throw new AssertionError(failure);}});return time.get();
    }
    private Bitmap smileyFrame(ChatSmileyTextView view){Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));return bitmap;}
    private int countSmileySpans(View view){
        int count=0;if(view instanceof ChatSmileyTextView&&((ChatSmileyTextView)view).getText() instanceof android.text.Spanned){android.text.Spanned text=(android.text.Spanned)((ChatSmileyTextView)view).getText();count=text.getSpans(0,text.length(),android.text.style.ImageSpan.class).length;}
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)count+=countSmileySpans(((ViewGroup)view).getChildAt(i));return count;
    }
    private void assertTabs(View root,Activity activity,int selected){
        int[] ids={R.string.dashboard_status,R.string.dashboard_chats,R.string.dashboard_route_short,R.string.dashboard_settings_short};
        for(int i=0;i<ids.length;i++){Button button=findButton(root,activity.getString(ids[i]));assertNotNull("Missing persistent tab",button);assertTrue(button.isShown());assertEquals(i==selected,button.isSelected());}
    }
    private RouteMapView findMap(View view){
        if(view instanceof RouteMapView)return (RouteMapView)view;
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){RouteMapView found=findMap(((ViewGroup)view).getChildAt(i));if(found!=null)return found;}
        return null;
    }
    private boolean containsText(View view,String text){
        if(view instanceof android.widget.TextView&&text.contentEquals(((android.widget.TextView)view).getText()))return true;
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)if(containsText(((ViewGroup)view).getChildAt(i),text))return true;
        return false;
    }
    private Button findButton(View view,String text){
        if(view instanceof Button&&text.contentEquals(((Button)view).getText()))return (Button)view;
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){
            Button found=findButton(((ViewGroup)view).getChildAt(i),text);if(found!=null)return found;
        }
        return null;
    }
    @Test public void switchesFollowStateWithoutTriggeringConnection(){
        Instrumentation instrument=InstrumentationRegistry.getInstrumentation();
        // Packaging regression: compressed APK libraries must load in the target process.
        NativeTcp.load(instrument.getTargetContext());
        instrument.runOnMainSync(()->{
            TerminalToggle toggle=new TerminalToggle(instrument.getTargetContext());toggle.setText(R.string.dashboard_motion);toggle.setMotion(false);
            toggle.setControlled(true);toggle.performClick();assertFalse(toggle.isChecked());
            toggle.setChecked(true);assertTrue(toggle.isChecked());
            toggle.setControlled(false);toggle.performClick();assertFalse(toggle.isChecked());
            toggle.performClick();assertTrue(toggle.isChecked());
        });
    }
}
