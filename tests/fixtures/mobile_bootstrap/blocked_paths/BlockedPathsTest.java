package com.familyconnect.app;

import android.content.Context;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.SocketTimeoutException;
import java.net.URL;
import java.net.URLConnection;
import java.net.URLStreamHandler;
import java.security.Key;
import java.security.KeyStoreSpi;
import java.security.Provider;
import java.security.Security;
import java.security.cert.Certificate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.Enumeration;
import java.util.List;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

public final class BlockedPathsTest {
    private static final List<String> requests = new ArrayList<>();
    private final Context context = new Context(new java.io.File(System.getProperty("fixture.state")));

    public static final class EmptyKeyStore extends KeyStoreSpi {
        public Key engineGetKey(String alias, char[] password) { return null; }
        public Certificate[] engineGetCertificateChain(String alias) { return null; }
        public Certificate engineGetCertificate(String alias) { return null; }
        public Date engineGetCreationDate(String alias) { return null; }
        public void engineSetKeyEntry(String alias, Key key, char[] password, Certificate[] chain) { throw new AssertionError(); }
        public void engineSetKeyEntry(String alias, byte[] key, Certificate[] chain) { throw new AssertionError(); }
        public void engineSetCertificateEntry(String alias, Certificate certificate) { throw new AssertionError(); }
        public void engineDeleteEntry(String alias) { throw new AssertionError(); }
        public Enumeration<String> engineAliases() { return Collections.emptyEnumeration(); }
        public boolean engineContainsAlias(String alias) { return alias.equals("family-connect-friends-identity-v1") && FriendsIdentityVault.saved != null; }
        public int engineSize() { return 0; }
        public boolean engineIsKeyEntry(String alias) { return false; }
        public boolean engineIsCertificateEntry(String alias) { return false; }
        public String engineGetCertificateAlias(Certificate certificate) { return null; }
        public void engineStore(OutputStream output, char[] password) { throw new AssertionError(); }
        public void engineLoad(InputStream input, char[] password) {}
    }

    @BeforeClass public static void blockAllHttpsInProcess() {
        Provider provider = new Provider("SyntheticAndroidVault", "1", "Memory only") {};
        provider.put("KeyStore.AndroidKeyStore", EmptyKeyStore.class.getName());
        Security.addProvider(provider);
        URL.setURLStreamHandlerFactory(protocol -> {
            if (protocol.equals("file") || protocol.equals("jar")) return null;
            return new URLStreamHandler() {
                protected URLConnection openConnection(URL address) {
                    if (!protocol.equals("https")) throw new AssertionError("Unexpected network connection");
                    requests.add(address.getPath());
                    return new javax.net.ssl.HttpsURLConnection(address) {
                        public OutputStream getOutputStream() throws SocketTimeoutException { throw new SocketTimeoutException("Synthetic blocked HTTPS"); }
                        public void disconnect() {}
                        public void connect() { throw new AssertionError(); }
                        public boolean usingProxy() { return false; }
                        public String getCipherSuite() { throw new AssertionError(); }
                        public Certificate[] getLocalCertificates() { throw new AssertionError(); }
                        public Certificate[] getServerCertificates() { throw new AssertionError(); }
                    };
                }
            };
        });
    }

    @Before public void reset() {
        requests.clear();
        ControlRnsAndroid.opens = 0;
        NativeRestricted.acquisitions = 0;
        FriendsIdentityVault.reset();
    }

    private RestrictedBootstrap.Selection refresh(RestrictedCache cache, long now) throws Exception {
        ReadinessProduct product = new ReadinessProduct(cache, new ReadinessProductTest.Memory(), "test", 113, () -> now);
        OwnerPrewarmReceipt receipt = new OwnerPrewarmReceipt();
        try (ControlIdentity identity = ControlIdentity.generate()) {
            FriendsAccessAndroid client = new FriendsAccessAndroid(context, android.os.SystemClock.elapsedRealtime() + 30000);
            RestrictedBootstrap.Selection selected = RestrictedBootstrap.refresh(cache, product, receipt,
                () -> client.restrictedReadiness(identity, receipt), this, () -> now);
            assertEquals(List.of("/friends/restricted-readiness/challenge"), requests);
            assertEquals(1, ControlRnsAndroid.opens);
            assertEquals(ReadinessImportResult.Code.FETCH_FAILED, selected.result.code());
            assertTrue(selected.availabilityFailure);
            assertFalse(selected.authorizationRejected);
            return selected;
        }
    }

    @Test public void activatedWithoutReadinessCannotReachMesh() throws Exception {
        RestrictedCache cache = RestrictedCache.detailed(new ReadinessProductTest.Memory(), raw -> { throw new AssertionError("Missing material"); });
        RestrictedBootstrap.Selection selected = refresh(cache, 1500);
        assertNull(selected.response);
        try {
            RestrictedBootstrap.select(selected.response, selected.availabilityFailure, false);
            fail();
        } catch (ConnectivityOrchestrator.Rejected expected) {
            assertEquals(ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE, expected.category);
            assertTrue(expected.temporaryBootstrap);
        }
    }

    @Test public void validatedCacheCanBeSelectedForFreshConnectButNotRecovery() throws Exception {
        byte[] saved = ReadinessProductTest.response(1000, 2000);
        RestrictedCache cache = RestrictedCache.detailed(new ReadinessProductTest.Memory(), raw -> ReadinessImportResult.Code.READY);
        cache.importProduct(saved, new OwnerPrewarmReceipt(), 1500);
        RestrictedBootstrap.Selection selected = refresh(cache, 1500);
        assertArrayEquals(saved, RestrictedBootstrap.select(selected.response, selected.availabilityFailure, false));
        assertEquals("CACHED_VALID_REFRESH_UNAVAILABLE", selected.status);
        try {
            RestrictedBootstrap.select(selected.response, selected.availabilityFailure, true);
            fail();
        } catch (ConnectivityOrchestrator.Rejected expected) {
            assertEquals(ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE, expected.category);
        }
    }

    @Test public void expiredCacheDoesNotRescueBlockedFetch() throws Exception {
        RestrictedCache cache = RestrictedCache.detailed(new ReadinessProductTest.Memory(), raw -> ReadinessImportResult.Code.READY);
        cache.importProduct(ReadinessProductTest.response(1000, 2000), new OwnerPrewarmReceipt(), 1500);
        assertNull(refresh(cache, 2000).response);
    }

    @Test public void freshActivationCannotUseReadinessRelay() throws Exception {
        try {
            new FriendsAccessAndroid(context).activate("SYNTHETIC_INVITATION");
            fail();
        } catch (SocketTimeoutException expected) {
            assertEquals(List.of("/friends/challenge"), requests);
            assertEquals(1, FriendsIdentityVault.creates);
            assertEquals(0, ControlRnsAndroid.opens);
        }
    }

    @Test public void freshRegistrationCannotSkipChallenge() throws Exception {
        try {
            new FriendsAccessAndroid(context).register("");
            fail();
        } catch (SocketTimeoutException expected) {
            assertEquals(List.of("/friends/challenge"), requests);
            assertEquals(1, FriendsIdentityVault.creates);
            assertEquals(0, ControlRnsAndroid.opens);
        }
    }

    @Test public void invitationRegistrationStopsAtClaim() throws Exception {
        try {
            new FriendsAccessAndroid(context).register("0".repeat(64));
            fail();
        } catch (SocketTimeoutException expected) {
            assertEquals(List.of("/friends/referral/claim"), requests);
            assertEquals(1, FriendsIdentityVault.creates);
            assertEquals(0, ControlRnsAndroid.opens);
        }
    }

    @Test public void serviceOnlyChatIsNotAnUncachedProvisioningRoute() throws Exception {
        try (ControlIdentity identity = new FriendsIdentityVault(context).create(); ChatCarrier carrier = new ChatCarrier(context)) {
            assertEquals(-1, carrier.openMailbox(100));
            assertEquals(0, NativeRestricted.acquisitions);
            assertTrue(requests.isEmpty());
            assertEquals(0, ControlRnsAndroid.opens);
        }
    }
}
