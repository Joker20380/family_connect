"""Root-owned timer entry point; never emits the membership list."""
import sys
sys.path.insert(0,'/opt/apps/family_connect/friends-access/app')
from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.chat_sync import synchronize
from control.friends.chat_sync import ROOT

if __name__=='__main__':
    try:
        access=Access(ROOT/'access.db')
        snapshot,node=synchronize(ChatAccess(access))
        if (ROOT/'chat-support.json').exists():
            from control.friends.support import publish
            publish(access,ROOT,node)
    except Exception:sys.exit(1)
