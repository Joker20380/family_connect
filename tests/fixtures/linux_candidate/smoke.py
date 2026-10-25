"""Run exact candidate gates only inside a disposable offline systemd255 container."""
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import time

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


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert Path('/proc/1/comm').read_text().strip() == 'systemd'
    assert os.environ['FC_L032_HOST_NETNS'] != str(Path('/proc/self/ns/net').stat().st_ino)
    assert run('systemctl', '--version').stdout.startswith('systemd 255 ')
    wait(lambda: run('systemctl', 'is-active', 'dbus', 'systemd-resolved', ok=False).stdout.split() == ['active', 'active'])
    no_vpn()
    assert not SYSTEM.exists()
    mode, artifact = sys.argv[1:]
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
    run('systemctl', 'restart', 'polkit')
    assert run(*application, '--setup-system', '/tmp/other-installer', user=True, ok=False).returncode != 0
    assert run(*application, '--setup-system', user=True, uid=1001, ok=False).returncode != 0
    assert not SYSTEM.exists()
    receipt = json.loads(run(*application, '--setup-system', user=True).stdout)
    assert receipt['installed'] and not receipt['service_started']
    assert json.loads(run(*application, '--candidate-status', user=True).stdout)['system'] == 'READY'
    no_vpn()
    second = json.loads(run(*application, '--setup-system', user=True).stdout)
    assert second['installed'] and second['backup'] != receipt['backup']
    assert not list(Path('/tmp').glob('family-connect-user-setup-*'))
    assert not list(Path('/var/tmp').glob('family-connect-root-setup-*'))
    record('explicit_polkit_setup_reinstall_uid_path_and_cleanup', dict(build_id=contract['system']['build_id']))
    damaged = Path('/opt/tampered-user')
    shutil.copytree(root, damaged)
    candidate_record = (damaged / 'candidate.json').read_bytes()
    (damaged / 'candidate.json').unlink()
    refused = run('/usr/bin/python3', '-I', str(damaged / 'launcher.py'), '--smoke', user=True, ok=False)
    assert refused.returncode != 0 and 'candidate.json' in refused.stderr
    (damaged / 'candidate.json').write_bytes(candidate_record)
    (damaged / 'embedded/system.tar.gz').write_bytes(b'tampered')
    assert run('/usr/bin/python3', '-I', str(damaged / 'launcher.py'), '--setup-system', user=True, ok=False).returncode != 0
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
