#!/usr/bin/env python3
"""Build the existing carrier CLI as an extracted Android PIE test executable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ndk", type=Path, required=True)
    parser.add_argument("--go", default="go")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    generated = root / "clients/android/telemost-runtime/native-generated"
    binary = generated / "jniLibs/arm64-v8a/libfc_telemost.so"
    binary.parent.mkdir(parents=True, exist_ok=True)
    toolchain = args.ndk.resolve() / "toolchains/llvm/prebuilt/linux-x86_64/bin"
    env = os.environ.copy()
    env.pop("FC_TELEMOST_ROOM", None)
    env.update(GOOS="android", GOARCH="arm64", CGO_ENABLED="1",
               CC=str(toolchain / "aarch64-linux-android26-clang"),
               CGO_LDFLAGS="-Wl,-z,max-page-size=16384")
    subprocess.run([args.go, "build", "-trimpath", "-buildmode=pie", "-ldflags=-checklinkname=0", "-o", str(binary),
                    "./cmd/telemost-binary"], cwd=root / "carrier", env=env, check=True)
    assets = generated / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copytree(root / "carrier/licenses", assets / "licenses", dirs_exist_ok=True)
    shutil.copyfile(args.ndk / "NOTICE", assets / "licenses/android-ndk-NOTICE.txt")
    shutil.copyfile(toolchain.parent / "NOTICE", assets / "licenses/llvm-NOTICE.txt")
    metadata = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root)),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "go": subprocess.check_output([args.go, "version"], env=env, text=True).strip(),
        "ndk": (args.ndk / "source.properties").read_text().strip(),
        "abi": "arm64-v8a", "min_api": 26, "scope": "synthetic-only, no TUN, sockets unprotected",
    }
    (assets / "build.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
