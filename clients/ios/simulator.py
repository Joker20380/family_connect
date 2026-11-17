import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import time


def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def main(output):
    runtime = 'com.apple.CoreSimulator.SimRuntime.iOS-18-5'
    device = run('xcrun', 'simctl', 'create', 'FC-MESH-isolated', 'com.apple.CoreSimulator.SimDeviceType.iPhone-16', runtime)
    try:
        run('xcrun', 'simctl', 'boot', device)
        run('xcrun', 'simctl', 'bootstatus', device, '-b')
        with tempfile.TemporaryDirectory(prefix='fc-ios-simulator-') as directory:
            app = Path(directory) / 'FamilyConnect.app'
            shutil.copytree(output / 'iphonesimulator/FamilyConnect.app', app)
            run('codesign', '--force', '--sign', '-', app / 'PlugIns/MeshPacketTunnel.appex')
            run('codesign', '--force', '--sign', '-', app)
            run('xcrun', 'simctl', 'install', device, app)
        launch = run('xcrun', 'simctl', 'launch', device, 'org.familyconnect.mesh.lab', '--self-test')
        (output / 'simulator-launch.txt').write_text(launch+'\n')
        container = Path(run('xcrun', 'simctl', 'get_app_container', device, 'org.familyconnect.mesh.lab', 'data'))
        receipt = container / 'Documents/self-test.json'
        deadline = time.monotonic()+90
        while not receipt.exists() and time.monotonic() < deadline:
            time.sleep(1)
        if not receipt.exists():
            raise RuntimeError('Simulator produced no self-test receipt')
        result = json.loads(receipt.read_text())
        result.update(source_sha=run('git', 'rev-parse', 'HEAD'), runtime=runtime, device='iPhone 16 simulator', architecture='arm64', simulator_runtime_signing='ad-hoc copy; unsigned artifacts preserved')
        (output / 'simulator-result.json').write_text(json.dumps(result, indent=2)+'\n')
        run('xcrun', 'simctl', 'io', device, 'screenshot', output / 'simulator.png')
        if result.get('passed') is not True or result.get('handles') != 0:
            raise RuntimeError('Isolated Swift/C/Go checks failed: '+json.dumps(result))
        print(json.dumps(result))
        hashes = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(output.rglob('*')) if path.is_file() and path.name != 'sha256.json'}
        (output / 'sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
    finally:
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', device], check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out.resolve())
