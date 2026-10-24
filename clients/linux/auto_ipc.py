"""Fixed, bounded user-to-Auto-service commands; no paths or executables on wire."""
import base64
import re

if __package__:
    from . import mesh_ipc as ipc
else:
    import mesh_ipc as ipc

MAX_REQUEST = 32768
MAX_REPLY = ipc.MAX_REPLY


def require(condition):
    if not condition:
        raise ipc.ProtocolError()


def encoded(value, size=None, maximum=None):
    try:
        require(isinstance(value, str))
        require(len(value) <= 4 * ((maximum or size) + 2) // 3 + 4)
        raw = base64.b64decode(value, validate=True)
        require(base64.b64encode(raw).decode() == value)
        require(len(raw) == size if size is not None else 0 < len(raw) <= maximum)
    except (TypeError, ValueError):
        raise ipc.ProtocolError() from None


def selection(value):
    require(isinstance(value, dict) and set(value) == {'materials', 'preferred'})
    require(value['preferred'] in ('', 'awg', 'tcp'))
    material = value['materials']
    require(isinstance(material, dict) and set(material) == {
        'identity', 'wireguard_private', 'wireguard_public', 'anchor', 'profile', 'country', 'normal_floors'})
    require(material['country'] in ('ru', 'nl') and material['profile'] in ('P0', 'P1'))
    for field, size in (('identity', 64), ('wireguard_private', 32), ('wireguard_public', 32), ('anchor', 32)):
        encoded(material[field], size=size)
    floors = material['normal_floors']
    require(isinstance(floors, list) and len(floors) <= 2)
    for floor in floors:
        catalog(floor)
    return value


def catalog(value):
    require(isinstance(value, dict) and set(value) == {'payload', 'signature'})
    encoded(value['payload'], maximum=8192)
    encoded(value['signature'], size=64)
    return value


def validate_request(value):
    require(isinstance(value, dict) and type(value.get('schema')) is int and value['schema'] == 1)
    require(type(value.get('id')) is int and 0 < value['id'] < 2**63)
    action = value.get('action')
    require(action in ('start', 'status', 'stop', 'catalog'))
    expected = {'schema', 'id', 'action'} | ({'selection'} if action == 'start' else {'generation'} if action == 'stop' else set())
    require(set(value) == expected)
    if action == 'start':
        selection(value['selection'])
    elif action == 'stop':
        require(isinstance(value['generation'], str) and re.fullmatch('[a-f0-9]{32}', value['generation']))
    ipc.encode(value, MAX_REQUEST)
    return value
