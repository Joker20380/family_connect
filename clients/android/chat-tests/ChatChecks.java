package com.familyconnect.app;
import java.util.*;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

public final class ChatChecks {
    private static void check(boolean valid){if(!valid)throw new AssertionError();}
    public static void main(String[] args) throws Exception {
        KeyGenerator generator=KeyGenerator.getInstance("AES");generator.init(256);
        SecretKey wrapping=generator.generateKey();byte[] key=new byte[32];new java.security.SecureRandom().nextBytes(key);
        byte[] encrypted=ChatKeyEnvelope.seal(wrapping,key);
        check(encrypted.length==61);check(Arrays.equals(key,ChatKeyEnvelope.open(wrapping,encrypted)));
        check(!Arrays.equals(encrypted,ChatKeyEnvelope.seal(wrapping,key)));
        for(int i=0;i<encrypted.length;i++) {
            byte[] altered=encrypted.clone();altered[i]^=1;
            try{ChatKeyEnvelope.open(wrapping,altered);throw new AssertionError("Tamper accepted");}
            catch(GeneralSecurityException expected){}
        }
        try{ChatKeyEnvelope.open(generator.generateKey(),encrypted);throw new AssertionError();}
        catch(GeneralSecurityException expected){}
        for(int size:new int[]{0,13,60,62,200}) {
            try{ChatKeyEnvelope.open(wrapping,new byte[size]);throw new AssertionError();}
            catch(GeneralSecurityException expected){}
        }
        check(ChatSmileys.FACES.size()==8);
        for(int i=0;i<8;i++) {
            String token=ChatSmileys.FACES.get(i).token;
            check(token.getBytes(StandardCharsets.UTF_8).length<=3);
            List<ChatSmileys.Match> found=ChatSmileys.find("Привет "+token+" друг");
            check(found.size()==1&&found.get(0).index==i);
            check(("Привет "+token+" друг").substring(found.get(0).start,found.get(0).end).equals(token));
        }
        check(ChatSmileys.find("https://host/:) word:) :)word B)ook").isEmpty());
        check(ChatSmileys.find(":) :D\n;) 😀").size()==3);
        check(ChatSmileys.find("😀 :) привет").get(0).start==3);
        check(ChatSmileys.find(":unknown: <3").isEmpty());
        System.out.println("PASS: roundtrip, random nonce, 61 tamper positions, wrong key, bounds, 8 smileys, UTF-16 offsets, URL boundaries, fallback");
    }
}
