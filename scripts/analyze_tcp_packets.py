import json,statistics
from pathlib import Path
base=Path('/tmp/fc-tcp-packets/results')
c=json.loads((base/'client-headers.json').read_text());srv=json.loads((base/'server.json').read_text());s=srv['headers']
m=json.loads((base/'matched.json').read_text());syns={}
for p in c:
    if p['to_peer'] and p['flags']&0x12==2:syns.setdefault((p['sp'],p['seq']),[]).append(p)
flows=[]
for (port,seq),out in syns.items():
    received=[p for p in s if not p['to_peer'] and p['flags']&0x12==2 and p['seq']==seq]
    sent=[p for p in s if p['to_peer'] and p['flags']&0x12==0x12 and p['ack']==(seq+1)%2**32]
    back=[p for p in c if not p['to_peer'] and p['dp']==port and p['flags']&0x12==0x12 and p['ack']==(seq+1)%2**32]
    row={'client_syns':len(out),'server_syns':len(received),'server_synacks':len(sent),'client_synacks':len(back)}
    if back:row['client_handshake_seconds']=round(back[0]['t']-out[0]['t'],6)
    if received and sent:row['server_response_seconds']=round(sent[0]['t']-received[0]['t'],6)
    if sent:
        ack=[p for p in s if not p['to_peer'] and p['flags']&16 and p['ack']==(sent[0]['seq']+1)%2**32 and p['seq']==(seq+1)%2**32]
        if ack:row['server_ack_seconds']=round(ack[0]['t']-sent[0]['t'],6)
    row['start_relative']=round(out[0]['t']-m['summary'].get('started_wall',out[0]['t']),3)
    flows.append(row)
result={'capture_counts':{'client':len(c),'server':len(s),'client_outgoing':sum(p['to_peer'] for p in c),'server_outgoing':sum(p['to_peer'] for p in s)},'flows':flows,'https':{k:m['summary'][k] for k in ('direct','tun','socks','dns','dns_direct')},'failures':m['summary']['failures'],'server_https':{'passed':sum(p['code']==0 and p['timing'][0]=='200' for p in srv['https']),'total':len(srv['https'])},'cleanup':m['summary']['cleanup']}
(base/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='flows'}))
print('flow count',len(flows),'repeated SYN',sum(p['client_syns']>1 for p in flows),'missing server SYN',sum(not p['server_syns'] for p in flows),'missing client SYNACK',sum(not p['client_synacks'] for p in flows))
print('slow flows',json.dumps([p for p in flows if p.get('client_handshake_seconds',0)>.5 or p['client_syns']>1]))
