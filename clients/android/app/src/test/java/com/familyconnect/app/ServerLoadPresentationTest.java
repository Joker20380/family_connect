package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class ServerLoadPresentationTest {
    private ServerLoad sample(double cpu,Double percent,boolean estimated){
        return new ServerLoad("nl",1000,cpu,12.5,7.3,percent,estimated);
    }

    @Test public void freshUnknownCapacityShowsMeasuredCpuNotTotalLoad(){
        ServerLoad source=sample(13.8,null,false);
        ServerLoadPresentation result=ServerLoadPresentation.from(source,"nl",1010,true);
        assertEquals(13.8,result.percent,0);
        assertEquals("CPU сервера · 14%",result.label());
        assertEquals("CPU 14%",result.value);
        assertTrue(result.details.contains("↓ 12.5 / ↑ 7.3 Mbps"));
        assertTrue(result.details.contains("загрузка канала неизвестна"));
        assertNull(source.percent);
    }

    @Test public void englishCpuLabelIsExplicitAndNotAnEstimate(){
        ServerLoadPresentation result=ServerLoadPresentation.from(sample(40,null,true),"nl",1010,false);
        assertEquals("Server CPU · 40%",result.label());
        assertEquals("CPU 40%",result.value);
        assertTrue(result.details.contains("channel utilization unknown"));
        assertFalse(result.value.contains("≈"));
    }

    @Test public void knownCapacityRetainsAggregateAndEstimatedMarker(){
        ServerLoadPresentation result=ServerLoadPresentation.from(sample(30,75.0,true),"nl",1010,true);
        assertEquals(75,result.percent,0);
        assertEquals("Нагрузка сервера · ≈ 75%",result.label());
        assertFalse(result.details.contains("200"));
        assertEquals("Server load · 75%",ServerLoadPresentation.from(sample(30,75.0,false),"nl",1010,false).label());
    }

    @Test public void missingStaleFutureAndWrongCountryNeverShowZeroAsMeasurement(){
        for(ServerLoad source:new ServerLoad[]{null,sample(30,null,false),sample(30,75.0,true)}){
            for(double now:new double[]{1046,984}){
                ServerLoadPresentation result=ServerLoadPresentation.from(source,"nl",now,false);
                assertNull(result.percent);assertEquals("No data",result.value);
            }
            ServerLoadPresentation wrong=ServerLoadPresentation.from(source,"ru",1010,true);
            assertNull(wrong.percent);assertEquals("Нет данных",wrong.value);
        }
    }

    @Test public void zeroAndSaturatedCpuAreValidAndFreshnessBoundaryIsRetained(){
        assertEquals("CPU 0%",ServerLoadPresentation.from(sample(0,null,false),"nl",1045,false).value);
        assertEquals("CPU 100%",ServerLoadPresentation.from(sample(100,null,false),"nl",985,false).value);
    }
}
