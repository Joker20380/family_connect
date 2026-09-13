package com.familyconnect.app;

import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Consumer;
import static com.familyconnect.app.ControlJson.*;

final class ControlVectors {
    static final String MANIFEST="c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd";
    interface Loader {InputStream open(String name)throws Exception;}
    static byte[] load(Loader loader,String name)throws Exception {
        try(InputStream input=loader.open("control-v1/"+name);ByteArrayOutputStream output=new ByteArrayOutputStream()) {
            if(input==null)throw new AssertionError("Missing public fixture: "+name);
            byte[] buffer=new byte[4096];int n;while((n=input.read(buffer))!=-1)output.write(buffer,0,n);return output.toByteArray();
        }
    }
    static void check(boolean ok,String context){if(!ok)throw new AssertionError(context);}
    static String run(Loader loader)throws Exception {
        byte[] manifestBytes=load(loader,"manifest.json");check(ControlProtocol.hash(manifestBytes).equals(MANIFEST),"Corpus revision");
        JsonObject manifest=parse(manifestBytes).getAsJsonObject();check(manifest.get("test_only").getAsBoolean(),"Test corpus only");
        for(Map.Entry<String,JsonElement> file:manifest.getAsJsonObject("files").entrySet()) {
            byte[] raw=load(loader,file.getKey());JsonObject metadata=file.getValue().getAsJsonObject();
            check(raw.length==metadata.get("size").getAsInt()&&ControlProtocol.hash(raw).equals(text(metadata.get("sha256"))),"Corpus integrity: "+file.getKey());
        }
        JsonObject fixture=parse(load(loader,text(manifest.get("fixture_identity")))).getAsJsonObject();
        byte[] anchor=ControlProtocol.base64(text(fixture.get("anchor_b64")),true),privateKey=ControlProtocol.base64(text(fixture.get("rns_private_b64")),true),publicKey=ControlProtocol.base64(text(fixture.get("public_identity_b64")),true);
        int configurations=0,acks=0;
        for(JsonElement item:manifest.getAsJsonArray("configurations")) {
            JsonObject v=item.getAsJsonObject(),expected=v.getAsJsonObject("expected");String category;ControlProtocol.Verified result=null;
            try{result=ControlProtocol.verifyConfiguration(load(loader,text(v.get("input"))),anchor,privateKey,publicKey,text(fixture.get("wireguard_public_key")),text(v.get("client_version")),integer(v.get("now"),Long.MIN_VALUE));category="ACCEPT";}
            catch(ControlProtocol.Rejected e){category=e.category;}
            check(category.equals(text(expected.get("category"))),"Configuration "+text(v.get("id"))+": "+category);
            if(result!=null)check(result.state().equals(expected.get("payload"))&&result.digest.equals(text(expected.get("envelope_sha256"))),"Configuration payload/hash");
            configurations++;
        }
        for(JsonElement item:manifest.getAsJsonArray("acknowledgements")) {
            JsonObject v=item.getAsJsonObject(),expected=v.getAsJsonObject("expected");String category;JsonObject body=null;
            try{body=ControlProtocol.verifyAck(load(loader,text(v.get("input"))));category="ACCEPT";}catch(ControlProtocol.Rejected e){category=e.category;}
            check(category.equals(text(expected.get("category")))&&(body==null||body.equals(expected.get("body"))),"ACK "+text(v.get("id"))+": "+category);acks++;
        }
        JsonObject valid=manifest.getAsJsonArray("configurations").get(0).getAsJsonObject().getAsJsonObject("expected").getAsJsonObject("payload");
        int refusals=structures(valid);
        cryptoRefusals(loader,fixture,anchor,privateKey,publicKey);
        return configurations+" configurations, "+acks+" ACKs, "+refusals+" structure refusals, 4 authenticated-cipher refusals; manifest SHA256 "+MANIFEST;
    }
    static void cryptoRefusals(Loader loader,JsonObject fixture,byte[] anchor,byte[] privateKey,byte[] publicKey)throws Exception {
        JsonObject original=parse(load(loader,"valid-wg.envelope")).getAsJsonObject();
        byte[] validCipher=ControlProtocol.base64(text(original.get("ciphertext")),true);
        for(int mode=0;mode<4;mode++) {
            byte[] cipher=validCipher.clone(),deviceKey=privateKey.clone();
            if(mode==0)cipher[cipher.length-1]^=1;
            if(mode==1)cipher=Arrays.copyOf(cipher,64);
            if(mode==2)Arrays.fill(cipher,0,32,(byte)0);
            if(mode==3)deviceKey[4]^=1;
            // PUBLIC TEST ONLY issuer deliberately authenticates invalid ciphertext.
            org.bouncycastle.crypto.signers.Ed25519Signer signer=new org.bouncycastle.crypto.signers.Ed25519Signer();
            signer.init(true,new org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters(ControlProtocol.base64(text(fixture.get("issuer_private_b64")),true),0));
            byte[] domain=("family-connect/control-config/v1"+"\0").getBytes(StandardCharsets.UTF_8);
            signer.update(domain,0,domain.length);signer.update(cipher,0,cipher.length);
            JsonObject outer=new JsonObject();outer.addProperty("ciphertext",Base64.getEncoder().encodeToString(cipher));outer.addProperty("signature",Base64.getEncoder().encodeToString(signer.generateSignature()));
            try{ControlProtocol.verifyConfiguration(outer.toString().getBytes(StandardCharsets.UTF_8),anchor,deviceKey,publicKey,text(fixture.get("wireguard_public_key")),"0.2.9",1000);}
            catch(ControlProtocol.Rejected e){check(e.category.equals("STRUCTURE"),"Authenticated cipher category");continue;}
            throw new AssertionError("Authenticated invalid ciphertext accepted");
        }
    }
    static void reject(JsonObject valid,Consumer<JsonObject> mutate)throws Exception {
        JsonObject value=valid.deepCopy();mutate.accept(value);
        try{ControlProfiles.validate(value);}catch(Exception e){return;}throw new AssertionError("Invalid schema2 accepted");
    }
    static int structures(JsonObject valid)throws Exception {
        List<Consumer<JsonObject>> mutations=new ArrayList<>();
        for(String field:Arrays.asList("revision","issued_at","expires_at")) {
            mutations.add(v->v.addProperty(field,true));mutations.add(v->v.addProperty(field,0));
        }
        mutations.add(v->v.addProperty("expires_at",1000));mutations.add(v->v.addProperty("expires_at",87401));
        mutations.add(v->v.addProperty("min_client_version","00.2.9"));mutations.add(v->v.addProperty("wireguard_public_key",Base64.getEncoder().encodeToString(new byte[32])));
        mutations.add(v->v.addProperty("previous_config_hash","bad"));mutations.add(v->v.addProperty("extra",1));
        mutations.add(v->v.getAsJsonArray("gateways").add(v.getAsJsonArray("gateways").get(0).deepCopy()));
        mutations.add(v->v.getAsJsonArray("transport_profiles").add(v.getAsJsonArray("transport_profiles").get(0).deepCopy()));
        for(String host:Arrays.asList("127.0.0.1","0.0.0.0","224.0.0.1","::1","::","ff02::1","198.51.100.01","example.com"))mutations.add(v->v.getAsJsonArray("gateways").get(0).getAsJsonObject().addProperty("endpoint",host));
        mutations.add(v->v.getAsJsonArray("gateways").get(0).getAsJsonObject().addProperty("port",true));
        mutations.add(v->profile(v).addProperty("gateway_id","missing"));mutations.add(v->profile(v).addProperty("transport_version","2.0"));
        String p=text(profile(valid).get("config"));
        for(String config:Arrays.asList(p+"PostUp = command\n",p+"PublicKey = duplicate\n",p.replace("LOCAL_DEVICE_KEY",Base64.getEncoder().encodeToString(new byte[32])),p.replace("MTU = 1280","MTU = 1279"),p.replace("0.0.0.0/0, ::/0","0.0.0.0/0"),p.replace(":51820",":51821"),p.replace("10.77.0.4/32","10.77.0.4/33")))mutations.add(v->profile(v).addProperty("config",config));
        for(Consumer<JsonObject> mutation:mutations)reject(valid,mutation);
        return mutations.size();
    }
    private static JsonObject profile(JsonObject value){return value.getAsJsonArray("transport_profiles").get(0).getAsJsonObject();}
    static void jsonRefusals()throws Exception {
        for(String invalid:Arrays.asList("{\"a\":1,\"\\u0061\":2}","{\"a\":[{\"x\":1,\"x\":2}]}","{a:1}","{\"a\":1,}","[1,]","{} {}","//comment\n{}","{\"a\":NaN}","{\"a\":01}")) {
            try{parse(invalid.getBytes(StandardCharsets.UTF_8));}catch(Exception e){continue;}throw new AssertionError("Invalid JSON accepted");
        }
        for(String bad:new String[]{"\""+"\\u"+"d800\"", "\""+"\\u"+"dc00\""}) {
            try{parse(bad.getBytes(StandardCharsets.UTF_8));}catch(Exception e){continue;}throw new AssertionError("Unpaired surrogate accepted");
        }
        try{parse(new byte[]{'{','"',(byte)0xff,'"',':','1','}'});}catch(Exception e){return;}throw new AssertionError("Invalid UTF8 accepted");
    }
}
