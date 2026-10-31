package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class SpeedProfileTest {
    @Test public void selectionRequiresIdleDisconnected() {
        assertTrue(SpeedProfile.canSelect("off",false));
        assertFalse(SpeedProfile.canSelect("off",true));
        for(String state:new String[]{"on","connecting","recovering","failed",null})assertFalse(SpeedProfile.canSelect(state,false));
    }
    @Test public void finiteProfiles() { for(int profile=0;profile<3;profile++)assertEquals(profile,SpeedProfile.checked(profile)); }
    @Test(expected=IllegalArgumentException.class) public void rejectsNegative() { SpeedProfile.checked(-1); }
    @Test(expected=IllegalArgumentException.class) public void rejectsUnknown() { SpeedProfile.checked(3); }
}
