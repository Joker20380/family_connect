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
        for (int index = 0; index < 96; index++) {
            UiObject object = new UiObject(new UiSelector()
                .packageName("com.familyconnect.app.friends").instance(index));
            if (!object.exists()) break;
            System.out.println("SUBSCRIPTION_UI " + object.getClassName() + " | "
                + object.getText() + " | " + object.getBounds().toShortString());
        }
    }
}
