"""Windows CI only: local Wintun/VLESS data path, no Internet/default-route changes."""
import hashlib,http.client,http.server,json,os,secrets,subprocess,sys,tempfile,threading,time,uuid
from pathlib import Path
PREFIX='198.18.0.1/32';LOCAL='198.18.0.2';TARGET='198.18.0.1'
def ps(code):
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',"$ErrorActionPreference='Stop'; "+code],capture_output=True,text=True,timeout=30)
    if p.returncode:raise RuntimeError('Windows network operation failed: '+p.stderr[-500:])
    return p.stdout.strip()
def snapshot():
    return ps("Get-NetRoute | Where-Object { $_.DestinationPrefix -in @('0.0.0.0/0','::/0') } | Sort-Object InterfaceIndex,DestinationPrefix,NextHop | Select-Object InterfaceIndex,DestinationPrefix,NextHop,RouteMetric | ConvertTo-Json -Compress")
def adapter(name):
    out=ps("Get-NetAdapter -Name '"+name+"' -IncludeHidden -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ifIndex")
    return int(out) if out else None
def stop(process):
    if process and process.poll() is None:
        process.kill();process.wait(timeout=10)
def main():
    assert sys.platform=='win32' and os.environ.get('GITHUB_ACTIONS')=='true','Isolated Windows CI runner required'
    engine=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]);exe=engine/'xray.exe'
    record=json.loads((engine/'build.json').read_text(encoding='utf-8-sig'))
    for name,digest in record['files'].items():assert hashlib.sha256((engine/name).read_bytes()).hexdigest()==digest
    assert not ps("Get-NetRoute -DestinationPrefix '"+PREFIX+"' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty InterfaceIndex"),'Test route already exists'
    before=snapshot();dns_before=ps('Get-DnsClientServerAddress | Where-Object { $_.ServerAddresses.Count -gt 0 } | Sort-Object InterfaceIndex,AddressFamily | Select-Object InterfaceIndex,AddressFamily,ServerAddresses | ConvertTo-Json -Compress')
    token=secrets.token_hex(16).encode();result={'source':record['xray_revision'],'rounds':[],'default_routes_unchanged':False}
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200);self.send_header('Content-Length',str(len(token)));self.end_headers();self.wfile.write(token)
        def log_message(self,*args):pass
    fixture=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=fixture.serve_forever,daemon=True);thread.start()
    try:
        for iteration in range(2):
            ident='fctcpci'+uuid.uuid4().hex[:8];assert adapter(ident) is None
            server=None;client=None;index=None;row={'iteration':iteration+1,'https':False,'local_http':0,'forced_process_exit':False}
            with tempfile.TemporaryDirectory(prefix='fc-win-tcp-') as folder:
                root=Path(folder);server_port=fixture.server_port+iteration+1
                # Separate temporary VLESS listener; connection readiness is checked below.
                import socket
                with socket.socket() as listener:listener.bind(('127.0.0.1',0));server_port=listener.getsockname()[1]
                client_id=str(uuid.uuid4())
                server_config={'log':{'loglevel':'none'},'inbounds':[{'listen':'127.0.0.1','port':server_port,'protocol':'vless','settings':{'clients':[{'id':client_id}],'decryption':'none'}}],'outbounds':[{'protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(fixture.server_port)}}]}
                client_config={'log':{'loglevel':'none'},'inbounds':[{'protocol':'tun','settings':{'name':ident,'MTU':1280}}],'outbounds':[{'protocol':'vless','settings':{'vnext':[{'address':'127.0.0.1','port':server_port,'users':[{'id':client_id,'encryption':'none'}]}]}}]}
                try:
                    for name,config in [('server',server_config),('client',client_config)]:
                        path=root/(name+'.json');path.write_text(json.dumps(config))
                        p=subprocess.Popen([str(exe),'run','-config',str(path)],cwd=engine,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                        if name=='server':server=p
                        else:client=p
                    until=time.monotonic()+30
                    while time.monotonic()<until:
                        assert server.poll() is None and client.poll() is None,'Engine exited before adapter readiness'
                        index=adapter(ident)
                        if index is not None:break
                        time.sleep(.25)
                    assert index is not None,'No Wintun adapter'
                    ps(f"Set-NetIPInterface -InterfaceIndex {index} -AddressFamily IPv4 -Dhcp Disabled; New-NetIPAddress -InterfaceIndex {index} -IPAddress '{LOCAL}' -PrefixLength 32 -PolicyStore ActiveStore | Out-Null; New-NetRoute -InterfaceIndex {index} -DestinationPrefix '{PREFIX}' -NextHop 0.0.0.0 -PolicyStore ActiveStore | Out-Null")
                    time.sleep(1)
                    assert snapshot()==before,'Default route changed'
                    for _ in range(6):
                        c=http.client.HTTPConnection(TARGET,fixture.server_port,timeout=5,source_address=(LOCAL,0))
                        try:c.request('GET','/');reply=c.getresponse();assert reply.status==200 and reply.read()==token;row['local_http']+=1
                        finally:c.close()
                    # Forced termination exercises cleanup of an actual adapter, not a mock.
                    stop(client);row['forced_process_exit']=True
                finally:
                    if index is not None:
                        ps(f"Get-NetRoute -InterfaceIndex {index} -DestinationPrefix '{PREFIX}' -ErrorAction SilentlyContinue | Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue; Get-NetIPAddress -InterfaceIndex {index} -IPAddress '{LOCAL}' -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue")
                    stop(client);stop(server)
                    for _ in range(20):
                        if adapter(ident) is None:break
                        time.sleep(.25)
                    row['adapter_removed']=adapter(ident) is None;result['rounds'].append(row)
                    assert row['adapter_removed'],'Test adapter remains'
    finally:
        fixture.shutdown();fixture.server_close();thread.join(timeout=3)
        result['default_routes_unchanged']=snapshot()==before
        result['dns_unchanged']=dns_before==ps('Get-DnsClientServerAddress | Where-Object { $_.ServerAddresses.Count -gt 0 } | Sort-Object InterfaceIndex,AddressFamily | Select-Object InterfaceIndex,AddressFamily,ServerAddresses | ConvertTo-Json -Compress')
        result['test_route_absent']=not ps("Get-NetRoute -DestinationPrefix '"+PREFIX+"' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty InterfaceIndex")
        result['passed']=len(result['rounds'])==2 and all(x['local_http']==6 and x['forced_process_exit'] and x['adapter_removed'] for x in result['rounds']) and result['default_routes_unchanged'] and result['dns_unchanged'] and result['test_route_absent']
        output.write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
    assert result['passed']
if __name__=='__main__':main()
