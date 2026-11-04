package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class GatewayPickerTest {
    @Test public void ordinaryTransportsShowExactlyTwoAmsterdamNodesAndRussia(){
        for(String transport:new String[]{"awg","tcp"}){
            assertArrayEquals(new String[]{"nl-amsterdam-1","ru","nl-amsterdam-2"},GatewayPicker.targets(transport));
            assertEquals("nl-amsterdam-1",GatewayPicker.target("nl","",transport));
            assertEquals("nl-amsterdam-1",GatewayPicker.target("nl","unknown",transport));
            for(String gateway:new String[]{"nl-amsterdam-1","nl-amsterdam-2"}){
                assertEquals(gateway,GatewayPicker.target("nl",gateway,transport));
                assertEquals("ru",GatewayPicker.target("ru",gateway,transport));
            }
        }
    }

    @Test public void automaticRemainsCountryBasedRegardlessOfSavedManualNode(){
        assertArrayEquals(new String[]{"nl","ru"},GatewayPicker.targets("auto"));
        for(String gateway:new String[]{"","nl-amsterdam-1","nl-amsterdam-2"}){
            assertEquals("nl",GatewayPicker.target("nl",gateway,"auto"));
            assertEquals("nl",GatewayPicker.target(gateway,gateway,"auto"));
            assertEquals("ru",GatewayPicker.target("ru",gateway,"auto"));
        }
    }

    @Test public void meshShowsOnlyItsTwoAmsterdamNodesAndRetainsTheManualTarget(){
        assertTrue(GatewayPicker.manual("telemost"));
        assertArrayEquals(new String[]{"nl-amsterdam-1","nl-amsterdam-2"},GatewayPicker.targets("telemost"));
        for(String country:new String[]{"nl","ru","nl-amsterdam-1","nl-amsterdam-2"}){
            for(String gateway:new String[]{"nl-amsterdam-1","nl-amsterdam-2"}){
                assertEquals(gateway,GatewayPicker.target(country,gateway,"telemost"));
            }
            assertEquals("nl-amsterdam-1",GatewayPicker.target(country,"","telemost"));
            assertEquals("nl-amsterdam-1",GatewayPicker.target(country,"unknown","telemost"));
        }
        assertFalse(GatewayPicker.manual("auto"));
    }

    @Test public void returnedChoicesCannotMutateSubsequentModels(){
        GatewayPicker.targets("tcp")[0]="nl";
        GatewayPicker.targets("auto")[0]="nl-amsterdam-2";
        GatewayPicker.targets("telemost")[0]="ru";
        assertEquals("nl-amsterdam-1",GatewayPicker.targets("tcp")[0]);
        assertEquals("nl",GatewayPicker.targets("auto")[0]);
        assertEquals("nl-amsterdam-1",GatewayPicker.targets("telemost")[0]);
    }

    @Test public void selectedSecondaryMeshRefreshesBothItsOwnCacheAndThePrimaryChatCache(){
        assertArrayEquals(new String[]{"nl-amsterdam-1","nl-amsterdam-2"},GatewayPicker.readinessTargets("nl-amsterdam-2","telemost"));
        for(String target:new String[]{"nl-amsterdam-1","nl","ru","unknown",null}){
            assertArrayEquals(new String[]{"nl-amsterdam-1"},GatewayPicker.readinessTargets(target,"telemost"));
        }
        for(String transport:new String[]{"auto","awg","tcp","unknown",null}){
            assertArrayEquals(new String[]{"nl-amsterdam-1"},GatewayPicker.readinessTargets("nl-amsterdam-2",transport));
        }
    }

    @Test public void readinessChoicesCannotMutateOtherScopesOrLaterSelections(){
        GatewayPicker.readinessTargets("nl-amsterdam-2","telemost")[0]="ru";
        GatewayPicker.readinessTargets("nl-amsterdam-1","telemost")[0]="nl-amsterdam-2";
        assertArrayEquals(new String[]{"nl-amsterdam-1","nl-amsterdam-2"},GatewayPicker.readinessTargets("nl-amsterdam-2","telemost"));
        assertArrayEquals(new String[]{"nl-amsterdam-1"},GatewayPicker.readinessTargets("nl-amsterdam-1","telemost"));
    }
}
