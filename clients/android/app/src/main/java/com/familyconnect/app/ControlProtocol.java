package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import org.bouncycastle.crypto.params.*;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.bouncycastle.crypto.generators.HKDFBytesGenerator;
import org.bouncycastle.crypto.digests.SHA256Digest;
import static com.familyconnect.app.ControlJson.*;

/** Verification only: no carrier, storage, revision acceptance, or VPN mutations. */
final class ControlProtocol {
    static final String CONFIG="family-connect/control-config/v1", ACK="family-connect/control-ack/v1";
    static final class Rejected extends Exception {
        final String category;Rejected(String category){super(category);this.category=category;}
    }
    static final class Verified {
        private final JsonObject state;final String digest;
        Verified(JsonObject state,String digest){this.state=state.deepCopy();this.digest=digest;}
        JsonObject state(){return state.deepCopy();}
    }
    static byte[] base64(String value,boolean canonical) {
        require(value.matches("[A-Za-z0-9+/]*={0,2}") && value.length()%4==0);
        byte[] bytes=Base64.getDecoder().decode(value);
        if(canonical)require(Base64.getEncoder().encodeToString(bytes).equals(value));return bytes;
    }
    static byte[] sha(byte[] value)throws GeneralSecurityException{return MessageDigest.getInstance("SHA-256").digest(value);}
    static String hash(byte[] value)throws GeneralSecurityException {
        StringBuilder result=new StringBuilder();for(byte b:sha(value))result.append(String.format(Locale.ROOT,"%02x",b&255));return result.toString();
    }
    private static boolean signature(byte[] key,byte[] sig,String purpose,byte[] value) {
        if(key.length!=32 || sig.length!=64)return false;
        Ed25519Signer verifier=new Ed25519Signer();verifier.init(false,new Ed25519PublicKeyParameters(key,0));
        byte[] domain=(purpose+"\0").getBytes(StandardCharsets.UTF_8);
        verifier.update(domain,0,domain.length);verifier.update(value,0,value.length);return verifier.verifySignature(sig);
    }
    static JsonObject verifyAck(byte[] raw)throws Rejected {
        try {
            require(raw.length<=4096);JsonElement outerValue=parse(raw);fields(outerValue,"body signature");JsonObject outer=outerValue.getAsJsonObject();
            JsonElement bodyValue=outer.get("body");fields(bodyValue,"schema_version device public_identity envelope_hash config_id sequence status error timestamp ack_id");JsonObject body=bodyValue.getAsJsonObject();
            require(integer(body.get("schema_version"),0)==1);integer(body.get("sequence"),0);integer(body.get("timestamp"),0);
            require(Arrays.asList("RECEIVED REJECTED APPLIED COMMITTED ROLLED_BACK FAILED".split(" ")).contains(text(body.get("status"))));
            require(Arrays.asList("NONE SIZE CLOCK SIGNATURE MALFORMED SCHEMA TARGET SIGNER STRUCTURE LEASE CLIENT_VERSION UNSUPPORTED_TRANSPORT_VERSION REPLAY PREVIOUS_HASH APPLY HEALTH RECOVERY ROLLBACK".split(" ")).contains(text(body.get("error"))));
            require(text(body.get("envelope_hash")).matches("[0-9a-f]{64}") && text(body.get("ack_id")).matches("[0-9a-f]{64}"));
            require(body.get("config_id").isJsonNull() || text(body.get("config_id")).matches("[a-zA-Z0-9_-]{1,64}"));
            byte[] key=base64(text(body.get("public_identity")),true);require(key.length==64);
            require(hash(key).substring(0,32).equals(text(body.get("device"))));
            require(signature(Arrays.copyOfRange(key,32,64),base64(text(outer.get("signature")),false),ACK,canonical(body,false)));
            require(hash(canonical(body,true)).equals(text(body.get("ack_id"))));return body.deepCopy();
        } catch(Exception e){throw new Rejected("REJECT");}
    }
    private static byte[] decrypt(byte[] cipher,byte[] privateKey,byte[] publicIdentity)throws Exception {
        require(privateKey.length==64 && publicIdentity.length==64 && cipher.length>=96);
        byte[] shared=new byte[32],derived=new byte[64];
        try {
            new X25519PrivateKeyParameters(privateKey,0).generateSecret(new X25519PublicKeyParameters(cipher,0),shared,0);
            HKDFBytesGenerator hkdf=new HKDFBytesGenerator(new SHA256Digest());
            hkdf.init(new HKDFParameters(shared,Arrays.copyOf(sha(publicIdentity),16),null));hkdf.generateBytes(derived,0,64);
            Mac mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(Arrays.copyOf(derived,32),"HmacSHA256"));
            mac.update(cipher,32,cipher.length-64);require(MessageDigest.isEqual(mac.doFinal(),Arrays.copyOfRange(cipher,cipher.length-32,cipher.length)));
            Cipher aes=Cipher.getInstance("AES/CBC/PKCS5Padding");
            aes.init(Cipher.DECRYPT_MODE,new SecretKeySpec(Arrays.copyOfRange(derived,32,64),"AES"),new IvParameterSpec(cipher,32,16));
            return aes.doFinal(cipher,48,cipher.length-80);
        } finally {Arrays.fill(shared,(byte)0);Arrays.fill(derived,(byte)0);}
    }
    static int[] version(String value) {
        require(value.matches("(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,5})\\.(0|[1-9][0-9]{0,5})"));
        String[] parts=value.split("\\.");return new int[]{Integer.parseInt(parts[0]),Integer.parseInt(parts[1]),Integer.parseInt(parts[2])};
    }
    private static boolean equalsString(JsonElement value,String expected){return value!=null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isString() && value.getAsString().equals(expected);}
    static Verified verifyConfiguration(byte[] raw,byte[] anchor,byte[] rnsPrivate,byte[] publicIdentity,String wgPublic,String clientVersion,long now)throws Rejected {
        if(now<0)throw new Rejected("CLOCK");if(raw==null || raw.length>65536)throw new Rejected("SIZE");byte[] cipher;
        try {
            JsonElement value=parse(raw);fields(value,"ciphertext signature");JsonObject outer=value.getAsJsonObject();cipher=base64(text(outer.get("ciphertext")),false);
            if(!signature(anchor,base64(text(outer.get("signature")),false),CONFIG,cipher))throw new Rejected("SIGNATURE");
        }catch(Rejected e){throw e;}catch(Exception e){throw new Rejected("MALFORMED");}
        JsonObject state;
        try {
            byte[] plain=decrypt(cipher,rnsPrivate,publicIdentity);JsonElement value;
            try{value=parse(plain);}finally{Arrays.fill(plain,(byte)0);}
            require(value.isJsonObject());state=value.getAsJsonObject();JsonElement schema=state.get("schema_version");
            if(schema==null || !schema.isJsonPrimitive() || !schema.getAsJsonPrimitive().isNumber() || !schema.getAsString().equals("2"))throw new Rejected("SCHEMA");
            if(!equalsString(state.get("audience"),CONFIG) || !equalsString(state.get("recipient"),hash(publicIdentity).substring(0,32)))throw new Rejected("TARGET");
            if(!equalsString(state.get("signer_key_id"),hash(anchor)))throw new Rejected("SIGNER");
            JsonElement profiles=state.get("transport_profiles");
            if(profiles!=null && profiles.isJsonArray())for(JsonElement p:profiles.getAsJsonArray())
                if(p.isJsonObject() && equalsString(p.getAsJsonObject().get("transport"),"amneziawg") && equalsString(p.getAsJsonObject().get("transport_version"),"3.1"))throw new Rejected("UNSUPPORTED_TRANSPORT_VERSION");
            ControlProfiles.validate(state);
        }catch(Rejected e){throw e;}catch(Exception e){throw new Rejected("STRUCTURE");}
        try {
            if(!text(state.get("wireguard_public_key")).equals(wgPublic))throw new Rejected("TARGET");
            if(now<integer(state.get("issued_at"),1) || now>=integer(state.get("expires_at"),1))throw new Rejected("LEASE");
            int[] minimum=version(text(state.get("min_client_version"))),client=version(clientVersion);
            for(int n=0;n<3;n++){if(minimum[n]>client[n])throw new Rejected("CLIENT_VERSION");if(minimum[n]<client[n])break;}
            return new Verified(state,hash(raw));
        }catch(Rejected e){throw e;}catch(Exception e){throw new Rejected("STRUCTURE");}
    }
}
