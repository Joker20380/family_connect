package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.*;
import java.util.function.BooleanSupplier;
import static com.familyconnect.app.ControlJson.*;

/** Explicit signed-envelope intake. File bytes are never treated as a plaintext native profile. */
final class ControlIntake {
    static final int LIMIT=65536;
    static byte[] copy(byte[] raw)throws IOException {
        if(raw==null||raw.length==0||raw.length>LIMIT)throw new IOException("Invalid control envelope size");return raw.clone();
    }
    static byte[] read(InputStream input)throws IOException {
        if(input==null)throw new IOException("Missing control envelope");
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int n;
        while((n=input.read(buffer))!=-1){
            if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Control intake cancelled");
            if(n==0)throw new IOException("Control input made no progress");
            if(bytes.size()+n>LIMIT)throw new IOException("Control envelope too large");bytes.write(buffer,0,n);
        }
        return copy(bytes.toByteArray());
    }
    static String apply(ControlTransaction core,ControlIdentity identity,JsonObject enrollment,
                        byte[] envelope,BooleanSupplier connected)throws Exception {
        byte[] raw=copy(envelope);
        fields(enrollment,"schema origin phase device proof");require(integer(enrollment.get("schema"),1)==1);
        require("ENROLLED".equals(text(enrollment.get("phase")))&&enrollment.get("proof").isJsonNull());
        require(identity.reference().equals(text(enrollment.get("device"))));
        require(ControlEnrollment.origin(text(enrollment.get("origin"))).equals(text(enrollment.get("origin"))));
        String outcome=core.receive(raw);
        // A duplicate committed envelope after process restart must verify/health-check resume,
        // without new profile writes or a second application transaction.
        if("COMMITTED".equals(outcome)&&!connected.getAsBoolean())core.resume();
        return outcome;
    }
}
