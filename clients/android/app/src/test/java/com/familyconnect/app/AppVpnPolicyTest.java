package com.familyconnect.app;

import org.junit.Test;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import static org.junit.Assert.*;

public class AppVpnPolicyTest {
    @Test public void migrationIsAllWithoutExceptions(){
        AppVpnPolicy policy=AppVpnPolicy.all();policy.requireConnectable();
        assertEquals(AppVpnPolicy.Mode.ALL,policy.mode);assertTrue(policy.selected().isEmpty());
        assertTrue(policy.included.isEmpty());assertTrue(policy.excluded.isEmpty());
    }
    @Test public void immutableSelectionAndIndependentLists(){
        ArrayList<String> names=new ArrayList<>(List.of("com.example.alpha"));
        AppVpnPolicy policy=new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,names,Set.of("com.example.beta"));names.clear();
        assertEquals(Set.of("com.example.alpha"),policy.selected());assertEquals(Set.of("com.example.beta"),policy.excluded);
        assertThrows(UnsupportedOperationException.class,()->policy.included.clear());
    }
    @Test public void emptyIncludeNeverMeansAll(){
        AppVpnPolicy policy=new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,Set.of(),Set.of("com.example.beta"));
        assertThrows(IllegalArgumentException.class,policy::requireConnectable);
    }
    @Test public void emptyExcludeStillHasExplicitMode(){
        AppVpnPolicy policy=new AppVpnPolicy(AppVpnPolicy.Mode.EXCLUDE,Set.of("com.example.alpha"),Set.of());policy.requireConnectable();
        assertTrue(policy.selected().isEmpty());assertNotEquals(AppVpnPolicy.all(),policy);
    }
    @Test public void duplicateNamesAreOneRule(){
        assertEquals(1,new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,List.of("android","android"),Set.of()).selected().size());
    }
    @Test public void invalidNamesAreNotUidOrProfileSelectors(){
        for(String name:List.of("", "12345", "com.example/app", "com.example\nother", "com..example", "10:com.example", "com.example;all"))
            assertThrows(IllegalArgumentException.class,()->new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,List.of(name),Set.of()));
    }
    @Test public void inactiveListSurvivesModeChange(){
        AppVpnPolicy saved=new AppVpnPolicy(AppVpnPolicy.Mode.EXCLUDE,Set.of("com.example.alpha"),Set.of("com.example.beta"));
        AppVpnPolicy active=new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,saved.included,saved.excluded);
        assertEquals(Set.of("com.example.alpha"),active.selected());assertNotEquals(saved,active);
    }
}
