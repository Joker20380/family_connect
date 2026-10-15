import pathlib
import sys

root = pathlib.Path(sys.argv[1])
native = root / 'pilot/android-restricted/native'
main = (native / 'main.go').read_text()
chat = (native / 'chat.go').read_text()
checks = {
    'VPN reserves shared gate before bootstrap': 'transportOwner.ReserveVPN(ctx)' in main,
    'VPN awaits real cleanup before bootstrap': 'owned.ownership.Wait(ctx)' in main and main.index('owned.ownership.Wait(ctx)') < main.index('wholedevice.OpenProvisioned(ctx'),
    'chat acquires through same production gate': 'transportOwner.AcquireChat(' in chat,
    'chat does not take ownerMu': 'ownerMu.Lock()' not in chat,
    'Java can reacquire cancelled handles': 'NativeRestricted.chatState(handle) < 0' in (root / 'clients/android/app/src/main/java/com/familyconnect/app/ChatCarrier.java').read_text(),
}
for name, passed in checks.items():
    print(('PASS ' if passed else 'FAIL ') + name)
sys.exit(0 if all(checks.values()) else 1)
