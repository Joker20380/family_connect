package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public final class Ui60PresentationTest {
    @Test public void batteryBarUsesOnlyValidObservedPercent(){
        assertEquals(0f,Ui60Presentation.batteryFraction("0%"),0f);
        assertEquals(.42f,Ui60Presentation.batteryFraction("42%"),0f);
        assertEquals(1f,Ui60Presentation.batteryFraction("100%"),0f);
        for(String value:new String[]{null,"—","42","101%","-1%","unknown%"})assertEquals(-1f,Ui60Presentation.batteryFraction(value),0f);
    }
    @Test public void truthfulStates(){
        assertEquals(R.string.off,Ui60Presentation.status("off",false));
        assertEquals(R.string.connecting,Ui60Presentation.status("connecting",false));
        assertEquals(R.string.on,Ui60Presentation.status("on",false));
        assertEquals(R.string.ui_disconnecting,Ui60Presentation.status("disconnecting",false));
        assertEquals(R.string.ui_cleanup_required,Ui60Presentation.status("cleanup-required",false));
        assertEquals(R.string.restoring,Ui60Presentation.status("restoring",false));
        assertEquals(R.string.unable_connect,Ui60Presentation.status("failed",true));
        assertEquals(R.string.unable_connect,Ui60Presentation.status("off",true));
        assertEquals(R.string.connecting,Ui60Presentation.status("tun-created",false));
    }
    @Test public void previewDoesNotStealMinimumControlsSpace(){
        assertEquals(209,Ui60Presentation.dialHeight(348,780,120));
        assertEquals(166,Ui60Presentation.dialHeight(276,640,120));
        assertEquals(120,Ui60Presentation.dialHeight(736,392,120));
        assertEquals(188,Ui60Presentation.compactDialHeight(209,120,21));
        assertEquals(120,Ui60Presentation.compactDialHeight(166,120,300));
        assertEquals(209,Ui60Presentation.compactDialHeight(209,120,-30));
        assertEquals(156,Ui60Presentation.mapHeight(368,6,145f/360f));
        assertEquals(127,Ui60Presentation.mapHeight(296,6,145f/360f));
        assertEquals(311,Ui60Presentation.mapHeight(736,12,145f/360f));
        assertEquals(161,Ui60Presentation.mapHeight(368,6,150f/360f));
    }
}
