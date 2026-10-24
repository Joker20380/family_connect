# Laptop thermal diagnostic —2026-10-23,18:29 CEST

Read-only host process, memory, vmstat, sensors and procfs inspection.
No deployments, versions, services or processes changed; rollback not applicable.

- Main observed load: Android emulator `fc-parity106`, PID1088092, parent Codex
  PID447275 with Family Connect working directory. Running approximately56min.
- Current3s CPU sample573.6% (about5.7 logical CPUs), RSS3830272KiB.
- Headless emulator arguments:2 guest cores,1536MiB guest RAM,
  `swiftshader_indirect` GPU. KVM descriptor open: not evidence of disabled KVM.
  Exact hot thread/function was not profiled; software rendering is a candidate,
  not a proven sole internal cause.
- CPU package100°C at critical threshold; cpu0 core throttle count4165→4172 and
  package count89736→89973 over3s. Active thermal throttling confirmed.
-12 logical CPUs; load7.44/7.30/5.21. Available RAM approximately18GiB of30GiB;
  swap0/8GiB. Sampled IO wait0%; disks64% root,55% data.
- Fans approximately5400/5700RPM. No fan-control changes made.

Next: obtain owner approval/coordinate with other active session before graceful
AVD shutdown, then remeasure CPU and temperatures. Preserve ongoing test work.
No runtime tests or stress tests run; no release or artifact verification needed.

## Remediation by the owning parity session

The above is the original read-only observation, not the final process state.
The parity session stopped only its verified `fc-parity106` PID1088092. Subsequent
measurement: process absent, CPU51°C and5.3% total busy over2s. No physical phone,
other working session, gateway or application service was stopped.

Owner clarified that emulator-based development must continue on the laptop's
GPU rather than being abandoned. Host inventory confirms Intel UHD and NVIDIA
GeForce GTX1650Ti Mobile, NVIDIA driver580.178.04. PRIME `glxinfo -B` reports direct
rendering and NVIDIA OpenGL/ES; this alone was not treated as emulator evidence.

A fresh bounded run of the same AVD used `-gpu host -accel on -cores 2 -memory 2560
-no-window -no-audio -no-boot-anim -no-snapshot`, with the existing dedicated adb5040
and emulator5582. NVIDIA selection was explicit:

```text
__NV_PRIME_RENDER_OFFLOAD=1
__GLX_VENDOR_LIBRARY_NAME=nvidia
__VK_LAYER_NV_optimus=NVIDIA_only
VK_DRIVER_FILES=/usr/share/vulkan/icd.d/nvidia_icd.json
QT_QPA_PLATFORM=xcb
```

The user systemd service enforced `CPUQuota=150%`, `RuntimeMaxSec=180s`,
`TimeoutStopSec=8s`, `KillMode=control-group`, `Nice=10`. Its watchdog sampled CPU
temperature every2s and NVIDIA periodically, with CPU85°C/GPU80°C stop thresholds.
The first launch attempt stopped before starting the emulator because CPU was
already at least70°C; the second passed the prelaunch check. No threshold was raised.

Actual second-run results:
- Emulator log selects NVIDIA for both host Vulkan and host GLES.
- Guest SurfaceFlinger: `Google (NVIDIA Corporation), Android Emulator OpenGL ES
  Translator (NVIDIA GeForce GTX 1650 Ti/PCIe/SSE2)`.
- Boot completed30.3s; offline connectivity still `Active default network: none`.
- Existing unchanged106 launched and its RU disconnected home rendered correctly;
  console screenshot visually inspected. No APK reinstall or user-phone operation.
- Sampled emulator CPU28.8–150.7% (cgroup quota, about1.5 logical CPUs, not150% of
  the entire12-CPU laptop); sampled CPU peak82°C, GPU peak63°C. Short sampling
  variation is not a strict per-sample quota guarantee. This is not a long soak
  result and does not prove software rendering alone caused the earlier heat.
- Completed around51s; finally-stop removed the entire service cgroup.
  `MainPID=0`, inactive unit, old/new emulator PIDs1088092/1233373 absent.
  CPU67°C immediately after stop, later72°C; other laptop load remains independent.

Evidence: `state-client-build/desktop-parity106-20261023/reference-emulator/host-gpu-check-2/`
contains `emulator.log`, `result.json`, `launch.py` and `Screenshot_1792773766.png`.
The JSON records effective service limits, timing, guest renderer, samples and stop
readback. AVD config now defaults GPU enabled/host and2 cores; launch-time NVIDIA
selection and systemd/watchdog bounds are still mandatory, not provided by the
AVD config alone. The recorded script is the exact one-shot check; select a new
evidence directory before reuse, never overwrite an earlier result.

No emulator is left running. Future reference checks retain these bounds and stop
after capture. GPU absence/failure must be reported, not silently replaced with
SwiftShader. No global driver, power, fan or thermal-protection settings changed.

## Owner-requested visible GPU rerun —23 October,22:43–22:45 CEST

`reference-emulator/launch-host-gpu-check-3.py` reuses the prior bounded launcher
with a fresh evidence directory, a visible window and capture90s after boot.
NVIDIA GTX1650Ti is again confirmed by guest SurfaceFlinger, not only host logs.
KVM,2 cores,2560MiB,CPUQuota150%,180s maximum and CPU85°C/GPU80°C guards remain.
Boot30.2s; final sample122.1s. Sampled CPU peak81°C/GPU61°C; CPU82°C immediately
after stop. This short run is not a sustained thermal certification.
Offline unchanged106 home screenshot visually inspected; no APK reinstall,
physical phone operation or network session. Finally-stop confirms inactive unit,
MainPID0 and no remaining emulator process. No global machine settings changed.

Evidence: `state-client-build/desktop-parity106-20261023/reference-emulator/host-gpu-check-3/`
contains emulator log, result JSON and `Screenshot_1792788304.png`.
