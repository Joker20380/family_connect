package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.junit.Test;
import static org.junit.Assert.*;

public class AndroidUpdateManifestTest {
    private final Ed25519PrivateKeyParameters key=new Ed25519PrivateKeyParameters(new java.security.SecureRandom());
    private JsonObject payload(){
        JsonObject data=new JsonObject();data.addProperty("schema",1);data.addProperty("channel","android-field");data.addProperty("sequence",2);
        data.addProperty("package","com.familyconnect.app.friends");data.addProperty("abi","arm64-v8a");data.addProperty("version","0.1.18-beta59");data.addProperty("version_code",59);
        data.addProperty("size",2048);data.addProperty("sha256","0".repeat(64));data.addProperty("url",AppUpdate.BASE+"/downloads/FamilyConnect-Test-0.1.18-beta59.apk");
        data.addProperty("signer_fingerprint",AndroidUpdateManifest.SIGNER);data.addProperty("minimum_supported_version",1);data.addProperty("mandatory_after",0);
        data.addProperty("issued_at",1000);data.addProperty("expires_at",2000);return data;
    }
    private byte[] signed(JsonObject data){
        byte[] payload=data.toString().getBytes(StandardCharsets.UTF_8);Ed25519Signer signer=new Ed25519Signer();signer.init(true,key);
        signer.update(AndroidUpdateManifest.DOMAIN,0,AndroidUpdateManifest.DOMAIN.length);signer.update(payload,0,payload.length);
        JsonObject envelope=new JsonObject();envelope.addProperty("payload",Base64.getEncoder().encodeToString(payload));envelope.addProperty("signature",Base64.getEncoder().encodeToString(signer.generateSignature()));return envelope.toString().getBytes(StandardCharsets.UTF_8);
    }
    private AndroidUpdateManifest verify(byte[] raw,long floor,String hash)throws Exception{return AndroidUpdateManifest.verify(raw,1500,floor,hash,key.generatePublicKey().getEncoded());}
    @Test public void verifiesSignatureFloorLeaseAndOptionalPolicy()throws Exception{
        byte[] raw=signed(payload());AndroidUpdateManifest manifest=verify(raw,0,"");assertEquals(59,manifest.update.code);assertFalse(manifest.required(51,1500));
        assertEquals(2,verify(raw,2,manifest.digest).sequence);
        for(long floor:new long[]{2,3})try{verify(raw,floor,"");fail();}catch(SecurityException expected){}
        try{AndroidUpdateManifest.verify(raw,1500,0,"");fail();}catch(SecurityException expected){}
        try{verify(payload().toString().getBytes(StandardCharsets.UTF_8),0,"");fail();}catch(Exception expected){}
    }
    @Test public void rejectsSignedWrongIdentityExpiredAndMalformedPolicy()throws Exception{
        for(String field:new String[]{"signer_fingerprint","channel","package","url"}){JsonObject data=payload();data.addProperty(field,"foreign");try{verify(signed(data),0,"");fail(field);}catch(RuntimeException expected){}}
        for(String field:new String[]{"expires_at","issued_at","minimum_supported_version","mandatory_after"}){JsonObject data=payload();data.addProperty(field,field.equals("expires_at")?1500:9000);try{verify(signed(data),0,"");fail(field);}catch(SecurityException expected){}}
    }
    @Test public void mandatoryNoticeDoesNotApplyBeforeGraceDeadline()throws Exception{
        JsonObject data=payload();data.addProperty("minimum_supported_version",59);data.addProperty("mandatory_after",1600);
        AndroidUpdateManifest manifest=verify(signed(data),0,"");assertFalse(manifest.required(51,1599));assertTrue(manifest.required(51,1600));assertFalse(manifest.required(59,1600));
    }
}
