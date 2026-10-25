"""Run exact candidate gates only inside a disposable offline Ubuntu system."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

sys.dont_write_bytecode = True
RESULTS = {}
HOME = Path(pwd.getpwuid(1000).pw_dir)
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C', 'HOME': str(HOME),
       'XDG_RUNTIME_DIR': '/run/user/1000', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/1000/bus',
       'DISPLAY': ':99', 'GSK_RENDERER': 'cairo', 'GTK_A11Y': 'none', 'APPIMAGE_EXTRACT_AND_RUN': '1',
       'PYTHONDONTWRITEBYTECODE': '1'}
SYSTEM = Path('/usr/local/lib/family-connect-mesh')


def run(*command, user=False, uid=1000, ok=True, **options):
    if user:
        command = ('setpriv', '--reuid', str(uid), '--regid', str(pwd.getpwuid(uid).pw_gid), '--init-groups', *command)
    result = subprocess.run(command, env=ENV, text=True, capture_output=True, timeout=300, **options)
    if ok and result.returncode:
        raise AssertionError((command[:4], result.returncode, result.stdout[-1000:], result.stderr[-2200:]))
    return result


def record(name, value=True):
    RESULTS[name] = value
    print(json.dumps({name: value}), flush=True)


def wait(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.2)
    raise AssertionError('Timed out waiting for real service')


def no_vpn():
    assert [item['ifname'] for item in json.loads(run('ip', '-j', 'link').stdout)] == ['lo']
    assert not Path('/run/family-connect-mesh/active.json').exists()
    assert not Path('/run/family-connect-auto/normal.json').exists()


def retained_old_system(root, application):
    raw = Path('/evidence/build-9.tar.gz').read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    assert checksum == 'bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9'
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        manifest = json.load(archive.extractfile('FamilyConnect-MESH-system-amd64/manifest.json'))
    assert manifest['build_id'] == '8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da'
    spec = importlib.util.spec_from_file_location('verified_setup', root/'candidate_setup.py')
    setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup)
    expected = dict(size=len(raw), sha256=checksum, build_id=manifest['build_id'],
                    source_digest=manifest['source_digest'], installer_sha256=manifest['sha256']['install.py'])
    with tempfile.TemporaryDirectory(prefix='old-system-fixture-') as directory:
        component = setup.extract_verified(raw, expected, Path(directory))
        run('/usr/bin/python3', '-I', str(component/'install.py'))
    assert json.loads((SYSTEM/'capabilities.json').read_text())['build_id'] == manifest['build_id']
    status = json.loads(run(*application, '--candidate-status', user=True).stdout)
    assert status['system'] != 'READY'
    no_vpn()
    record('actual_retained_build_9_mismatch', dict(build_id=manifest['build_id'], status=status['system']))


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert Path('/proc/1/comm').read_text().strip() == 'systemd'
    assert os.environ['FC_L032_HOST_NETNS'] != str(Path('/proc/self/ns/net').stat().st_ino)
    release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    platform = (release['ID'].strip('"'), release['VERSION_ID'].strip('"'))
    systemd, python_abi = {('ubuntu', '24.04'): ('255', (3, 12)), ('ubuntu', '26.04'): ('259', (3, 14))}[platform]
    assert run('systemctl', '--version').stdout.startswith('systemd ' + systemd + ' ')
    assert sys.version_info[:2] == python_abi
    record('platform', dict(distribution=platform, systemd=systemd, python=python_abi))
    wait(lambda: run('systemctl', 'is-active', 'dbus', 'systemd-resolved', ok=False).stdout.split() == ['active', 'active'])
    no_vpn()
    assert not SYSTEM.exists()
    mode, artifact = sys.argv[1:]
    mixed = mode == 'deb-old-system'
    if mixed:
        mode = 'deb'
    prestart = mode.removeprefix('prestart-') if mode in ('prestart-awg', 'prestart-tcp') else None
    if prestart:
        mode = 'deb'
    artifact = Path(artifact)
    record('artifact', dict(mode=mode, file=artifact.name, size=artifact.stat().st_size,
                            sha256=hashlib.sha256(artifact.read_bytes()).hexdigest()))
    run('loginctl', 'enable-linger', '1000')
    run('systemctl', 'start', 'user@1000.service')
    wait(lambda: Path('/run/user/1000/bus').exists())
    display = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x900x24', '-nolisten', 'tcp', '-ac'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait(lambda: Path('/tmp/.X11-unix/X99').exists())
    run('useradd', '-m', '-u', '1001', 'other-user')
    if mode == 'deb':
        run('dpkg', '-i', str(artifact))
        root = Path('/usr/lib/family-connect')
        application = ['/usr/bin/family-connect']
        assert 'x-scheme-handler/familyconnect' in Path('/usr/share/applications/com.familyconnect.Client.desktop').read_text()
        assert Path('/usr/lib/systemd/user/family-connect-chat.service').is_file()
    else:
        image = HOME / artifact.name
        shutil.copyfile(artifact, image)
        image.chmod(0o755)
        os.chown(image, 1000, pwd.getpwuid(1000).pw_gid)
        destination = Path('/opt/appimage')
        destination.mkdir()
        os.chown(destination, 1000, pwd.getpwuid(1000).pw_gid)
        run(str(image), '--appimage-extract', user=True, cwd=destination)
        root = destination / 'squashfs-root/usr/lib/family-connect'
        ENV.update(APPIMAGE=str(image), APPDIR=str(destination / 'squashfs-root'))
        application = [str(image), '--appimage-extract-and-run']
        run(*application, '--integrate', user=True)
        desktop = HOME / '.local/share/applications/com.familyconnect.Client.desktop'
        assert 'Exec="' + str(image) + '" %u' in desktop.read_text()
    no_vpn()
    assert not SYSTEM.exists()
    assert run('systemctl', '--user', 'is-active', 'family-connect-chat.service', user=True, ok=False).returncode != 0
    check = json.loads(run(*application, '--candidate-check', user=True).stdout)
    assert check['user_imports'] == 'PASS'
    run(*application, '--smoke', user=True)
    assert not SYSTEM.exists()
    record('clean_user_install_imports_gui_no_silent_system_setup')
    contract = json.loads((root / 'candidate.json').read_text())
    root_source = (root / 'candidate_setup.py').read_text() + '\nroot_main(' + repr(contract['system']) + ')\n'
    expected_command = '/usr/bin/python3 -I -S -c ' + root_source
    rule = '''polkit.addRule(function(action, subject) {
        if (action.id === "org.freedesktop.policykit.exec") {
            if (subject.user === USER && ((action.lookup("program") === "/usr/bin/python3" &&
                 action.lookup("command_line") === COMMAND) ||
                 action.lookup("program") === "/usr/local/lib/family-connect-mesh/helper")) {
                return polkit.Result.YES;
            }
            return polkit.Result.NO;
        }
    });'''.replace('USER', json.dumps(pwd.getpwuid(1000).pw_name)).replace('COMMAND', json.dumps(expected_command))
    Path('/etc/polkit-1/rules.d/00-fc-candidate-fixture.rules').write_text(rule)
    if prestart:
        session_rule = '''polkit.addRule(function(action, subject) {
            if (action.id === "org.freedesktop.policykit.exec" && subject.user === USER &&
                ((action.lookup("program") === "/usr/local/lib/family-connect-awg/helper" &&
                  action.lookup("command_line") === "/usr/local/lib/family-connect-awg/helper session") ||
                 (action.lookup("program") === "/usr/local/lib/family-connect-tcp/helper" &&
                  action.lookup("command_line") === "/usr/local/lib/family-connect-tcp/helper session"))) {
                return polkit.Result.YES;
            }
        });'''.replace('USER', json.dumps(pwd.getpwuid(1000).pw_name))
        Path('/etc/polkit-1/rules.d/00-aa-fc-prestart-fixture.rules').write_text(session_rule)
    run('systemctl', 'restart', 'polkit')
    assert run(*application, '--setup-system', '/tmp/other-installer', user=True, ok=False).returncode != 0
    assert run(*application, '--setup-system', user=True, uid=1001, ok=False).returncode != 0
    denied = run('/usr/bin/pkexec', '/usr/bin/python3', '-I', '-S', '-c', root_source, user=True, uid=1001, ok=False)
    assert denied.returncode == 127 and 'Not authorized' in denied.stderr
    assert not SYSTEM.exists()
    if mixed:
        retained_old_system(root, application)
    receipt = json.loads(run(*application, '--setup-system', user=True).stdout)
    assert receipt['installed'] and not receipt['service_started']
    assert json.loads(run(*application, '--candidate-status', user=True).stdout)['system'] == 'READY'
    no_vpn()
    second = json.loads(run(*application, '--setup-system', user=True).stdout)
    assert second['installed'] and second['backup'] != receipt['backup']
    assert not list(Path('/tmp').glob('family-connect-user-setup-*'))
    assert not list(Path('/var/tmp').glob('family-connect-root-setup-*'))
    record('explicit_polkit_setup_reinstall_uid_path_and_cleanup', dict(build_id=contract['system']['build_id']))
    if prestart:
        evidence = run('/usr/bin/env', 'FC_PRESTART_EXPECT=green',
                       'FC_L032_HOST_NETNS='+os.environ['FC_L032_HOST_NETNS'], '/usr/bin/python3', '-I', '-S',
                       '/fixture/prestart.py', 'parent', prestart).stdout
        record('actual_prestart_terminalization', json.loads(evidence))
        no_vpn()
        return
    damaged = Path('/opt/tampered-user')
    shutil.copytree(root, damaged)
    for member in (damaged, *damaged.rglob('*')):
        os.chown(member, 1000, pwd.getpwuid(1000).pw_gid)
    candidate_record = (damaged / 'candidate.json').read_bytes()
    (damaged / 'candidate.json').unlink()
    refused = run('/usr/bin/python3', '-I', str(damaged / 'launcher.py'), '--smoke', user=True, ok=False)
    assert refused.returncode != 0 and 'candidate.json' in refused.stderr
    (damaged / 'candidate.json').write_bytes(candidate_record)
    (damaged / 'embedded/system.tar.gz').write_bytes(b'tampered')
    refused = run('/usr/bin/python3', '-I', str(damaged / 'launcher.py'), '--setup-system', user=True, ok=False)
    assert refused.returncode != 0 and 'Candidate member hash mismatch' in refused.stderr
    inventory_path, capability_path = SYSTEM / 'installed.json', SYSTEM / 'capabilities.json'
    original_inventory, original_capability = inventory_path.read_bytes(), capability_path.read_bytes()
    inventory, capability = json.loads(original_inventory), json.loads(original_capability)
    inventory['build_id'] = capability['build_id'] = '0'*64
    inventory_path.write_text(json.dumps(inventory))
    capability['installed_sha256'] = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    capability_path.write_text(json.dumps(capability))
    assert json.loads(run(*application, '--candidate-status', user=True).stdout)['system'] == 'CANDIDATE_SYSTEM_BUILD_MISMATCH'
    inventory_path.write_bytes(original_inventory)
    capability_path.write_bytes(original_capability)
    capability = json.loads(original_capability)
    capability['schema'] = 1
    capability_path.write_text(json.dumps(capability))
    assert json.loads(run(*application, '--candidate-status', user=True).stdout)['system'] != 'READY'
    capability_path.write_bytes(original_capability)
    module = SYSTEM / 'mesh_ownership.py'
    original_module = module.read_bytes()
    module.write_bytes(original_module + b'\n')
    assert json.loads(run(*application, '--candidate-status', user=True).stdout)['system'] != 'READY'
    module.write_bytes(original_module)
    record('tampered_embedded_and_mixed_system_fail_closed')
    run(*application, '--prepare-chat', user=True)
    for kind in ('direct', 'mesh'):
        assert run('systemctl', 'is-active', 'family-connect-chat-' + kind + '@1000.service').stdout.strip() == 'active'
    no_vpn()
    record('fixed_chat_prepare_without_vpn')
    prefix = 'import sys;from pathlib import Path;sys.path[:0]=' + repr([str(root / 'clients/desktop'), str(root), str(root / 'vendor')]) + ';'
    run('/usr/bin/python3', '-I', '-c', prefix +
        'from device_identity.friends import load_friends_identity;'
        'directory=Path.home()/".local/share/family-connect";directory.mkdir(mode=0o700,parents=True,exist_ok=True);'
        'load_friends_identity(directory/"friends-identity",create=True)', user=True)
    keyring = subprocess.Popen(['setpriv', '--reuid', '1000', '--regid', str(pwd.getpwuid(1000).pw_gid), '--init-groups',
                               'gnome-keyring-daemon', '--foreground', '--unlock', '--components=secrets'],
                              env=ENV, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    keyring.stdin.write(b'synthetic-disposable-keyring\n')
    keyring.stdin.close()
    time.sleep(1)
    run('/usr/bin/python3', '-I', '-c', prefix +
        'from provisioning.chat_client import ChatClient;client=ChatClient();client.open(create=True);'
        'assert client.invoke("background_delivery",enabled=True)["background"];client.close()', user=True)
    pid = run('systemctl', '--user', 'show', 'family-connect-chat.service', '-p', 'MainPID', '--value', user=True).stdout.strip()
    assert int(pid) > 0
    run(*application, '--smoke', user=True)
    time.sleep(3)
    assert run('systemctl', '--user', 'show', 'family-connect-chat.service', '-p', 'MainPID', '--value', user=True).stdout.strip() == pid
    command = run('systemctl', '--user', 'show', 'family-connect-chat.service', '-p', 'ExecStart', '--value', user=True).stdout
    assert ('/usr/bin/family-connect' if mode == 'deb' else str(image)) in command
    run('/usr/bin/python3', '-I', '-c', prefix +
        'from provisioning.chat_client import ChatClient;client=ChatClient();assert client.invoke("delivery_settings")["background"];client.close()', user=True)
    record('real_user_dbus_background_owner_survives_gui_exit')
    if mode == 'deb':
        run('dpkg', '-i', str(artifact))
        run('dpkg', '--remove', 'family-connect')
        assert not root.exists()
        assert run('systemctl', '--user', 'is-active', 'family-connect-chat.service', user=True, ok=False).returncode != 0
        assert not Path('/usr/lib/systemd/user/family-connect-chat.service').exists()
        assert (SYSTEM / 'installed.json').read_bytes() == original_inventory
        assert Path(receipt['backup']).is_dir()
        run('dpkg', '-i', str(artifact))
        run('systemctl', '--user', 'daemon-reload', user=True)
        run('/usr/bin/python3', '-I', '-c', prefix +
            'from provisioning.chat_client import ChatClient;client=ChatClient();client.open();'
            'assert client.invoke("delivery_settings")["background"];client.close()', user=True)
        record('deb_remove_preserves_encrypted_state_and_independent_root_runtime')
        peer = HOME / artifact.name.replace('FamilyConnect_', 'FamilyConnect-').replace('_amd64.deb', '-x86_64.AppImage')
        shutil.copyfile(artifact.parent / peer.name, peer)
        peer.chmod(0o755)
        os.chown(peer, 1000, pwd.getpwuid(1000).pw_gid)
        peer_application = [str(peer), '--appimage-extract-and-run']
        assert json.loads(run(*peer_application, '--candidate-check', user=True).stdout) == check
        assert json.loads(run(*peer_application, '--candidate-status', user=True).stdout) == dict(candidate=contract['build_id'], system='READY')
        run(*peer_application, '--smoke', user=True)
        assert (SYSTEM / 'installed.json').read_bytes() == original_inventory
        run('/usr/bin/python3', '-I', '-c', prefix +
            'from provisioning.chat_client import ChatClient;client=ChatClient();'
            'assert client.invoke("delivery_settings")["background"];client.close()', user=True)
        record('original_appimage_and_deb_same_uid_state_system_no_second_setup')
    else:
        record('appimage_owner_reopens_original_image_not_gui_mount')
        run(*application, '--remove-integration', user=True)
        assert not desktop.exists()
        assert run('systemctl', '--user', 'is-active', 'family-connect-chat.service', user=True, ok=False).returncode != 0
        assert (HOME / '.local/share/family-connect/chat/store').is_dir()
        assert (SYSTEM / 'installed.json').read_bytes() == original_inventory
        image.unlink()
        record('appimage_explicit_removal_preserves_state_and_root_runtime')
    if mode == 'deb':
        run('systemctl', '--user', 'stop', 'family-connect-chat.service', user=True)
    keyring.terminate()
    display.terminate()
    no_vpn()
    record('result', 'PASS')
    print(json.dumps(RESULTS, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
