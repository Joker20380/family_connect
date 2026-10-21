import com.android.uiautomator.core.Configurator;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public final class OwnerUi extends UiAutomatorTestCase {
    public void testRead() throws Exception {
        Configurator.getInstance().setWaitForIdleTimeout(0);
        String action = getParams().getString("action", "read");
        if (!action.equals("read")) {
            assertTrue(action.equals("Connect") || action.equals("Disconnect"));
            UiObject button = new UiObject(new UiSelector().packageName("com.familyconnect.app.friends").description(action).clickable(true));
            assertTrue(button.exists());
            assertTrue(button.click());
            System.out.println("OWNER_ACTION " + action);
            return;
        }
        for (int index = 0; index < 32; index++) {
            UiObject object = new UiObject(new UiSelector().packageName("com.familyconnect.app.friends").clickable(true).instance(index));
            if (!object.exists()) break;
            System.out.println("OWNER_BUTTON " + object.getText() + " | " + object.getContentDescription() + " | " + object.getBounds().toShortString());
        }
    }
}
