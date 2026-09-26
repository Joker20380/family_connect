"""Root-owned timer entry point; never emits the membership list."""
import sys
sys.path.insert(0,'/opt/apps/family_connect/friends-access/app')
from control.friends.access import Access
from control.friends.chat import ChatAccess
from control.friends.chat_sync import synchronize

if __name__=='__main__':
    try:synchronize(ChatAccess(Access('/opt/apps/family_connect/friends-access/access.db')))
    except Exception:sys.exit(1)
