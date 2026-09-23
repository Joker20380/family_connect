package com.familyconnect.app;

import android.content.Context;
import android.os.Bundle;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import java.util.concurrent.TimeUnit;
import org.junit.Test;
import static org.junit.Assume.assumeTrue;

/** Opt-in diagnostics: only delivery counters/error codes, never message contents. */
public class ChatDeliveryDiagnosticTest {
    @Test public void reportDeliveryState() throws Exception {
        assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fcDeliveryDiagnostic")));
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        ChatRuntime.WORKER.submit(()->{
            PythonRuntimeAndroid.get(context).getModule("builtins").callAttr("exec",
                "import fc_chat_transport as carrier, traceback, json\n"+
                "carrier.diagnostic_frames = ''\n"+
                "original_exchange = carrier.CarrierMailbox.exchange\n"+
                "def diagnostic_exchange(self, *args, **kwargs):\n"+
                "    try: return original_exchange(self, *args, **kwargs)\n"+
                "    except Exception as error:\n"+
                "        carrier.diagnostic_frames = json.dumps({'type': type(error).__name__, 'frames': [(f.filename.rsplit('/',1)[-1], f.name, f.lineno) for f in traceback.extract_tb(error.__traceback__)]})\n"+
                "        raise\n"+
                "carrier.CarrierMailbox.exchange = diagnostic_exchange\n",
                PythonRuntimeAndroid.get(context).getModule("builtins").callAttr("dict"));
            return null;
        }).get(30,TimeUnit.SECONDS);
        ChatRuntime.start(context);
        for(int i=0;i<4;i++) {
            SystemClock.sleep(10000);
            JsonObject state=ChatRuntime.WORKER.submit(()->ChatRuntime.open(context,false)
                .call("delivery_state",new JsonObject()).getAsJsonObject()).get(30,TimeUnit.SECONDS);
            Bundle status=new Bundle();status.putString("stream","delivery="+state+"\n");
            InstrumentationRegistry.getInstrumentation().sendStatus(0,status);
            String frames=ChatRuntime.WORKER.submit(()->PythonRuntimeAndroid.get(context)
                .getModule("fc_chat_transport").get("diagnostic_frames").toString()).get(30,TimeUnit.SECONDS);
            Bundle trace=new Bundle();trace.putString("stream","frames="+frames+"\n");
            InstrumentationRegistry.getInstrumentation().sendStatus(0,trace);
        }
    }
}
