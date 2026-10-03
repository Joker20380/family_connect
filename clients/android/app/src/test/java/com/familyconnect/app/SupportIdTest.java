package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class SupportIdTest {
    @Test public void acceptsOnlySafeHumanIdentifiers(){
        assertTrue(SupportId.valid("FC-7K4M-29QX"));
        for(String value:new String[]{null,"","fc-7k4m-29qx","FC-0000-1111","0123456789abcdef0123456789abcdef","https://room/private","FC-7K4M-29QX\n"})assertFalse(SupportId.valid(value));
    }
    @Test public void diagnosticsUsesOnlyBoundSupportIdentifier(){
        DiagnosticRing ring=new DiagnosticRing(null,"0.1.18-beta59",59,31);
        ring.support("FC-7K4M-29QX");assertEquals("FC-7K4M-29QX",ring.snapshot().get("device_support_id").getAsString());
        ring.support("private-identity");assertFalse(ring.snapshot().toString().contains("private-identity"));
    }
}
