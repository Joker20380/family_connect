package com.familyconnect.app;

import android.app.Activity;
import android.content.Intent;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class VpnHandoverRuntimeTest {
    @Test public void activeApplicationVpnTransfersOnlyAfterSystemResult() throws Exception {
        AwgRuntimeTest helper = new AwgRuntimeTest();
        helper.clean();
        ControlOperations.APP.requireIdle();
        helper.shell("appops set " + helper.context.getPackageName() + " ACTIVATE_VPN allow");
        helper.shell("pm grant " + helper.context.getPackageName() + " android.permission.POST_NOTIFICATIONS");
        Intent launch = helper.context.getPackageManager().getLaunchIntentForPackage(helper.context.getPackageName());
        assertNotNull(launch);
        Activity activity = InstrumentationRegistry.getInstrumentation().startActivitySync(launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        ProfileStore profiles = new ProfileStore(helper.context, Transport.AWG);
        try {
            profiles.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.AWG), Transport.AWG));
            helper.context.startForegroundService(new Intent(helper.context, ConnectionService.class).setAction("connect").putExtra("transport", "awg"));
            helper.waitState("on");
            helper.traffic(Transport.AWG);
            helper.handoverState("active-application-before-revoke");
            helper.shell("appops set " + helper.context.getPackageName() + " ACTIVATE_VPN deny");
            helper.revokeThroughSystemDialog();
            helper.waitState("off");
            helper.clean();
            ControlOperations.APP.requireIdle();
            assertNotNull(android.net.VpnService.prepare(helper.context));
        } finally {
            helper.context.startService(new Intent(helper.context, ConnectionService.class).setAction("disconnect"));
            helper.waitState("off");
            helper.clean();
            ControlOperations.APP.requireIdle();
            profiles.clear();
            InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
        }
    }
    @Test public void freshAndPreviouslyAuthorizedTestPackage() throws Exception {
        AwgRuntimeTest helper = new AwgRuntimeTest();
        helper.clean();
        ControlOperations.APP.requireIdle();
        Intent launch = helper.context.getPackageManager().getLaunchIntentForPackage(helper.context.getPackageName());
        assertNotNull(launch);
        Activity activity = InstrumentationRegistry.getInstrumentation().startActivitySync(launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        String testPackage = InstrumentationRegistry.getInstrumentation().getContext().getPackageName();
        try {
            for (String previous : new String[]{"default", "allow"}) {
                helper.handoverCommand("previous-" + previous, "appops set " + testPackage + " ACTIVATE_VPN " + previous);
                helper.revokeThroughSystemDialog();
                helper.handoverCommand("after-confirmation", "appops get " + testPackage + " ACTIVATE_VPN");
                helper.clean();
                ControlOperations.APP.requireIdle();
                assertEquals("off", ConnectionService.status);
            }
        } finally {
            helper.shell("appops set " + testPackage + " ACTIVATE_VPN deny");
            InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
            helper.clean();
            ControlOperations.APP.requireIdle();
        }
    }
}
