"""Synthetic Friends UI acceptance on a disposable CI emulator; no beta signing key."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Disposable GitHub emulator only")
    serial = subprocess.check_output(["adb", "get-serialno"], text=True).strip()
    if not serial.startswith("emulator-"):
        raise SystemExit("Refusing to install a CI-signed APK on a physical device")
    build = ROOT / "clients/android"
    gradle = ["gradle", "--no-daemon", "-PfcTestBuildType=friends", "-PfcFriendsCi=true", "-PfcTargetAbi=x86_64"]
    subprocess.run(gradle + [":app:assembleFriends", ":app:assembleFriendsAndroidTest"], cwd=build, check=True)
    apk, = (build / "app/build/outputs/apk/friends").glob("*.apk")
    subprocess.run(["adb", "-s", serial, "install", "-r", str(apk)], check=True)
    subprocess.run(["adb", "-s", serial, "shell", "pm", "grant", "com.familyconnect.app.friends", "android.permission.POST_NOTIFICATIONS"], check=True)
    classes = ["AppLanguageRuntimeTest", "AppUpdateRuntimeTest", "DashboardLayoutRuntimeTest",
               "DialRuntimeTest", "RouteMapRuntimeTest", "ChatNotificationRuntimeTest",
               "ChatScrollRuntimeTest", "VoiceBubbleRuntimeTest", "VoiceHoldRuntimeTest", "VoiceRuntimeTest", "InvitationRuntimeTest"]
    subprocess.run(gradle + [":app:connectedFriendsAndroidTest",
        "-Pandroid.testInstrumentationRunnerArguments.fcInvitationCi=true",
        "-Pandroid.testInstrumentationRunnerArguments.class=" + ",".join("com.familyconnect.app." + c for c in classes)], cwd=build, check=True)

if __name__ == "__main__":
    main()
