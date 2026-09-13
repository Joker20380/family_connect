package com.familyconnect.app;
import android.util.Log;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
@RunWith(AndroidJUnit4.class)
public class ControlProtocolRuntimeTest {
    @Test public void immutableCorpus()throws Exception {
        String result=ControlVectors.run(name->InstrumentationRegistry.getInstrumentation().getContext().getAssets().open(name));
        Log.i("FamilyConnectControl",result);
    }
    @Test public void strictJson()throws Exception {ControlVectors.jsonRefusals();}
}
