import com.android.uiautomator.core.Configurator;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public final class SubscriptionDeviceUi extends UiAutomatorTestCase {
    public void testUi() throws Exception {
        Configurator.getInstance().setWaitForIdleTimeout(0);
        String label = getParams().getString("click");
        if (label != null) {
            UiObject button = new UiObject(new UiSelector()
                .packageName("com.familyconnect.app.friends").text(label).clickable(true));
            assertTrue(button.exists());
            assertTrue(button.click());
        }
        getUiDevice().dumpWindowHierarchy("fc-subscription-3.xml");
    }
}
