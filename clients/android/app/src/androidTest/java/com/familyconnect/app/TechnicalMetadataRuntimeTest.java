package com.familyconnect.app;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.net.NetworkCapabilities;
import android.net.ConnectivityManager;
import android.net.Network;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class TechnicalMetadataRuntimeTest {
    @Test public void basicPublicApiSnapshotOmitsExtendedFields(){
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        JsonObject groups=TechnicalMetadataAndroid.sample(context,true);
        JsonObject profile=groups.getAsJsonObject("profile").getAsJsonObject("values");
        assertEquals(3,profile.size());assertEquals("Android",profile.get("os").getAsString());
        assertEquals(Build.VERSION.RELEASE,profile.get("os_version").getAsString());
        for(String forbidden:new String[]{"manufacturer","model","radio","radio_reason","readiness","preference","city","country","region","ip"})
            assertFalse(groups.toString().contains("\""+forbidden+"\""));
        assertTrue(groups.getAsJsonObject("mobile").getAsJsonObject("values").has("sim_reason"));
    }
    @Test public void publicApiProfileAndRadioFallbackWithoutNewPhonePermission(){
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertNotEquals(PackageManager.PERMISSION_GRANTED,context.checkSelfPermission(android.Manifest.permission.READ_PHONE_STATE));
        JsonObject groups=TechnicalMetadataAndroid.sample(context);
        JsonObject profile=groups.getAsJsonObject("profile").getAsJsonObject("values");
        assertEquals(Build.VERSION.SDK_INT,profile.get("api_level").getAsInt());
        assertEquals(BuildConfig.VERSION_CODE,profile.get("version_code").getAsInt());
        assertFalse(profile.get("model").isJsonNull());assertFalse(profile.get("manufacturer").isJsonNull());
        JsonObject mobile=groups.getAsJsonObject("mobile").getAsJsonObject("values");
        String radio=mobile.get("radio").getAsString();
        if(Build.VERSION.SDK_INT<33)assertEquals("UNKNOWN",radio);
        if("UNKNOWN".equals(radio))assertNotEquals("none",mobile.get("radio_reason").getAsString());
        else{assertTrue("LTE_4G".equals(radio)||"5G".equals(radio));assertEquals("none",mobile.get("radio_reason").getAsString());}
        for(String forbidden:new String[]{"imei","phone_number","ssid","bssid","cell_id","latitude","longitude","installed_apps","ip"})assertFalse(groups.toString().contains("\""+forbidden+"\""));
    }
    @Test public void newConsentDoesNotInheritSevenDayDiagnostics(){
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertFalse(context.getSharedPreferences("technical-metadata-v1",Context.MODE_PRIVATE).getBoolean("enabled",false));
    }
    @Test public void platformVpnTransportCapabilitiesDoNotPickFirstOfMultipleUnderlays(){
        assertEquals("WIFI",TechnicalMetadataSnapshot.networkKind(true,false,false));
        assertEquals("UNKNOWN",TechnicalMetadataSnapshot.networkKind(true,true,false));
        assertEquals("CELLULAR",TechnicalMetadataSnapshot.networkKind(false,true,false));
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        assertNotNull(manager);
        Network network=manager.getActiveNetwork();
        assertNotNull("Qualification requires a connected Android testbed",network);
        NetworkCapabilities caps=manager.getNetworkCapabilities(network);
        assertNotNull(caps);
        assertFalse("Run this observation before VPN session tests",caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN));
        assertTrue(caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN));
        JsonObject observation=TechnicalMetadataAndroid.network(context,System.currentTimeMillis());
        assertEquals("android_default_network",observation.get("source").getAsString());
        assertEquals("available",observation.get("status").getAsString());
        assertEquals(TechnicalMetadataAndroid.kind(caps),observation.getAsJsonObject("values").get("kind").getAsString());
        assertNotEquals("UNKNOWN",observation.getAsJsonObject("values").get("kind").getAsString());
    }
}
