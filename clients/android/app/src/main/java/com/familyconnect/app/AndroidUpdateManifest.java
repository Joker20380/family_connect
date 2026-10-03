package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;

final class AndroidUpdateManifest {
    static final String ANCHOR="0NdiJ/7kjveUMEEFNr7or8tMZNQHHzNq4rrfzp6/6i0=";
    static final String SIGNER="67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a";
    static final byte[] DOMAIN="family-connect/android-update/v1\0".getBytes(StandardCharsets.UTF_8);
    final AppUpdate update;
    final long sequence,minimum,mandatoryAfter;
    final String digest;
    private AndroidUpdateManifest(AppUpdate update,long sequence,long minimum,long mandatoryAfter,String digest){
        this.update=update;this.sequence=sequence;this.minimum=minimum;this.mandatoryAfter=mandatoryAfter;this.digest=digest;
    }
    static AndroidUpdateManifest verify(byte[] raw,long now,long floor,String previous)throws Exception{
        return verify(raw,now,floor,previous,Base64.getDecoder().decode(ANCHOR));
    }
    static AndroidUpdateManifest verify(byte[] raw,long now,long floor,String previous,byte[] anchor)throws Exception{
        if(raw.length==0||raw.length>16384)throw new SecurityException("Manifest size");
        JsonObject envelope=JsonParser.parseString(new String(raw,StandardCharsets.UTF_8)).getAsJsonObject();
        byte[] payload=Base64.getDecoder().decode(envelope.get("payload").getAsString());
        byte[] signature=Base64.getDecoder().decode(envelope.get("signature").getAsString());
        Ed25519Signer verifier=new Ed25519Signer();verifier.init(false,new Ed25519PublicKeyParameters(anchor,0));
        verifier.update(DOMAIN,0,DOMAIN.length);verifier.update(payload,0,payload.length);
        if(!verifier.verifySignature(signature))throw new SecurityException("Manifest signature");
        AppUpdate update=AppUpdate.parse(payload);
        JsonObject data=JsonParser.parseString(new String(payload,StandardCharsets.UTF_8)).getAsJsonObject();
        long sequence=number(data,"sequence"),issued=number(data,"issued_at"),expires=number(data,"expires_at");
        long minimum=number(data,"minimum_supported_version"),mandatory=number(data,"mandatory_after");
        String digest=AppUpdate.hex(MessageDigest.getInstance("SHA-256").digest(payload));
        if(!"android-field".equals(data.get("channel").getAsString())||!SIGNER.equals(data.get("signer_fingerprint").getAsString())
            ||sequence<1||sequence<floor||(sequence==floor&&!digest.equals(previous))||issued>now+300||expires<=now||expires<=issued
            ||expires-issued>90*86400L||minimum<1||minimum>update.code||(mandatory!=0&&(mandatory<issued||mandatory>=expires)))
            throw new SecurityException("Manifest policy");
        return new AndroidUpdateManifest(update,sequence,minimum,mandatory,digest);
    }
    private static long number(JsonObject data,String name){
        JsonPrimitive value=data.getAsJsonPrimitive(name);
        if(!value.isNumber()||!value.getAsString().matches("[0-9]{1,15}"))throw new SecurityException("Manifest number");
        return value.getAsLong();
    }
    boolean required(long installed,long now){return installed<minimum&&mandatoryAfter>0&&now>=mandatoryAfter;}
}
