"""Build the service-owned desktop worker from pinned106 sources; never install it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
XRAY_REVISION = "d2758a023cd7f4174a5a5fa4ff66e487d4342ba0"
PATCH_SHA256 = "eaeb30fd1e2aa52272d7f3a2a06bcad7b983ca9866a87fbd0a614eede6048872"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources(source):
    inventory = {str(path.relative_to(ROOT)): digest(path) for folder in (ROOT / "carrier", source)
                 for path in sorted(folder.rglob("*")) if path.is_file() and path.suffix in (".go", ".mod", ".sum", ".patch") and "state-client-build" not in path.relative_to(folder).parts}
    inventory["clients/shared/android106-reference.json"] = digest(ROOT / "clients/shared/android106-reference.json")
    inventory["clients/shared/android106-chat.json"] = digest(ROOT / "clients/shared/android106-chat.json")
    inventory["scripts/build_desktop_mesh.py"] = digest(Path(__file__))
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--go", type=Path, required=True)
    parser.add_argument("--xray", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--os", choices=("linux", "windows"), required=True)
    parser.add_argument("--arch", choices=("amd64",), default="amd64")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    args.go, args.xray, args.out = args.go.resolve(), args.xray.resolve(), args.out.resolve()
    if args.out.exists():
        raise ValueError("fresh output directory required; preserve prior builds")
    source = ROOT / "clients/mesh"
    patch = source / "xray-packet-boundary.patch"
    if digest(patch) != PATCH_SHA256:
        raise ValueError("accepted106 packet patch does not match")
    from scripts.verify_desktop_reference import verify
    if verify()["result"] != "PASS":
        raise ValueError("shared106 source verification failed")
    subprocess.run(["git", "-C", str(args.xray), "cat-file", "-e", XRAY_REVISION + "^{commit}"], check=True)
    environment = {key: value for key, value in os.environ.items() if not key.startswith(("FC_", "YANDEX_", "CGO_"))}
    environment.update(GOOS=args.os, GOARCH=args.arch, CGO_ENABLED="0", GOFLAGS="", GOTOOLCHAIN="local", GOWORK="off")
    args.out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="fc-desktop-mesh-") as temporary:
        workspace = Path(temporary)
        archive = workspace / "xray.tar"
        subprocess.run(["git", "-C", str(args.xray), "archive", "--format=tar", "-o", str(archive), XRAY_REVISION], check=True)
        xray = workspace / "xray"
        xray.mkdir()
        with tarfile.open(archive) as bundle:
            bundle.extractall(xray, filter="data")
        subprocess.run(["git", "apply", str(patch)], cwd=xray, env=environment | {"GIT_CEILING_DIRECTORIES": str(workspace)}, check=True)
        module = workspace / "bridge.mod"
        shutil.copyfile(source / "go.mod", module)
        shutil.copyfile(source / "go.sum", module.with_suffix(".sum"))
        subprocess.run([str(args.go), "mod", "edit", "-modfile=" + str(module),
                        "-replace=github.com/xtls/xray-core=" + str(xray),
                        "-replace=github.com/Joker20380/family_connect/carrier=" + str(ROOT / "carrier")], cwd=source, env=environment, check=True)
        inventory = sources(source)
        source_digest = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if args.test:
            host = subprocess.check_output([str(args.go), "env", "GOHOSTOS"], env=environment, text=True).strip()
            if host != args.os:
                raise ValueError("runtime tests require the target OS; cross-build is not runtime")
            with (args.out / "test.log").open("x") as output:
                subprocess.run([str(args.go), "test", "-race", "-count=1", "-mod=readonly", "-modfile=" + str(module), "./..."],
                               cwd=source, env=environment | {"CGO_ENABLED": "1"}, stdout=output, stderr=subprocess.STDOUT, check=True)
        binary = args.out / ("fc-mesh.exe" if args.os == "windows" else "fc-mesh")
        command = [str(args.go), "build", "-p=2", "-buildvcs=false", "-mod=readonly", "-modfile=" + str(module), "-trimpath",
                   "-ldflags=-checklinkname=0 -X main.sourceManifest=" + source_digest, "-o", str(binary), "./cmd/fc-mesh"]
        with (args.out / "build.log").open("x") as output:
            subprocess.run(command, cwd=source, env=environment, stdout=output, stderr=subprocess.STDOUT, check=True)
        modules = subprocess.check_output([str(args.go), "list", "-mod=readonly", "-modfile=" + str(module), "-deps", "-f", "{{if .Module}}{{.Module.Path}} {{.Module.Version}} {{.Module.Dir}}{{end}}", "./cmd/fc-mesh"], cwd=source, env=environment, text=True)
        licenses = args.out / "licenses"
        licenses.mkdir()
        shutil.copytree(ROOT / "carrier/licenses", licenses / "carrier")
        module_inventory = {}
        for line in sorted(set(modules.splitlines())):
            if not line.strip():
                continue
            name, version, directory = line.split(" ", 2)
            if name.startswith("github.com/Joker20380/family_connect/"):
                continue
            if name == "github.com/xtls/xray-core":
                version = XRAY_REVISION
            notices = {}
            destination = licenses / name.replace("/", "_")
            for path in sorted(Path(directory).rglob("*")):
                if path.is_file() and (path.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")) or path.parent.name == "LICENSES"):
                    target = destination / path.relative_to(directory)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
                    notices[str(target.relative_to(licenses))] = digest(target)
            if not notices:
                raise ValueError("dependency notice missing: " + name)
            module_inventory[name] = {"version": version, "notices": notices}
        goroot = Path(subprocess.check_output([str(args.go), "env", "GOROOT"], env=environment, text=True).strip())
        shutil.copyfile(goroot / "LICENSE", licenses / "Go.txt")
        shutil.copyfile(patch, licenses / "Xray-modifications.patch")
        if sources(source) != inventory:
            raise ValueError("source set changed during build")
        (args.out / "source-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
        (args.out / "dependencies.json").write_text(json.dumps(module_inventory, indent=2) + "\n")
        manifest = {"schema": 1, "os": args.os, "arch": args.arch, "reference": "android106-native105",
                    "source_digest": source_digest, "xray_revision": XRAY_REVISION, "xray_patch_sha256": PATCH_SHA256,
                    "go": subprocess.check_output([str(args.go), "version"], text=True).strip(), "build_tags": [],
                    "files": {binary.name: {"sha256": digest(binary), "size": binary.stat().st_size}},
                    "installed": False, "runtime_acceptance": "NOT_RUN", "publicly_distributed": False}
        manifest["local_packet_ipc_tests"] = "PASS" if args.test else "NOT_RUN"
        manifest["chat_reference_manifest"] = inventory["clients/shared/android106-chat.json"]
        manifest["chat_integration"] = {"vpn_ownership": "integrated",
                                        "private_worker_ipc": "inherited-unix-stream-v1" if args.os == "linux" else "NOT_INTEGRATED",
                                        "desktop_api_mailbox_ipc": "linux-existing-exit-host-source" if args.os == "linux" else "NOT_INTEGRATED",
                                        "service_only_host": "NOT_INTEGRATED",
                                        "protected_underlying_direct": "linux-fixed-chat-host-source" if args.os == "linux" else "NOT_INTEGRATED"}
        (args.out / "build.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
