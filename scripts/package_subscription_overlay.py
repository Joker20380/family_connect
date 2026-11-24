"""Add subscription reads to a pinned serving HTTP archive, preserving other bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def replace_once(raw, old, new):
    if raw.count(old) != 1:
        raise ValueError('Serving source does not match the reviewed subscription patch')
    return raw.replace(old, new)


def build(baseline, expected_sha256, output):
    raw = baseline.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Serving archive pin mismatch')
    with zipfile.ZipFile(baseline) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or 'control/friends/subscription.py' in names:
            raise ValueError('Duplicate members or subscription already present')
        members = {name: archive.read(name) for name in names}
        access = replace_once(members['control/friends/access.py'],
                              b"('activate','status','support',",
                              b"('activate','status','subscription','support',")
        handler = members['friends_http.py']
        for old, new in (
            (b'from control.friends.referrals import Referrals,Exhausted,RateLimited\n',
             b'from control.friends.referrals import Referrals,Exhausted,RateLimited\n'
             b'from control.friends.subscription import Unsupported as SubscriptionUnsupported\n'),
            (b"'/friends/device/status','/friends/device/support'",
             b"'/friends/device/status','/friends/device/subscription','/friends/device/support'"),
            (b"   elif self.path=='/friends/device/status':\n    result=access.status(value)\n",
             b"   elif self.path=='/friends/device/status':\n    result=access.status(value)\n"
             b"   elif self.path=='/friends/device/subscription':\n"
             b'    from control.friends.subscription import request\n    result=request(access,value)\n'),
            (b'  except Exhausted:',
             b"  except SubscriptionUnsupported:self.reply(501,{'error':'subscription-unsupported'})\n"
             b'  except Exhausted:'),
        ):
            handler = replace_once(handler, old, new)
        changes = {'friends_http.py': handler, 'control/friends/access.py': access,
                   'control/friends/subscription.py': (ROOT / 'control/friends/subscription.py').read_bytes()}
        for name, content in changes.items():
            compile(content, name, 'exec')
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as candidate:
            for entry in archive.infolist():
                candidate.writestr(entry, changes.get(entry.filename, members[entry.filename]))
            entry = zipfile.ZipInfo('control/friends/subscription.py', date_time=(1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            candidate.writestr(entry, changes[entry.filename])
    return dict(baseline_sha256=expected_sha256, candidate_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                changed={name: hashlib.sha256(content).hexdigest() for name, content in changes.items()},
                unchanged_members=len(names) - 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.baseline, args.expected_sha256, args.output), indent=2))


if __name__ == '__main__':
    main()
