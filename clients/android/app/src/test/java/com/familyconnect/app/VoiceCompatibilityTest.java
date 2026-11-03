package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class VoiceCompatibilityTest {
    @Test public void legacyDevicesNeverChooseUnsupportedOpusRecording(){
        for(int sdk:new int[]{26,27,28}){
            assertEquals(9,VoiceCompatibility.mode(16,sdk));
            assertEquals(9,VoiceCompatibility.mode(-1,sdk));
            assertArrayEquals(new int[]{7,8,9},VoiceCompatibility.modes(sdk));
        }
    }
    @Test public void modernDefaultAndExplicitRadioChoicesArePreserved(){
        for(int sdk:new int[]{29,31,35}){
            assertEquals(16,VoiceCompatibility.mode(16,sdk));
            assertArrayEquals(new int[]{16,7,8,9},VoiceCompatibility.modes(sdk));
        }
        for(int sdk:new int[]{27,35})for(int selected:new int[]{7,8,9})assertEquals(selected,VoiceCompatibility.mode(selected,sdk));
    }
}
