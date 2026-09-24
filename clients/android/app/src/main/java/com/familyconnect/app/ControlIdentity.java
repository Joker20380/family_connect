package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters;
import org.bouncycastle.crypto.params.X25519PrivateKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;

/** Independent RNS encryption/signing keys and WG key. Never an imported VPN identity. */
final class ControlIdentity implements AutoCloseable {
    static final int SIZE = 96;
    private byte[] secret;

    private ControlIdentity(byte[] material) {
        if (material.length != SIZE) throw new IllegalArgumentException("Invalid control identity length");
        secret = material.clone();
    }
    static ControlIdentity restore(byte[] material) { return new ControlIdentity(material); }
    static ControlIdentity generate() {
        byte[] material = new byte[SIZE];
        try {
            SecureRandom random = new SecureRandom();
            System.arraycopy(new X25519PrivateKeyParameters(random).getEncoded(), 0, material, 0, 32);
            System.arraycopy(new Ed25519PrivateKeyParameters(random).getEncoded(), 0, material, 32, 32);
            System.arraycopy(new X25519PrivateKeyParameters(random).getEncoded(), 0, material, 64, 32);
            return restore(material);
        } finally { Arrays.fill(material, (byte) 0); }
    }
    private void requireOpen() {
        if (secret == null) throw new IllegalStateException("Control identity closed");
    }
    // Storage boundary only. Caller wipes this copy immediately after encryption.
    synchronized byte[] material() { requireOpen(); return secret.clone(); }
    synchronized byte[] publicIdentity() {
        requireOpen(); byte[] result = new byte[64];
        System.arraycopy(new X25519PrivateKeyParameters(secret, 0).generatePublicKey().getEncoded(), 0, result, 0, 32);
        System.arraycopy(new Ed25519PrivateKeyParameters(secret, 32).generatePublicKey().getEncoded(), 0, result, 32, 32);
        return result;
    }
    // Local profile application only. Caller wipes the returned raw key copy.
    synchronized byte[] wireguardPrivateKey() { requireOpen(); return Arrays.copyOfRange(secret,64,96); }
    synchronized String wireguardPublicKey() {
        requireOpen();
        return Base64.getEncoder().encodeToString(new X25519PrivateKeyParameters(secret, 64).generatePublicKey().getEncoded());
    }
    synchronized String reference() throws Exception { return ControlProtocol.hash(publicIdentity()).substring(0, 32); }
    synchronized JsonObject proveTransportKey(String challenge) throws java.io.IOException {
        requireOpen();
        if (ControlProtocol.base64(challenge, true).length != 32)
            throw new IllegalArgumentException("Invalid enrollment challenge");
        JsonObject binding = new JsonObject();
        binding.addProperty("schema_version", 1);
        binding.addProperty("public_identity", Base64.getEncoder().encodeToString(publicIdentity()));
        binding.addProperty("wireguard_public_key", wireguardPublicKey());
        binding.addProperty("challenge", challenge);
        binding.addProperty("audience", "family-connect/enrollment/v1");
        binding.addProperty("transport", "wireguard");
        Ed25519Signer signer = new Ed25519Signer();
        signer.init(true, new Ed25519PrivateKeyParameters(secret, 32));
        byte[] domain = "family-connect/transport-key-binding/v1\0".getBytes(StandardCharsets.US_ASCII);
        byte[] body = ControlJson.canonical(binding, false);
        signer.update(domain, 0, domain.length); signer.update(body, 0, body.length);
        binding.addProperty("signature", Base64.getEncoder().encodeToString(signer.generateSignature()));
        return binding;
    }
    synchronized JsonObject proveFetch(String challenge)throws java.io.IOException {
        requireOpen();if(ControlProtocol.base64(challenge,true).length!=32)throw new IllegalArgumentException("Invalid fetch challenge");
        JsonObject binding=new JsonObject();binding.addProperty("schema_version",1);binding.addProperty("audience","family-connect/provisioning-fetch/v1");
        binding.addProperty("public_identity",Base64.getEncoder().encodeToString(publicIdentity()));binding.addProperty("wireguard_public_key",wireguardPublicKey());binding.addProperty("challenge",challenge);
        byte[] domain="family-connect/provisioning-fetch/v1\0".getBytes(StandardCharsets.US_ASCII),body=ControlJson.canonical(binding,false);
        Ed25519Signer signer=new Ed25519Signer();signer.init(true,new Ed25519PrivateKeyParameters(secret,32));signer.update(domain,0,domain.length);signer.update(body,0,body.length);
        binding.addProperty("signature",Base64.getEncoder().encodeToString(signer.generateSignature()));return binding;
    }
    synchronized byte[] acknowledgement(String digest, String configId, long sequence,
            String status, String error, long now) throws Exception {
        requireOpen();
        JsonObject body = new JsonObject();
        body.addProperty("schema_version", 1); body.addProperty("device", reference());
        body.addProperty("public_identity", Base64.getEncoder().encodeToString(publicIdentity()));
        body.addProperty("envelope_hash", digest); body.addProperty("config_id", configId);
        body.addProperty("sequence", sequence); body.addProperty("status", status);
        body.addProperty("error", error); body.addProperty("timestamp", now);
        body.addProperty("ack_id", ControlProtocol.hash(ControlJson.canonical(body, false)));
        byte[] canonical = ControlJson.canonical(body, false);
        byte[] domain = (ControlProtocol.ACK+"\0").getBytes(StandardCharsets.US_ASCII);
        Ed25519Signer signer = new Ed25519Signer();
        signer.init(true, new Ed25519PrivateKeyParameters(secret, 32));
        signer.update(domain, 0, domain.length); signer.update(canonical, 0, canonical.length);
        String raw = "{\"body\":"+new String(canonical, StandardCharsets.UTF_8)
            +",\"signature\":\""+Base64.getEncoder().encodeToString(signer.generateSignature())+"\"}";
        byte[] result = raw.getBytes(StandardCharsets.UTF_8);
        ControlProtocol.verifyAck(result); // Refuse invalid status/category/sequence before persistence.
        return result;
    }
    synchronized ControlProtocol.Verified verify(byte[] envelope, byte[] anchor, String version, long now)
            throws ControlProtocol.Rejected {
        return verify(envelope,anchor,version,now,false);
    }
    synchronized ControlProtocol.Verified verify(byte[] envelope, byte[] anchor, String version, long now, boolean supportsAwg31)
            throws ControlProtocol.Rejected {
        requireOpen(); byte[] rns = Arrays.copyOf(secret, 64);
        try { return ControlProtocol.verifyConfiguration(envelope, anchor, rns, publicIdentity(), wireguardPublicKey(), version, now,supportsAwg31); }
        finally { Arrays.fill(rns, (byte) 0); }
    }
    @Override public synchronized void close() {
        if (secret != null) { Arrays.fill(secret, (byte) 0); secret = null; }
    }
}
