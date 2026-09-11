"""Bounded IPv4/TCP header metadata only; never persist packet payload."""
import json,os,socket,struct,subprocess,threading,time

def capture(interface,peer,port,duration,stop):
    rows=[]
    with socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(0x0003)) as sock:
        sock.bind((interface,0));sock.settimeout(.25);end=time.monotonic()+duration
        while time.monotonic()<end and not stop.is_set():
            try:data=sock.recv(65535)
            except socket.timeout:continue
            if len(data)<54 or data[12:14]!=b'\x08\x00':continue
            ip=data[14:];ihl=(ip[0]&15)*4
            if ip[9]!=6 or len(ip)<ihl+20 or struct.unpack('!H',ip[6:8])[0]&0x1fff:continue
            src=socket.inet_ntoa(ip[12:16]);dst=socket.inet_ntoa(ip[16:20])
            tcp=ip[ihl:];sp,dp,seq,ack=struct.unpack('!HHII',tcp[:12]);hlen=(tcp[12]>>4)*4
            if peer not in (src,dst) or port not in (sp,dp):continue
            rows.append(dict(t=time.time(),to_peer=dst==peer,sp=sp,dp=dp,seq=seq,ack=ack,
                flags=tcp[13],length=max(0,struct.unpack('!H',ip[2:4])[0]-ihl-hlen)))
            if len(rows)>=30000:break
    return rows

if __name__=='__main__':
    peer=os.environ['SSH_CONNECTION'].split()[0]
    interface=json.loads(subprocess.check_output(['ip','-j','route','get',peer]))[0]['dev']
    stop=threading.Event();rows=[];control=[]
    def worker():rows.extend(capture(interface,peer,443,115,stop))
    th=threading.Thread(target=worker);th.start()
    print(json.dumps({'ready':True,'time':time.time()}),flush=True)
    try:
        for _ in range(30):
            start=time.time()
            p=subprocess.run(['curl','--disable','--noproxy','*','-sS','--fail','--connect-timeout','3','--max-time','5','-o','/dev/null','-w','%{http_code} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}','https://1.1.1.1/cdn-cgi/trace'],capture_output=True,text=True,timeout=7)
            control.append(dict(t=start,code=p.returncode,timing=p.stdout.split(),error=p.stderr.strip()[:200]));time.sleep(3)
    finally:stop.set();th.join()
    print(json.dumps({'headers':rows,'https':control}),flush=True)
