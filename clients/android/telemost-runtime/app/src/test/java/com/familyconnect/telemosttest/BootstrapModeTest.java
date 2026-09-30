package com.familyconnect.telemosttest;

import org.junit.Test;
import java.nio.charset.StandardCharsets;
import static org.junit.Assert.*;

public final class BootstrapModeTest {
    @Test public void absentKeepsExistingDiagnosticPath() {
        assertEquals("", BootstrapMode.parse(null, ""));
    }

    @Test public void prepareAndGuardedRecover() {
        assertEquals("refresh", BootstrapMode.parse("refresh\n".getBytes(StandardCharsets.UTF_8), "https://192.0.2.1:18444"));
        assertEquals("recover", BootstrapMode.parse("recover".getBytes(StandardCharsets.UTF_8), "https://127.0.0.1:1"));
    }

    @Test public void invalidAndUnguardedRejected() {
        for (String mode : new String[]{"", "automatic", "https://example.org", "recover"}) {
            assertThrows(IllegalArgumentException.class, () -> BootstrapMode.parse(mode.getBytes(StandardCharsets.UTF_8), "https://192.0.2.1:18444"));
        }
        assertThrows(IllegalArgumentException.class, () -> BootstrapMode.parse(new byte[17], "https://127.0.0.1:1"));
        assertThrows(IllegalArgumentException.class, () -> BootstrapMode.parse("refresh".getBytes(StandardCharsets.UTF_8), ""));
    }
}
