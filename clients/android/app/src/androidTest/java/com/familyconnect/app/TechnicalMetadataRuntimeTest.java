package com.familyconnect.app;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.net.NetworkCapabilities;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class TechnicalMetadataRuntimeTest {
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
        NetworkCapabilities caps=new NetworkCapabilities().addTransportType(NetworkCapabilities.TRANSPORT_VPN).addTransportType(NetworkCapabilities.TRANSPORT_WIFI);
        assertEquals("WIFI",TechnicalMetadataAndroid.kind(caps));
        caps.addTransportType(NetworkCapabilities.TRANSPORT_CELLULAR);
        assertEquals("UNKNOWN",TechnicalMetadataAndroid.kind(caps));
        caps.removeTransportType(NetworkCapabilities.TRANSPORT_WIFI);
        assertEquals("CELLULAR",TechnicalMetadataAndroid.kind(caps));
    }
}
