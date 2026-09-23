package com.familyconnect.app;

import android.content.Context;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

/** Shared, lazy process startup for control and chat. No network is opened here. */
final class PythonRuntimeAndroid {
    private PythonRuntimeAndroid() {}

    static synchronized Python get(Context context) {
        if (!Python.isStarted()) Python.start(new AndroidPlatform(context.getApplicationContext()));
        return Python.getInstance();
    }
}
