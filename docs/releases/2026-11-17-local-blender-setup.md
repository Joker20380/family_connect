# 17 November 2026 — local Blender / Codex integration

## Scope and versions

Owner requested installing the components needed to control Blender on this laptop.
This is a local tooling checkpoint, not a Family Connect release or authorization to
resume its engineering queue. No gateway was contacted or modified. Family Connect
client/server versions, public installers, update catalogs and invitation pages are
unchanged; no application rollout or client acceptance is claimed.

- Existing Blender5.3.0, Snap revision7998, build `02f0899d78e3` is retained.
- Installed MCP for Blender2.3.0 in `~/.local/share/blender-codex/venv`, using
  Python3.14.4 and MCP SDK1.30.0. No system Python package or driver was changed.
- Upstream: <https://github.com/ahujasid/blender-mcp>, exact source commit
  `b6a2ce30c14636a562b5549684d9db6fc01f29ab`.
- Installed add-on SHA256:
  `35e5f317b932d15b485a37d914f7c9d7b527c7ea527f526569c1c111e5f39a05`.
- Native MCP registration: `blender` in the owner's Codex configuration.
  `~/.codex/skills/blender-local/SKILL.md` records the local workflow; the application
  launcher entry **Blender — Codex** uses `~/.local/bin/blender-codex`.

## Verification

- MCP initialization and live `get_scene_info` passed against the desktop GUI.
- `execute_blender_code` created eight objects in a separate test scene, including
  materials, lights and a camera; the original default scene remains intact.
- Saved `~/BlenderProjects/00_connection_test.blend`; EEVEE rendered the adjacent
  960×720 PNG. The image was opened and visually inspected.
- `look` returned a viewport image through MCP; that image was also inspected.
- Host GPU: NVIDIA GeForce GTX1650Ti, driver580.178.04. Blender's own renderer query
  confirms NVIDIA/Vulkan. The earlier sandbox-only `nvidia-smi` failure was not a
  host-driver failure; no driver repair was necessary.
- `pip check`, Python syntax checks and skill validation passed. Listener readback
  confirms `127.0.0.1:9876`, not a LAN/public bind.

The first attempted test script included Cycles preference changes. The upstream
code guard rejected it before execution. The test was rewritten to use EEVEE without
changing preferences or disabling the guard; Cycles/CUDA rendering is **NOT_RUN**.
Animation, export and third-party asset services are not part of this acceptance.

## Privacy, use and rollback

Telemetry is disabled through both environment variables and the add-on preference.
Remote connections and optional external asset/generation integrations are off.
`BLENDER_MCP_SAFE_MODE=true` is enabled, but this is an upstream Python code guard,
not an OS sandbox. The loopback listener is unauthenticated: other local processes
could control Blender while it is running. No network exposure was added.

Blender remains open on the test scene. The already-running Codex session can use
the local `mcp_call.py` client through the real MCP protocol; subsequent sessions can
load the configured server and skill normally. This fallback still requires normal
host execution approval where the terminal sandbox blocks localhost or GUI access.

Stop the connection from Blender's **N → MCP for Blender** sidebar, or disable the
`blender_mcp` add-on. `codex mcp remove blender` removes only the client registration,
not a listener in a still-running Blender process. The pre-setup Codex configuration
has a mode0600 local backup; do not publish it or overwrite later configuration
changes by blindly restoring it. Older Blender profiles and `startup.blend` remain
untouched. There was no pre-existing5.3 preferences file to overwrite.

Local installation receipt, pinned source archive and dependency inventory live in
`~/.local/share/blender-codex`; test sources and binary assets stay in
`~/BlenderProjects`, outside Git. Only this sanitized report and current-state notes
belong in the Family Connect repository. Pre-existing uncommitted changes are retained.

The existing `main` checkout was already seven commits ahead and288 behind its
tracking branch at entry. Do not merge, reset, force-push or rewrite that history
for this unrelated local-tool setup. A blocked ordinary push does not undo the
working local installation and must not be reported as a successful source push.
