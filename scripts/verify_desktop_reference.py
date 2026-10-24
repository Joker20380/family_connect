"""Verify the accepted Android reference without rebuilding or touching devices."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("clients/shared/android106-reference.json")
READINESS_MANIFEST = Path("clients/shared/desktop-readiness106.json")
RNS_PUBLIC_SOURCES = {
    "clients/android/app/src/main/assets/rns-relay.json": "clients/android/app/src/main/assets/rns-relay.json",
    "clients/android/app/src/main/python/fc_rns_transport.py": "clients/rns/fc_rns_transport.py",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or "\\" in name:
        raise ValueError("invalid manifest path")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("manifest path escapes root")
    return result


def verify(root=ROOT, capsule=False):
    manifest = json.loads((root / MANIFEST).read_text())
    if manifest["schema"] != 1 or manifest["build_tags"]:
        raise ValueError("unsupported reference or experimental build tags")
    if not set(manifest["desktop_adaptations"]).issubset(manifest["shared_sources"]):
        raise ValueError("adaptation lacks a pinned source")
    failures = []

    def check(path, expected, label):
        if not path.is_file() or digest(path) != expected:
            failures.append(label)

    for name, entry in manifest["shared_sources"].items():
        adaptation = manifest["desktop_adaptations"].get(name)
        expected = adaptation["sha256"] if adaptation else entry["sha256"]
        check(local_path(root, name), expected, name)
    for name, entry in manifest.get("desktop_test_changes", {}).items():
        if not name.endswith("_test.go"):
            raise ValueError("non-test source in test adaptations")
        check(local_path(root, name), entry["sha256"], name)
    for name, entry in manifest.get("desktop_platform_sources", {}).items():
        check(local_path(root, name), entry["sha256"], name)
    readiness = json.loads((root / READINESS_MANIFEST).read_text())
    if readiness['apk_sha256'] != manifest['reference']['apk_sha256']:
        failures.append('readiness_apk')
    if readiness['source_inventory_sha256'] != manifest['reference']['source_inventory_sha256']:
        failures.append('readiness_inventory')
    if set(readiness['rns_source_files']) != set(RNS_PUBLIC_SOURCES):
        failures.append('readiness_rns_sources')
    for accepted, public in RNS_PUBLIC_SOURCES.items():
        check(local_path(root, public), readiness['rns_source_files'].get(accepted), 'readiness_public/' + public)
    source_count = None
    if capsule:
        reference = manifest["reference"]
        inventory_path = local_path(root, reference["source_inventory"])
        check(inventory_path, reference["source_inventory_sha256"], "source_inventory")
        if "source_inventory" not in failures:
            inventory = json.loads(inventory_path.read_text())
            source_count = len(inventory)
            if source_count != reference["source_count"]:
                failures.append("source_count")
            source = local_path(root, reference["source"])
            for name, expected in inventory.items():
                check(local_path(source, name), expected, "capsule/" + name)
            for name, expected in manifest["android_ui_and_handlers"].items():
                if inventory.get(name) != expected:
                    failures.append("android_reference/" + name)
            for name, expected in readiness['rns_source_files'].items():
                if inventory.get(name) != expected:
                    failures.append('readiness_reference/' + name)
            voice = json.loads((root / 'clients/shared/android106-voice.json').read_text())
            chat = json.loads((root / 'clients/shared/android106-chat.json').read_text())
            if chat['source_inventory_sha256'] != reference['source_inventory_sha256']:
                failures.append('chat_inventory')
            for name, expected in chat['accepted_sources'].items():
                if inventory.get(name) != expected:
                    failures.append('chat_reference/' + name)
            notifications = json.loads((root / 'clients/shared/android106-notifications.json').read_text())
            if notifications['source_inventory_sha256'] != reference['source_inventory_sha256']:
                failures.append('notifications_inventory')
            for name, expected in notifications['accepted_sources'].items():
                if inventory.get(name) != expected:
                    failures.append('notifications_reference/' + name)
            announcements = json.loads((root / 'clients/shared/android106-announcements.json').read_text())
            if announcements['source_inventory_sha256'] != reference['source_inventory_sha256']:
                failures.append('announcements_inventory')
            for name, expected in announcements['accepted_sources'].items():
                if inventory.get(name) != expected:
                    failures.append('announcements_reference/' + name)
            automatic = json.loads((root / 'clients/shared/android106-auto.json').read_text())
            if automatic['source_inventory_sha256'] != reference['source_inventory_sha256']:
                failures.append('auto_inventory')
            for name, expected in automatic['accepted_sources'].items():
                if inventory.get(name) != expected:
                    failures.append('auto_reference/' + name)
            trace = automatic['reference_trace']
            check(local_path(root, trace['path']), trace['sha256'], 'auto_reference_trace')
            if voice['source_inventory_sha256'] != reference['source_inventory_sha256']:
                failures.append('voice_inventory')
            for name, expected in voice['accepted_sources'].items():
                if inventory.get(name) != expected:
                    failures.append('voice_reference/' + name)
            for name, entry in manifest["shared_sources"].items():
                if inventory.get(name) != entry["sha256"]:
                    failures.append("shared_reference/" + name)
        apk = local_path(root, reference["apk"])
        check(apk, reference["apk_sha256"], "apk")
        if "apk" not in failures:
            with zipfile.ZipFile(apk) as archive:
                native = archive.read("lib/arm64-v8a/libfc_restricted.so")
                if hashlib.sha256(native).hexdigest() != reference["restricted_native_sha256"]:
                    failures.append("restricted_native")
    return {"result": "FAIL" if failures else "PASS", "shared_files": len(manifest["shared_sources"]),
            "capsule_files": source_count, "failures": failures,
            "scope": "source integrity only; not runtime, UI, installer or APK signer verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capsule", action="store_true")
    arguments = parser.parse_args()
    result = verify(capsule=arguments.capsule)
    print(json.dumps(result, indent=2))
    return int(result["result"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
