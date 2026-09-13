"""Explicit root installation of the opt-in relay broker and one trusted pin.

Run from a reviewed preview; requires its expected helper SHA256. This does not
install/update the desktop client, change VPN routes, or fetch a trust identity.
"""
import argparse
import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import stat

BIN = Path('/usr/local/lib/family-connect-control-route')
CONFIG = Path('/etc/family-connect-control-route/pin.json')
POLICY = Path('/usr/share/polkit-1/actions/org.familyconnect.control-route.policy')


def directory(path):
    if not path.exists():
        directory(path.parent)
        path.mkdir(mode=0o755)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError('unsafe installation directory')


def install(path, content, mode):
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != mode or path.read_bytes() != content:
            raise ValueError('existing installation differs; review migration before replacing')
        return
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(content); stream.flush(); os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider-public', required=True)
    parser.add_argument('--address', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--uid', required=True, type=int)
    parser.add_argument('--helper-sha256', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise ValueError('root required')
    os.umask(0o022)
    key = base64.b64decode(args.provider_public, validate=True)
    address = ipaddress.IPv4Address(args.address)
    if len(key) != 64 or not address.is_global or str(address) != args.address or not 1 <= args.port <= 65535 or args.uid < 1000:
        raise ValueError('invalid explicit provider pin')
    source = Path(__file__).resolve().parents[1]/'clients/linux/control-route-helper.py'
    content = source.read_bytes()
    if hashlib.sha256(content).hexdigest() != args.helper_sha256:
        raise ValueError('helper hash mismatch')
    for path in (BIN, CONFIG.parent, POLICY.parent):
        directory(path)
    config = dict(schema=1, provider=hashlib.sha256(key).hexdigest(), address=args.address,
                  port=args.port, uid=args.uid, priority=10590)
    install(CONFIG, (json.dumps(config, sort_keys=True)+'\n').encode(), 0o600)
    install(BIN/'helper', content, 0o755)
    policy = b'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig><action id="org.familyconnect.control-route">
<description>Lease the trusted Family Connect control route</description>
<message>Authorize access to the trusted relay during VPN configuration</message>
<defaults><allow_any>no</allow_any><allow_inactive>no</allow_inactive><allow_active>auth_admin_keep</allow_active></defaults>
<annotate key="org.freedesktop.policykit.exec.path">/usr/local/lib/family-connect-control-route/helper</annotate>
</action></policyconfig>
'''
    install(POLICY, policy, 0o644)
    print(json.dumps(dict(installed=True, helper_sha256=args.helper_sha256, pin=config)))


if __name__ == '__main__':
    main()
