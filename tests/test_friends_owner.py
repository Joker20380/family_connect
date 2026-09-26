import base64,copy,hashlib,json,time
from pathlib import Path
import httpx
import pytest
from provisioning.friends_owner import FriendsOwner
from provisioning.friends import FriendsError
from control.friends.access import Access,Rejected


def test_persisted_owner_activation_configuration_and_restart(tmp_path,monkeypatch):
    fixture=json.loads((Path(__file__).parent/'fixtures/desktop-friends-catalog-v2.json').read_text())
    api=Access(tmp_path/'access.db');api.initialize();invitation=api.invite()
    anchor=tmp_path/'update.pub';anchor.write_text(fixture['anchor'])
    path=tmp_path/'private'/'identity';requests=[];denied=False
    def route(request):
        nonlocal denied
        requests.append(request.url.path);body=json.loads(request.content)
        assert (path/'friends.initialized').is_file() and (path/'wireguard.key').is_file()
        try:
            if request.url.path=='/friends/challenge':return httpx.Response(200,json=api.challenge(**body))
            if request.url.path=='/friends/activate':return httpx.Response(200,json={'device':api.complete(body,'activate')['device'],'status':'active'})
            if request.url.path=='/friends/configuration/nl':
                record=api.complete(body,'nl')
                if denied:return httpx.Response(403)
                reply=copy.deepcopy(fixture['vectors'][0]['reply']);reply['device']=record['device']
                return httpx.Response(200,json=reply)
            raise AssertionError('Unexpected request path')
        except Rejected:return httpx.Response(403)
    factory=lambda:httpx.Client(base_url='https://pilot.invalid',transport=httpx.MockTransport(route))
    owner=FriendsOwner(path,anchor,http_factory=factory);owner.activate(invitation)
    original=(path/'wireguard.key').read_bytes()
    assert owner.register()["status"]=="active"
    first=owner.configuration('nl');assert first.sequence==2
    resumed=FriendsOwner(path,anchor,http_factory=factory)
    assert resumed.configuration('nl').catalog_hash==first.catalog_hash
    assert (path/'wireguard.key').read_bytes()==original
    # Exercise the complete signed HTTP -> persisted cache -> desktop apply path.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'clients/desktop'))
    import backend
    monkeypatch.setattr(backend,'operation_directory',lambda:tmp_path/'operations')
    class Driver(backend.LinuxTCP):
        known=[];live=False;imports=0
        def profiles(self):return [(ident,ident) for ident in self.known]
        def active(self,ident):return self.live
        def import_profile(self,profile):
            # This is a device-specific TCP configuration, never test output.
            assert backend.parse_tcp(Path(profile).read_text())['type']=='vless-reality-v1'
            assert (path/'friends.configuration.json').is_file()
            self.imports+=1;self.known=['fctcp12345678'];return self.known[0]
        def connect(self,ident):self.live=True
        def disconnect(self,ident):self.live=False
        def healthy(self,ident):return self.live
    driver=Driver()
    applied=resumed.connect('nl',driver)
    assert applied==dict(profile='fctcp12345678',country='nl',transport='tcp',sequence=2)
    assert driver.live and driver.imports==1
    cache=(path/'friends.configuration.json').read_bytes();denied=True
    with pytest.raises(FriendsError,match='access_rejected'):resumed.configuration('nl')
    assert (path/'friends.configuration.json').read_bytes()==cache
    with pytest.raises(FriendsError,match='access_rejected'):resumed.connect('nl',driver)
    assert driver.live and driver.imports==1
    count=len(requests);(path/'friends.configuration.json').write_bytes(b'broken')
    with pytest.raises(ValueError):resumed.configuration('nl')
    assert len(requests)==count
