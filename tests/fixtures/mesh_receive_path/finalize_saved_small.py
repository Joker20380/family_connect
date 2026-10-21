"""Recover only saved measurement analysis after the seq0 parser error."""

import datetime
import json
import os
import sys

from preserve import ROOT, WORK
from correlate_receive import receive_evidence
from journal import reassemble, performance_lines
from correlate import reconstruct, correlate


def main():
    os.umask(0o077)
    target=WORK/'small'
    assert not (target/'result.json').exists()
    before=json.loads((target/'preflight.json').read_text())
    requests=[json.loads(line) for line in (target/'requests.jsonl').read_text().splitlines()]
    nodes={};errors={}
    rows,join_errors=reassemble((target/'capture/NL-raw.jsonl').read_text().splitlines())
    nodes['NL'],errors['NL']=reconstruct(performance_lines(rows));errors['NL']+=join_errors
    nodes['Android'],errors['Android']=reconstruct((target/'capture/Android-raw.jsonl').read_text().splitlines())
    result=correlate(nodes);result['receive_path']=receive_evidence(nodes)
    result['errors']+=result['receive_path']['errors'];result['parser_errors']=errors
    (target/'correlation-private.json').write_text(json.dumps(result,indent=2))
    both=[value for value in result['logical_data'] if len(value['nodes'])==2 and value['first_submission_observed']
          and value['consumes']==1 and 'new' in value['receive_results']
          and any(item['node']=='NL' and item['kind']=='submission_to_release_ns' for item in value['local_intervals'])]
    sockets=[json.loads(line) for line in (target/'nl-sockets-private.jsonl').read_text().splitlines()]
    matched=sum(bool(item['metrics'].get('remote_ip')) and any(item['metrics']['remote_ip']+':443' in line for row in sockets for line in row['sockets']) for item in requests)
    sys.path.insert(0,str(ROOT/'tests/fixtures/mesh_throughput_trace'))
    from measure import topology
    after=topology()
    cap=any((target/'capture'/(node+'-raw.jsonl')).stat().st_size>=64*1024*1024 for node in nodes)
    summary=dict(small_gate_pass=bool(both and len(requests)==1 and requests[0]['valid'] and matched==1 and
                 not result['errors'] and not any(errors.values()) and not cap and after==before['topology']),
                 two_sided_logical_blocks=len(both),snapshot_counts={node:len(records) for node,records in nodes.items()},
                 parser_error_counts={node:len(value) for node,value in errors.items()},matched_requests=matched,
                 requests=len(requests),parallel=[],source_gateway=json.loads((WORK/'gateway-build.json').read_text())['sha256'],
                 node_invocation=before['nl']['InvocationID'],application_bytes=sum(int(item['metrics'].get('BODY_BYTES',0)) for item in requests),
                 capture=dict(cap_reached=cap,exit_codes=None,stop_evidence='finally completed before local analysis exception'),
                 topology_stable=after==before['topology'],final_topology=after,
                 topology_check_after_analysis_recovery_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 recovery='saved capture only; no additional HTTP',continuous_TUN_observation=False)
    (target/'result.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))


if __name__=='__main__':main()
