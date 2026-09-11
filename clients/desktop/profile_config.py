"""Strict pilot profile parsing: one peer, full tunnel, no executable hooks."""
import base64
import ipaddress
import re
import json
import uuid

MAX_PROFILE=16384
FIELDS={'Interface':{'PrivateKey','Address','DNS','MTU','ListenPort'},
        'Peer':{'PublicKey','PresharedKey','Endpoint','AllowedIPs','PersistentKeepalive'}}


AWG_FIELDS=set("Jc Jmin Jmax S1 S2 S3 S4 H1 H2 H3 H4 I1 I2 I3 I4 I5".split())


def parse_tcp(text):
    """Credential envelope, never arbitrary Xray configuration or executable hooks."""
    if len(text.encode('utf-8')) > MAX_PROFILE: raise ValueError('Oversized TCP profile')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('Duplicate TCP field')
            result[key]=value
        return result
    p=json.loads(text,object_pairs_hook=unique)
    fields={'type','server','port','id','public_key','server_name','short_id'}
    if not isinstance(p,dict) or set(p)!=fields or p['type']!='vless-reality-v1':
        raise ValueError('Unsupported TCP profile')
    if not all(isinstance(p[k],str) for k in fields-{'port'}):raise ValueError('Invalid TCP field')
    if type(p['port']) is not int or not 1<=p['port']<=65535:raise ValueError('Invalid TCP port')
    if str(ipaddress.IPv4Address(p['server']))!=p['server']:raise ValueError('IPv4 gateway required')
    if str(uuid.UUID(p['id']))!=p['id']:raise ValueError('Invalid TCP identity')
    key=p['public_key']
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}',key) or base64.urlsafe_b64encode(base64.urlsafe_b64decode(key+'=')).decode().rstrip('=')!=key:
        raise ValueError('Invalid REALITY public key')
    if not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',p['server_name']) or len(p['server_name'])>253:
        raise ValueError('Invalid REALITY server name')
    if not re.fullmatch(r'(?:[0-9a-f]{2}){1,8}',p['short_id']):raise ValueError('Invalid REALITY short id')
    return p


def tcp_config(profile, interface):
    p=parse_tcp(json.dumps(profile))
    if not re.fullmatch(r'fctcp[0-9a-f]{8}',interface):raise ValueError('Invalid TCP interface')
    return {'log':{'loglevel':'none'},
        'inbounds':[{'tag':'tun','protocol':'tun','settings':{'name':interface,'MTU':1280}}],
        'outbounds':[{'tag':'vpn','protocol':'vless','settings':{'vnext':[{
            'address':p['server'],'port':p['port'],'users':[{'id':p['id'],
            'encryption':'none','flow':'xtls-rprx-vision'}]}]},
            'streamSettings':{'network':'raw','security':'reality',
                'realitySettings':{'fingerprint':'chrome','serverName':p['server_name'],
                    'password':p['public_key'],'shortId':p['short_id']},
                'sockopt':{'mark':64630}}}]}


def parse(text, *, allow_awg=False):
    allowed={k:set(v) for k,v in FIELDS.items()}
    if allow_awg: allowed["Interface"].update(AWG_FIELDS)
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
        if key not in allowed[section] or key in current or not value: raise ValueError('Unsupported field')
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
    if set(interface) & AWG_FIELDS:
        validate_awg(interface)
    return sections


def validate(text, *, allow_awg=False):
    sections=parse(text, allow_awg=allow_awg)
    return '\n\n'.join('['+name+']\n'+'\n'.join(k+' = '+v for k,v in fields.items()) for name,fields in sections.items())+'\n'


def validate_awg(fields):
    required=AWG_FIELDS-{f'I{i}' for i in range(1,6)}
    if not required <= set(fields): raise ValueError('Incomplete AWG 2 profile')
    for name, low, high in [('Jc',0,12),('Jmin',0,1280),('Jmax',0,1280)]+[(f'S{i}',0,256) for i in range(1,5)]:
        if not re.fullmatch(r'[0-9]{1,5}',fields[name]) or not low<=int(fields[name])<=high:
            raise ValueError('Invalid AWG padding')
    if int(fields['Jmin'])>int(fields['Jmax']): raise ValueError('Invalid AWG junk range')
    ranges=[]
    for name in ('H1','H2','H3','H4'):
        if not re.fullmatch(r'[0-9]{1,10}(?:-[0-9]{1,10})?',fields[name]): raise ValueError('Invalid AWG header')
        limits=list(map(int,fields[name].split('-')))
        lo,hi=limits[0],limits[-1]
        if not 5<=lo<=hi<=4294967295 or any(lo<=b and a<=hi for a,b in ranges):
            raise ValueError('Overlapping or invalid AWG headers')
        ranges.append((lo,hi))
    # Strict grammar: no hooks, arbitrary shell text or oversized signature packets.
    for name in (f'I{i}' for i in range(1,6)):
        if name not in fields: continue
        text=fields[name]; pos=0; size=0
        while pos<len(text):
            match=re.match(r'<(?:b 0x([0-9a-fA-F]+)|(r|rd|rc) ([0-9]{1,4})|(t))>',text[pos:])
            if not match: raise ValueError('Invalid AWG signature packet')
            if match[1]:
                if len(match[1])%2: raise ValueError('Invalid AWG bytes')
                size+=len(match[1])//2
            elif match[2]: size+=int(match[3])
            else: size+=4
            pos+=len(match[0])
        if not 1<=size<=1280: raise ValueError('Oversized AWG signature packet')
