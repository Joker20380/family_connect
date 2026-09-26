package com.familyconnect.app;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.chaquo.python.Python;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class ControlRnsRuntimeTest {
    @Test public void packagedPythonImportsRnsAndInitializesWithoutDeviceKeys(){
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        var python=PythonRuntimeAndroid.get(context);assertEquals("1.5.1",python.getModule("RNS").get("__version__").toString());
        assertEquals("internal",python.getModule("RNS.Cryptography.Provider").callAttr("backend").toString());
        python.getModule("fc_rns_transport").callAttr("initialize",new java.io.File(context.getNoBackupFilesDir(),"rns-runtime-test").getAbsolutePath());
    }
}
