package com.familyconnect.app;

import android.content.Context;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/** Same offline root as desktop update.pub; an APK resource, not a downloaded trust anchor. */
final class ControlTrust {
    static byte[] anchor(Context context)throws Exception{
        try(InputStream input=context.getAssets().open("control-anchor.pub");ByteArrayOutputStream raw=new ByteArrayOutputStream()){
            int b;while((b=input.read())!=-1){if(raw.size()>=128)throw new IOException("Invalid packaged control anchor");raw.write(b);}
            byte[] key=ControlProtocol.base64(new String(raw.toByteArray(),StandardCharsets.US_ASCII).trim(),true);
            if(key.length!=32)throw new IOException("Invalid control anchor size");return key;
        }
    }
}
