package com.familyconnect.app;

import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.Base64;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

public class ControlIdentityTest {
    private byte[] resource(String name) throws Exception {
        try (var input = getClass().getClassLoader().getResourceAsStream("control-v1/"+name)) {
            return input.readAllBytes();
        }
    }
    private ControlIdentity fixture() throws Exception {
        JsonObject fixture = ControlJson.parse(resource("TEST-ONLY-identity.json")).getAsJsonObject();
        byte[] material = new byte[ControlIdentity.SIZE];
        System.arraycopy(ControlProtocol.base64(fixture.get("rns_private_b64").getAsString(), true), 0, material, 0, 64);
        System.arraycopy(ControlProtocol.base64(fixture.get("wg_private_b64").getAsString(), true), 0, material, 64, 32);
        try { return ControlIdentity.restore(material); } finally { Arrays.fill(material, (byte) 0); }
    }
    private static SecretKey key() throws Exception { KeyGenerator g = KeyGenerator.getInstance("AES"); g.init(256); return g.generateKey(); }
    @Test public void referenceIdentityAndConfiguration() throws Exception {
        JsonObject f = ControlJson.parse(resource("TEST-ONLY-identity.json")).getAsJsonObject();
        try (ControlIdentity identity = fixture()) {
            assertEquals(f.get("device_reference").getAsString(), identity.reference());
            assertEquals(f.get("public_identity_b64").getAsString(), Base64.getEncoder().encodeToString(identity.publicIdentity()));
            assertEquals(f.get("wireguard_public_key").getAsString(), identity.wireguardPublicKey());
            var manifest = ControlJson.parse(resource("manifest.json")).getAsJsonObject();
            var v = manifest.getAsJsonArray("configurations").get(0).getAsJsonObject();
            var verified = identity.verify(resource(v.get("input").getAsString()), ControlProtocol.base64(f.get("anchor_b64").getAsString(), true), v.get("client_version").getAsString(), v.get("now").getAsLong());
            assertEquals(v.getAsJsonObject("expected").get("envelope_sha256").getAsString(), verified.digest);
        }
    }
    @Test public void enrollmentProofMatchesPythonFixture() throws Exception {
        try (ControlIdentity identity = fixture()) {
            String challenge = Base64.getEncoder().encodeToString(new byte[32]);
            JsonObject expected = ControlJson.parse(resource("../control-identity-v1/identity-binding-proof.json")).getAsJsonObject();
            assertEquals(expected, identity.proveTransportKey(challenge));
            assertThrows(IllegalArgumentException.class, () -> identity.proveTransportKey("AAAA"));
            assertThrows(IllegalArgumentException.class, () -> identity.proveTransportKey(challenge+"\n"));
        }
    }
    @Test public void independentKeysSurviveEncryptedRoundTrip() throws Exception {
        try (ControlIdentity first = ControlIdentity.generate(); ControlIdentity other = ControlIdentity.generate()) {
            assertNotEquals(first.reference(), other.reference());
            assertFalse(Arrays.equals(Arrays.copyOf(first.publicIdentity(), 32), Base64.getDecoder().decode(first.wireguardPublicKey())));
            byte[] material = first.material(); SecretKey wrapping = key();
            byte[] sealed = ControlIdentityEnvelope.seal(wrapping, material);
            assertEquals(ControlIdentityEnvelope.SIZE, sealed.length);
            assertFalse(Arrays.equals(sealed, ControlIdentityEnvelope.seal(wrapping, material)));
            byte[] plain = ControlIdentityEnvelope.open(wrapping, sealed);
            try (ControlIdentity restored = ControlIdentity.restore(plain)) {
                Arrays.fill(plain, (byte) 0); Arrays.fill(material, (byte) 0);
                assertEquals(first.reference(), restored.reference());
                assertEquals(first.wireguardPublicKey(), restored.wireguardPublicKey());
            }
        }
    }
    @Test public void corruptionWrongKeyAndSizeFailClosed() throws Exception {
        SecretKey wrapping = key(); byte[] raw = ControlIdentityEnvelope.seal(wrapping, new byte[ControlIdentity.SIZE]);
        for (int position = 0; position < raw.length; position++) {
            byte[] corrupt = raw.clone(); corrupt[position] ^= 1;
            assertThrows(java.security.GeneralSecurityException.class, () -> ControlIdentityEnvelope.open(wrapping, corrupt));
        }
        assertThrows(java.security.GeneralSecurityException.class, () -> ControlIdentityEnvelope.open(key(), raw));
        for (int size : new int[] {0, 61, raw.length-1, raw.length+1}) {
            byte[] wrong = Arrays.copyOf(raw, size);
            assertThrows(java.security.GeneralSecurityException.class, () -> ControlIdentityEnvelope.open(wrapping, wrong));
        }
        assertThrows(java.security.GeneralSecurityException.class, () -> ControlIdentityEnvelope.seal(wrapping, new byte[32]));
        assertThrows(IllegalArgumentException.class, () -> ControlIdentity.restore(new byte[64]));
    }
    @Test public void domainSeparationRejectsSameLengthForeignEnvelope() throws Exception {
        SecretKey wrapping = key();
        javax.crypto.Cipher cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(javax.crypto.Cipher.ENCRYPT_MODE, wrapping);
        cipher.updateAAD("family-connect/chat-store-key/v1".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
        byte[] raw = new byte[ControlIdentityEnvelope.SIZE]; raw[0] = 1;
        System.arraycopy(cipher.getIV(), 0, raw, 1, 12);
        byte[] encrypted = cipher.doFinal(new byte[ControlIdentity.SIZE]);
        System.arraycopy(encrypted, 0, raw, 13, encrypted.length);
        assertThrows(java.security.GeneralSecurityException.class, () -> ControlIdentityEnvelope.open(wrapping, raw));
    }
    @Test public void closedIdentityCannotBeReused() throws Exception {
        ControlIdentity identity = ControlIdentity.generate(); identity.close(); identity.close();
        assertThrows(IllegalStateException.class, identity::material);
        assertThrows(IllegalStateException.class, identity::publicIdentity);
        assertThrows(IllegalStateException.class, identity::wireguardPublicKey);
        assertThrows(IllegalStateException.class, () -> identity.proveTransportKey(Base64.getEncoder().encodeToString(new byte[32])));
    }
}
