"""Strict pilot profile parsing: one peer, full tunnel, no executable hooks."""
import base64
import ipaddress

MAX_PROFILE=16384
FIELDS={'Interface':{'PrivateKey','Address','DNS','MTU','ListenPort'},
        'Peer':{'PublicKey','PresharedKey','Endpoint','AllowedIPs','PersistentKeepalive'}}


def validate(text):
    if len(text.encode('utf-8'))>MAX_PROFILE or '\x00' in text:
        raise ValueError('Invalid profile size')
    sections={}; current=None
    for raw in text.splitlines():
        line=raw.split('#',1)[0].strip()
        if not line: continue
        if line.startswith('['):
            name=line[1:-1] if line.endswith(']') else ''
            if name not in FIELDS or name in sections: raise ValueError('One interface and one peer required')
            current=sections[name]={}; section=name; continue
        if current is None or '=' not in line: raise ValueError('Invalid profile')
        key,value=map(str.strip,line.split('=',1))
        if key not in FIELDS[section] or key in current or not value: raise ValueError('Unsupported field')
        current[key]=value
    if set(sections)!=set(FIELDS): raise ValueError('Incomplete profile')
    interface,peer=sections['Interface'],sections['Peer']
    for fields,key in [(interface,'PrivateKey'),(peer,'PublicKey')]:
        if len(base64.b64decode(fields.get(key,''),validate=True))!=32: raise ValueError('Invalid key')
    if 'PresharedKey' in peer and len(base64.b64decode(peer['PresharedKey'],validate=True))!=32: raise ValueError('Invalid key')
    if not interface.get('Address') or not interface.get('DNS'): raise ValueError('Address and DNS required')
    for value in interface['Address'].split(','): ipaddress.ip_interface(value.strip())
    for value in interface['DNS'].split(','): ipaddress.ip_address(value.strip())
    routes={str(ipaddress.ip_network(x.strip())) for x in peer.get('AllowedIPs','').split(',')}
    if routes!={'0.0.0.0/0','::/0'}: raise ValueError('Full IPv4 and IPv6 routes required')
    host,port=peer.get('Endpoint','').rsplit(':',1)
    ipaddress.ip_address(host.strip('[]'))
    if not 1<=int(port)<=65535: raise ValueError('Invalid endpoint')
    for field,low,high in [('MTU',1280,1500),('ListenPort',0,65535)]:
        if field in interface and not low<=int(interface[field])<=high: raise ValueError('Invalid interface option')
    if 'PersistentKeepalive' in peer and not 0<=int(peer['PersistentKeepalive'])<=65535: raise ValueError('Invalid keepalive')
    return '\n\n'.join('['+name+']\n'+'\n'.join(k+' = '+v for k,v in fields.items()) for name,fields in sections.items())+'\n'
