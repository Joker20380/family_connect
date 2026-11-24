"""Root-owned timer entry point; never emits the membership list."""
import argparse
from pathlib import Path
import sys
if __name__=='__main__':sys.path.insert(0,'/opt/apps/family_connect/friends-access/app')
from control.capture_gate import Busy, Gate
from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.chat_sync import synchronize
from control.friends.chat_sync import ROOT

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-gate',type=Path)
    args=parser.parse_args(argv)
    try:
        with Gate(args.capture_gate).operation():
            access=Access(ROOT/'access.db')
            snapshot,node=synchronize(ChatAccess(access))
            if (ROOT/'chat-support.json').exists():
                from control.friends.support import publish
                publish(access,ROOT,node)
    except Busy:return 75
    except Exception:return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
