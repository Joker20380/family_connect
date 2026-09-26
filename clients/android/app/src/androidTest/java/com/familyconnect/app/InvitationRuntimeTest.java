package com.familyconnect.app;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import java.io.FileInputStream;
import java.lang.reflect.Field;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

/** Real implicit URI dispatch; busy guard prevents registration/network requests. */
public class InvitationRuntimeTest {
    private final Instrumentation ins=InstrumentationRegistry.getInstrumentation();
    private FriendsActivity current(){
        for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))
            if(a instanceof FriendsActivity)return (FriendsActivity)a;
        return null;
    }
    private void shell(String command)throws Exception{
        try(ParcelFileDescriptor fd=ins.getUiAutomation().executeShellCommand(command);
            FileInputStream in=new FileInputStream(fd.getFileDescriptor())){while(in.read()!=-1){}}
        ins.waitForIdleSync();
    }
    @Test public void browsableLinksReuseActivityAndRejectMalformedToken()throws Exception{
        Context context=ins.getTargetContext();String pkg=context.getPackageName();
        assumeTrue(pkg.endsWith(".friends"));
        // CI-only, unactivated fixture; never run this against a user's identity.
        assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcInvitationCi")));
        assertFalse(context.getSharedPreferences(FriendsActivity.class.getName(),0).getBoolean("activated",false));
        shell("am start -W -n "+pkg+"/com.familyconnect.app.FriendsActivity");
        AtomicReference<FriendsActivity> found=new AtomicReference<>();
        long until=SystemClock.elapsedRealtime()+10000;
        while(found.get()==null&&SystemClock.elapsedRealtime()<until){ins.runOnMainSync(()->found.set(current()));SystemClock.sleep(50);}
        FriendsActivity activity=found.get();assertNotNull(activity);
        Field busy=FriendsActivity.class.getDeclaredField("busy");busy.setAccessible(true);
        Field pending=FriendsActivity.class.getDeclaredField("pendingInvitation");pending.setAccessible(true);
        ins.runOnMainSync(()->{try{assertFalse(busy.getBoolean(activity));busy.setBoolean(activity,true);}catch(ReflectiveOperationException e){throw new AssertionError(e);}});
        try{
            for(char letter:new char[]{'a','b'}){
                String token=new String(new char[64]).replace('\0',letter),uri="familyconnect://invite/"+token;
                Intent intent=new Intent(Intent.ACTION_VIEW,Uri.parse(uri)).addCategory(Intent.CATEGORY_BROWSABLE).setPackage(pkg);
                assertNotNull(intent.resolveActivity(context.getPackageManager()));
                shell("am start -W -a android.intent.action.VIEW -c android.intent.category.BROWSABLE -p "+pkg+" -d "+uri);
                ins.runOnMainSync(()->{try{assertSame(activity,current());assertEquals(token,pending.get(activity));assertNull(activity.getIntent().getData());}catch(ReflectiveOperationException e){throw new AssertionError(e);}});
            }
            shell("am start -W -a android.intent.action.VIEW -p "+pkg+" -d familyconnect://invite/invalid");
            ins.runOnMainSync(()->{try{assertSame(activity,current());assertEquals(new String(new char[64]).replace('\0','b'),pending.get(activity));}catch(ReflectiveOperationException e){throw new AssertionError(e);}});
        }finally{
            ins.runOnMainSync(()->{try{pending.set(activity,"");busy.setBoolean(activity,false);activity.navigate(0);}catch(ReflectiveOperationException e){throw new AssertionError(e);}});
        }
    }
}
