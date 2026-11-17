import argparse
import json
from pathlib import Path
import subprocess
import time


def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def main(output):
    runtime = 'com.apple.CoreSimulator.SimRuntime.iOS-18-5'
    device = run('xcrun', 'simctl', 'create', 'FC-MESH-isolated', 'com.apple.CoreSimulator.SimDeviceType.iPhone-16', runtime)
    try:
        run('xcrun', 'simctl', 'boot', device)
        run('xcrun', 'simctl', 'bootstatus', device, '-b')
        app = output / 'iphonesimulator/FamilyConnect.app'
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
        result.update(source_sha=run('git', 'rev-parse', 'HEAD'), runtime=runtime, device='iPhone 16 simulator', architecture='arm64')
        (output / 'simulator-result.json').write_text(json.dumps(result, indent=2)+'\n')
        run('xcrun', 'simctl', 'io', device, 'screenshot', output / 'simulator.png')
        if result.get('passed') is not True or result.get('handles') != 0:
            raise RuntimeError('Isolated Swift/C/Go checks failed: '+json.dumps(result))
        print(json.dumps(result))
    finally:
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', device], check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    main(parser.parse_args().out.resolve())
