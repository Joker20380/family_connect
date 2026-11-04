package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class GatewayPickerTest {
    @Test public void everyModeShowsTheSamePhysicalServersInTheSameOrder(){
        for(String transport:new String[]{"auto","awg","tcp","telemost"}){
            assertArrayEquals(new String[]{"ru","nl-amsterdam-1","nl-amsterdam-2"},GatewayPicker.targets(transport));
            for(String target:GatewayPicker.targets(transport)){
                assertEquals(target,GatewayPicker.target(target,"nl-amsterdam-1",transport));
                assertEquals(target,GatewayPicker.target(target,"nl-amsterdam-2",transport));
            }
        }
    }

    @Test public void legacyCountryPreferencesRecoverTheSavedNodeWithoutChangingRussia(){
        for(String transport:new String[]{"auto","awg","tcp","telemost"}){
            assertEquals("nl-amsterdam-1",GatewayPicker.target("nl","",transport));
            assertEquals("nl-amsterdam-1",GatewayPicker.target("nl","unknown",transport));
            assertEquals("nl-amsterdam-2",GatewayPicker.target("nl","nl-amsterdam-2",transport));
            assertEquals("ru",GatewayPicker.target("ru","nl-amsterdam-2",transport));
        }
    }

    @Test public void unsupportedRussiaMeshIsVisibleButCannotBecomeANetherlandsTunnel(){
        assertFalse(GatewayPicker.available("ru","telemost"));
        assertFalse(GatewayPicker.meshSupported("ru"));
        assertFalse(GatewayPicker.meshSupported("unknown"));
        for(String transport:new String[]{"auto","awg","tcp"})assertTrue(GatewayPicker.available("ru",transport));
        for(String target:new String[]{null,"nl","nl-amsterdam-1","nl-amsterdam-2"})assertTrue(GatewayPicker.meshSupported(target));
    }

    @Test public void choicesAreFreshAndComeFromTheAdmittedGatewayRegistry(){
        GatewayPicker.targets("telemost")[0]="unknown";
        assertEquals("ru",GatewayPicker.targets("auto")[0]);
        assertEquals(ControlFriendsCatalog.GATEWAYS.size()+1,GatewayPicker.targets("auto").length);
        for(String gateway:ControlFriendsCatalog.GATEWAYS)assertTrue(java.util.Arrays.asList(GatewayPicker.targets("auto")).contains(gateway));
    }

    @Test public void secondaryAutoAndMeshRefreshTheirOwnCacheAndThePrimaryChatCache(){
        for(String transport:new String[]{"auto","telemost"}){
            assertArrayEquals(new String[]{"nl-amsterdam-1","nl-amsterdam-2"},GatewayPicker.readinessTargets("nl-amsterdam-2",transport));
            for(String target:new String[]{"nl-amsterdam-1","nl","ru","unknown",null})
                assertArrayEquals(new String[]{"nl-amsterdam-1"},GatewayPicker.readinessTargets(target,transport));
        }
        for(String transport:new String[]{"awg","tcp","unknown",null})
            assertArrayEquals(new String[]{"nl-amsterdam-1"},GatewayPicker.readinessTargets("nl-amsterdam-2",transport));
    }

    @Test public void readinessChoicesCannotMutateOtherScopes(){
        GatewayPicker.readinessTargets("nl-amsterdam-2","auto")[0]="ru";
        assertArrayEquals(new String[]{"nl-amsterdam-1","nl-amsterdam-2"},GatewayPicker.readinessTargets("nl-amsterdam-2","telemost"));
    }
}
