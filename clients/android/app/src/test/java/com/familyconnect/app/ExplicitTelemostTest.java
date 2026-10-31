package com.familyconnect.app;
import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;
public class ExplicitTelemostTest {
    @Test public void explicitSelectionRetainsRestrictedOrchestrator(){assertEquals(List.of("restricted"),ConnectivityOrchestrator.order(List.of(),"awg","tcp"));}
}
