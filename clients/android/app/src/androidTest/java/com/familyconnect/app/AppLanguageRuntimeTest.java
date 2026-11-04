package com.familyconnect.app;
import android.app.*;
import android.content.*;
import android.os.*;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.*;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AppLanguageRuntimeTest {
    @org.junit.Before public void friendsVariantOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }
    private FriendsActivity current(){for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))if(a instanceof FriendsActivity)return (FriendsActivity)a;return null;}
    @Test public void languageSurvivesRecreationAndAllScreensUseSharedSelection()throws Exception{
        Instrumentation ins=InstrumentationRegistry.getInstrumentation();Context c=ins.getTargetContext();String before=AppLanguage.selected(c);
        try(ParcelFileDescriptor command=ins.getUiAutomation().executeShellCommand("am start -W -n "+c.getPackageName()+"/com.familyconnect.app.FriendsActivity")){try(InputStream in=new FileInputStream(command.getFileDescriptor())){while(in.read()!=-1){}}}
        SystemClock.sleep(700);
        try{
            for(String language:new String[]{"en","ru"}){
                AtomicReference<FriendsActivity> previous=new AtomicReference<>();
                ins.runOnMainSync(()->{
                    FriendsActivity activity=current();assertNotNull(activity);previous.set(activity);
                    android.widget.Spinner picker=activity.getWindow().getDecorView().findViewWithTag("app_language");
                    AppLanguage.select(activity,language);
                    if(picker!=null){
                        picker.getOnItemSelectedListener().onItemSelected(picker,picker.getSelectedView(),picker.getSelectedItemPosition(),picker.getSelectedItemId());
                        assertEquals("Old settings callback cannot undo a newer language selection",language,AppLanguage.selected(c));
                    }
                    activity.getIntent().putExtra("tab",3);activity.recreate();
                });
                AtomicReference<String> text=new AtomicReference<>();long until=SystemClock.elapsedRealtime()+15000;
                while(SystemClock.elapsedRealtime()<until){
                    ins.runOnMainSync(()->{
                        FriendsActivity activity=current();
                        if(activity!=null&&activity!=previous.get()&&!activity.isFinishing()&&!activity.isDestroyed()
                                &&language.equals(activity.getResources().getConfiguration().getLocales().get(0).getLanguage()))text.set(activity.getString(R.string.dashboard_settings));
                    });
                    if((language.equals("en")?"Settings":"Настройки").equals(text.get()))break;SystemClock.sleep(100);
                }
                assertEquals(language.equals("en")?"Settings":"Настройки",text.get());assertEquals(language,AppLanguage.selected(c));
                ins.runOnMainSync(()->{
                    FriendsActivity activity=current();assertNotNull(activity);
                    assertEquals(language.equals("ru")?"Россия":"Russia",activity.getString(R.string.gateway_russia));
                    assertEquals(language.equals("ru")?"Нидерланды":"Netherlands",activity.getString(R.string.gateway_amsterdam_1));
                    assertEquals(language.equals("ru")?"Нидерланды 2":"Netherlands 2",activity.getString(R.string.gateway_amsterdam_2));
                    try{new DashboardLayoutRuntimeTest().verifyPickerLanguage(activity,language);}
                    catch(ReflectiveOperationException failure){throw new AssertionError(failure);}
                });
                assertEquals(language,AppLanguage.wrap(c).getResources().getConfiguration().getLocales().get(0).getLanguage());
            }
            for(Class<?> screen:new Class<?>[]{FriendsActivity.class,MainActivity.class,ChatActivity.class,ReferralActivity.class})assertTrue(LocalizedActivity.class.isAssignableFrom(screen));
        }finally{ins.runOnMainSync(()->{AppLanguage.select(c,before);FriendsActivity a=current();if(a!=null){a.getIntent().putExtra("tab",3);a.recreate();}});}
    }
}
