"""Synthetic Friends UI acceptance on a disposable CI emulator; no beta signing key."""
import argparse
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]

def ready_emulator():
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10, check=True)
        devices = [line.split() for line in result.stdout.splitlines()[1:] if line.strip()]
        if len(devices) > 1 or any(not device[0].startswith("emulator-") for device in devices):
            raise SystemExit("Expected only one disposable emulator")
        if len(devices) == 1 and devices[0][1:] == ["device"]:
            serial = devices[0][0]
            boot = subprocess.run(["adb", "-s", serial, "shell", "getprop", "sys.boot_completed"],
                                  capture_output=True, text=True, timeout=10)
            if boot.returncode == 0 and boot.stdout.strip() == "1":
                return serial
        time.sleep(2)
    raise SystemExit("Disposable emulator did not become ready within 90 seconds")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy', action='store_true')
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Disposable GitHub emulator only")
    serial = ready_emulator()
    if not serial.startswith("emulator-"):
        raise SystemExit("Refusing to install a CI-signed APK on a physical device")
    sdk = int(subprocess.check_output(["adb", "-s", serial, "shell", "getprop", "ro.build.version.sdk"], text=True).strip())
    if args.legacy and sdk != 27:
        raise SystemExit("Legacy acceptance requires Android 8.1/API27")
    build = ROOT / "clients/android"
    gradle = ["gradle", "--no-daemon", "-PfcTestBuildType=friends", "-PfcFriendsCi=true", "-PfcTargetAbi=x86_64"]
    subprocess.run(gradle + [":app:assembleFriends", ":app:assembleFriendsAndroidTest"], cwd=build, check=True)
    apk, = (build / "app/build/outputs/apk/friends").glob("*.apk")
    subprocess.run(["adb", "-s", serial, "install", "-r", str(apk)], check=True)
    if sdk >= 33:
        subprocess.run(["adb", "-s", serial, "shell", "pm", "grant", "com.familyconnect.app.friends", "android.permission.POST_NOTIFICATIONS"], check=True)
    classes = ["AppLanguageRuntimeTest", "AppUpdateRuntimeTest", "DashboardLayoutRuntimeTest",
               "DialRuntimeTest", "RouteMapRuntimeTest", "ChatNotificationRuntimeTest",
               "ChatScrollRuntimeTest", "VoiceBubbleRuntimeTest", "VoiceHoldRuntimeTest", "VoiceRuntimeTest", "InvitationRuntimeTest", "AndroidCompatibilityRuntimeTest"]
    try:
        subprocess.run(gradle + [":app:connectedFriendsAndroidTest",
            "-Pandroid.injected.androidTest.leaveApksInstalledAfterRun=true",
            "-Pandroid.testInstrumentationRunnerArguments.fcInvitationCi=true",
            "-Pandroid.testInstrumentationRunnerArguments.class=" + ",".join("com.familyconnect.app." + c for c in classes)], cwd=build, check=True)
        images = ROOT / "android-ci-ui"
        if args.legacy:
            images = images / "api27"
        images.mkdir(parents=True, exist_ok=True)
        for name in ("dashboard-cpu-load.png", "server-row-cpu-load.png", "dashboard-failed-controls.png", "server-amsterdam-1.png", "server-amsterdam-2.png", "android-compatibility-voice.png"):
            subprocess.run(["adb", "-s", serial, "pull",
                "/sdcard/Android/data/com.familyconnect.app.friends/files/ui-acceptance/" + name,
                str(images / name)], check=True)
    finally:
        for package in ("com.familyconnect.app.friends.test", "com.familyconnect.app.friends"):
            subprocess.run(["adb", "-s", serial, "uninstall", package], timeout=60, check=False)

if __name__ == "__main__":
    main()
