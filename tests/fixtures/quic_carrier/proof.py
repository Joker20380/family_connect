import hashlib
import importlib.util
from lab import ROOT


def validate(proofs, requests, window):
    assert len(requests)==17 and all(row['passed'] and row['received']==(32 if row['operation']=='U' else row['size']) for row in requests),'BODY_OR_COUNT'
    payload=b''.join(hashlib.sha256(b'Family Connect isolated host comparison v1:'+index.to_bytes(8,'big')).digest() for index in range((4<<20)//32))
    for request in requests:
        expected=payload[:request['size']]
        if request['operation']=='U':expected=hashlib.sha256(expected).digest()
        assert request['sha256']==hashlib.sha256(expected).hexdigest(),'BODY_SHA256'
    if 'reliability' in proofs[0]:
        path=ROOT/'tests/fixtures/tls_rs_packing/interaction_proof.py'
        code=path.read_text().replace('==131541',"==sum(5+(row['size'] if row['operation']!='D' else 0) for row in requests)").replace('==8454560',"==sum(row['received'] for row in requests)")
        namespace={};exec(compile(code,str(path),'exec'),namespace);namespace['validate'](proofs,requests,window)
        return
    assert all(proof['error']=='<nil>' for proof in proofs),'QUIC_DRAIN'
    if 'mux' in proofs[0]:
        for proof in proofs:
            mux=proof['mux'];assert mux['Window']==window and mux['Opened']==mux['OpenOK']==17 and mux['ActiveStreams']==mux['RetainedBytes']==mux['ActiveSockets']==mux['OpenErrors']==mux['Resets']==mux['ProtocolErrors']==0,'QS_MUX'
        assert proofs[0]['mux']['SentBytes']==proofs[1]['mux']['ReceivedBytes']==sum(5+(row['size'] if row['operation']!='D' else 0) for row in requests),'QS_UPSTREAM'
        assert proofs[1]['mux']['SentBytes']==proofs[0]['mux']['ReceivedBytes']==sum(row['received'] for row in requests),'QS_DOWNSTREAM'
    else:
        receipts=proofs[1]['receipts'];assert len(receipts)==17,'RECEIPT_COUNT'
        for request in requests:
            receipt=receipts[str(request['stream']['ID'])]
            assert receipt['passed'] and receipt['bytes']==request['received'] and receipt['sha256']==request['sha256'],'RECEIVER_RECEIPT'
