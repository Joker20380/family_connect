"""Read-only loopback JSON monitoring; standard library, no outbound telemetry."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import subprocess
import time

UNITS = ('prepare', 'awg', 'tcp', 'mesh', 'snapshot', 'monitoring')


def observe(metadata, *, proc=Path('/proc'), disk=Path('/var/lib/family-connect-rehearsal')):
    memory = {}
    for line in (proc/'meminfo').read_text().splitlines():
        name, value = line.split(':', 1)
        if name in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):
            memory[name] = int(value.split()[0])*1024
    storage = os.statvfs(disk)
    states = {}
    for name in UNITS:
        result = subprocess.run(['systemctl','show','fc-rehearsal-'+name+'.service',
            '--property=ActiveState,SubState,NRestarts'], capture_output=True, text=True, timeout=5)
        values = dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
        states[name] = dict(active=values.get('ActiveState','unknown'), sub=values.get('SubState','unknown'),
                            restarts=int(values.get('NRestarts','0')))
    listeners = []
    for protocol in ('tcp', 'tcp6', 'udp', 'udp6'):
        for line in (proc/'net'/protocol).read_text().splitlines()[1:]:
            fields = line.split()
            if protocol.startswith('tcp') and fields[3] != '0A':
                continue
            listeners.append(dict(protocol=protocol, port=int(fields[1].split(':')[1],16)))
    cpu = [int(value) for value in (proc/'stat').read_text().splitlines()[0].split()[1:]]
    return dict(schema=1, scope='DISPOSABLE_FLEET_REHEARSAL_MONITOR', observed_at=int(time.time()),
        instance_id=metadata['instance_id'], bundle_id=metadata['bundle_id'], revision=metadata['revision'],
        material_expires_at=metadata['material_expires_at'], cpu_ticks=cpu, load=list(os.getloadavg()),
        memory=memory, disk=dict(available_bytes=storage.f_bavail*storage.f_frsize,
        total_bytes=storage.f_blocks*storage.f_frsize, available_inodes=storage.f_favail, total_inodes=storage.f_files),
        uptime_seconds=float((proc/'uptime').read_text().split()[0]), services=states, listeners=listeners)


def server(metadata, port=19727):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/status':
                self.send_error(404)
                return
            try:
                payload = json.dumps(observe(metadata), sort_keys=True, separators=(',',':'), allow_nan=False).encode()
            except Exception:
                payload = b'{"error":"observation_unavailable"}'
                self.send_response(503)
            else:
                self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            pass

    return HTTPServer(('127.0.0.1',port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata', required=True)
    args = parser.parse_args()
    metadata = json.loads(Path(args.metadata).read_bytes())
    with server(metadata) as http:
        http.serve_forever()


if __name__ == '__main__':
    main()
