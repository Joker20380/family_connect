import json
import pytest
import RNS
from LXMF.LXMPeer import LXMPeer
from messenger.membership import Membership, validate
from messenger.relay import ClosedRelay


def test_membership_expiry_corruption_and_empty(tmp_path):
    path=tmp_path/'members.json';clock=[1000]
    membership=Membership(path,lambda p,n:p.read_bytes(),clock=lambda:clock[0])
    assert membership.keys()==[]
    key=RNS.Identity().get_public_key()
    value=dict(sequence=1,expires_at=1100,public_keys=[key.hex()])
    path.write_text(json.dumps(value));assert membership.keys()==[key]
    clock[0]=1100;assert membership.keys()==[]
    path.write_text('{');assert membership.keys()==[]
    clock[0]=1000;value['public_keys']=[];path.write_text(json.dumps(value));assert membership.keys()==[]


@pytest.mark.parametrize('patch',[{'sequence':True},{'sequence':0},{'expires_at':1121},
    {'expires_at':1000},{'public_keys':['xx'*64]},{'public_keys':['00'*64]*2}])
def test_bad_snapshot_rejected(patch):
    with pytest.raises(ValueError):validate(dict(sequence=1,expires_at=1100,public_keys=[],**{})|patch,1000)


def test_existing_link_identity_loses_access_after_expiry(tmp_path,chat_runtime):
    static=RNS.Identity();member=RNS.Identity();node=RNS.Identity()
    path=tmp_path/'members.json';clock=[1000]
    path.write_text(json.dumps(dict(sequence=1,expires_at=1100,public_keys=[member.get_public_key().hex()])))
    membership=Membership(path,lambda p,n:p.read_bytes(),clock=lambda:clock[0])
    class Spool:
        def get(self,recipient,data):return []
    relay=ClosedRelay(node,Spool(),allowed_public=[static.get_public_key()],membership=membership)
    try:
        assert relay.respond(LXMPeer.MESSAGE_GET_PATH,[None,None],None,member,0)==[]
        clock[0]=1100
        assert relay.respond(LXMPeer.MESSAGE_GET_PATH,[None,None],None,member,0)==LXMPeer.ERROR_NO_ACCESS
        assert relay.respond(LXMPeer.MESSAGE_GET_PATH,[None,None],None,static,0)==[]
    finally:RNS.Transport.deregister_destination(relay.destination)
