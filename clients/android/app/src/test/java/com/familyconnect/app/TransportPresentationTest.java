package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.util.Locale;
import org.junit.Test;
import static org.junit.Assert.*;

public class TransportPresentationTest {
    @Test public void legacyIdsRemainPresentationOnly(){
        assertEquals("MESH",TransportPresentation.label("telemost"));
        assertEquals("MESH",TransportPresentation.label("restricted"));
        assertEquals("Auto",TransportPresentation.label("auto"));
        assertEquals("AWG 3.1",TransportPresentation.label("awg"));
        assertEquals("TCP REALITY",TransportPresentation.label("tcp"));
        assertEquals("WireGuard",TransportPresentation.label("wg"));
        assertEquals("—",TransportPresentation.label("mesh"));
        assertEquals("—",TransportPresentation.label(null));
    }

    @Test public void productNameIsNotLocalized(){
        Locale before=Locale.getDefault();
        try{
            for(Locale locale:new Locale[]{Locale.ENGLISH,Locale.forLanguageTag("ru")}){
                Locale.setDefault(locale);
                assertEquals("MESH",TransportPresentation.label("telemost"));
            }
        }finally{Locale.setDefault(before);}
    }

    @Test public void diagnosticMetadataDoesNotInventProtocolOrCapabilities(){
        JsonObject catalog=TransportPresentation.diagnostics();
        assertEquals(1,catalog.get("schema").getAsInt());
        JsonObject media=catalog.getAsJsonObject("restricted");
        assertEquals("MESH",media.get("name").getAsString());
        assertEquals("restricted",media.get("implementation").getAsString());
        assertEquals("telemost",media.get("selection_id").getAsString());
        assertEquals("VP8/RTP",media.get("carrier").getAsString());
        assertEquals("Telemost",media.get("provider").getAsString());
        assertEquals(5,media.size());
        media.addProperty("name","tampered");
        assertEquals("MESH",TransportPresentation.diagnostics().getAsJsonObject("restricted").get("name").getAsString());
    }
}
