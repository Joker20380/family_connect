"""Generate first pilot credentials on the gateway; files only, no secret stdout."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import uuid

PRIVATE_RANGES=['0.0.0.0/8','10.0.0.0/8','100.64.0.0/10','127.0.0.0/8',
    '169.254.0.0/16','172.16.0.0/12','192.168.0.0/16','198.18.0.0/15',
    '224.0.0.0/4','240.0.0.0/4','::/128','::1/128','fc00::/7','fe80::/10','ff00::/8']

def server_config(identity,private_key,short_id,server_name):
    return {'log':{'loglevel':'none'},'inbounds':[{'listen':'0.0.0.0','port':8443,
        'protocol':'vless','settings':{'clients':[{'id':identity,'flow':'xtls-rprx-vision'}],
        'decryption':'none'},'streamSettings':{'network':'raw','security':'reality',
        'realitySettings':{'show':False,'target':server_name+':443','xver':0,
        'serverNames':[server_name],'privateKey':private_key,'shortIds':[short_id]}}}],
        'outbounds':[{'tag':'internet','protocol':'freedom','settings':{'domainStrategy':'ForceIPv4'}},
            {'tag':'blocked','protocol':'blackhole'}],
        'routing':{'domainStrategy':'IPOnDemand','rules':[
            {'type':'field','ip':PRIVATE_RANGES,'outboundTag':'blocked'},
            {'type':'field','port':'25','outboundTag':'blocked'}]}}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',required=True,type=Path)
    parser.add_argument('--server',required=True)
    parser.add_argument('--server-name',required=True)
    args=parser.parse_args()
    result=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','xray',
        'family-connect-xray:26.3.27-pilot1','x25519'],capture_output=True,text=True,check=True)
    keys=dict(line.split(': ',1) for line in result.stdout.splitlines() if ': ' in line)
    identity=str(uuid.uuid4());short_id=secrets.token_hex(8)
    config=server_config(identity,keys['PrivateKey'],short_id,args.server_name)
    profile=dict(type='vless-reality-v1',server=args.server,port=443,id=identity,
        public_key=keys['Password (PublicKey)'],server_name=args.server_name,short_id=short_id)
    args.directory.mkdir(mode=0o700) # Never overwrite an existing deployment/key pair.
    for name,data in [('server.json',config),('linux.conf',profile)]:
        fd=os.open(args.directory/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as out:json.dump(data,out)
        os.chown(args.directory/name,65532,65532)
    os.chown(args.directory,65532,65532)

if __name__=='__main__':main()
