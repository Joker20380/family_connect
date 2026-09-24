# Android bridge host acceptance

With Go1.26.1 on PATH, run `python3 pilot/android-tcp/host-check/build.py --core /path/to/pinned/xray-source --output /new/private/build-directory`.
It verifies the clean source revision, copies the real bridge and host stubs, then
runs `go test` and `go build`.
Then run `python3 -m scripts.check_xhttp --xray /path/to/pinned/xray --client-binary /path/to/driver`.

The driver uses the actual Android bridge's protected dialer and session cleanup,
with a host stub for `VpnService.protect`; its only permitted destination is the
lab origin on loopback. No Android device, VPN permission, JNI or TUN is exercised.
The stub is never copied into `pilot/android-awg/build.py` or shipped in an APK.
