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

    @Test public void automaticAndMeshRemainCountryBasedRegardlessOfSavedManualNode(){
        for(String transport:new String[]{"auto","telemost"}){
            assertArrayEquals(new String[]{"nl","ru"},GatewayPicker.targets(transport));
            for(String gateway:new String[]{"","nl-amsterdam-1","nl-amsterdam-2"}){
                assertEquals("nl",GatewayPicker.target("nl",gateway,transport));
                assertEquals("nl",GatewayPicker.target(gateway,gateway,transport));
                assertEquals("ru",GatewayPicker.target("ru",gateway,transport));
            }
        }
    }

    @Test public void returnedChoicesCannotMutateSubsequentModels(){
        GatewayPicker.targets("tcp")[0]="nl";
        GatewayPicker.targets("auto")[0]="nl-amsterdam-2";
        assertEquals("nl-amsterdam-1",GatewayPicker.targets("tcp")[0]);
        assertEquals("nl",GatewayPicker.targets("auto")[0]);
    }
}
