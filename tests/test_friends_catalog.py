import base64
import json
from pathlib import Path
import pytest
from clients.desktop import profile_config
from provisioning.friends_catalog import verify

fixture=json.loads((Path(__file__).parent/'fixtures/desktop-friends-catalog-v2.json').read_text())

@pytest.mark.parametrize('case', fixture['vectors'], ids=lambda c:c['name'])
def test_shared_catalog_vectors(case):
    def call():
        return verify(case['reply'],base64.b64decode(fixture['anchor']),fixture['device'],case['reply']['country'],base64.b64decode(fixture['wireguard_key']),floor=case['floor'],previous_hash=case.get('previous_hash'))
    if not case['valid']:
        with pytest.raises(ValueError,match='^Invalid Friends configuration$'):call()
        return
    result=call()
    assert result.sequence==2 and result.address==case['reply']['address']
    assert 'DEVICE_CREDENTIAL' not in result.tcp and 'LOCAL_DEVICE_KEY' not in result.awg
    assert fixture['wireguard_key'] not in repr(result)
    # Parsing support must never silently opt older native AWG workers into 3.1.
    with pytest.raises(ValueError):profile_config.parse(result.awg,allow_awg=True)
    assert profile_config.parse(result.awg,allow_awg=True,allow_awg31=True)['Interface']['Address']==result.address

@pytest.mark.parametrize('failure', [None, 'device', 'signature', 'country', 'denied'])
def test_http_configuration_verifies_assignment_before_return(failure):
    import httpx
    import copy
    from device_identity.device import DeviceIdentity
    from provisioning.friends import FriendsClient, FriendsError
    identity=DeviceIdentity.generate()
    reply=copy.deepcopy(fixture['vectors'][0]['reply']);reply['device']=identity.reference
    if failure=='device':reply['device']='0'*32
    if failure=='country':reply['country']='ru'
    if failure=='signature':reply['catalog']['signature']=base64.b64encode(bytes(64)).decode()
    requests=[]
    def route(request):
        requests.append(request.url.path)
        if request.url.path=='/friends/challenge':
            assert json.loads(request.content)['purpose']=='nl'
            return httpx.Response(200,json={'challenge':base64.b64encode(bytes(32)).decode(),'expires_at':1120,'audience':'family-connect/enrollment/v1'})
        assert request.url.path=='/friends/configuration/nl'
        assert json.loads(request.content)['wireguard_public_key']==identity.wireguard_public_key
        return httpx.Response(403 if failure=='denied' else 200,json=reply)
    with httpx.Client(base_url='https://pilot.invalid',transport=httpx.MockTransport(route)) as http:
        client=FriendsClient(http,identity,clock=lambda:1000)
        if failure:
            with pytest.raises(FriendsError,match='^'+('access_rejected' if failure=='denied' else 'invalid_response')+'$'):
                client.configuration('nl',base64.b64decode(fixture['anchor']))
        else:
            response,profile=client.configuration('nl',base64.b64decode(fixture['anchor']))
            assert profile.address=='10.83.0.2/32' and response['device']==identity.reference
        assert len(requests)==2
        with pytest.raises(FriendsError,match='invalid_input'):client.configuration('../ru',base64.b64decode(fixture['anchor']))
        assert len(requests)==2
