"""Completion is exact bodies AND matching closed-stream/ACK/ciphertext ledgers."""
import hashlib


def validate(proofs, requests, window):
    assert len(requests)==17 and all(row['passed'] and row['received']==(32 if row['operation']=='U' else row['size']) for row in requests),'CLIENT_BODY_COMPLETION_FAILED'
    payload=b''.join(hashlib.sha256(b'Family Connect isolated host comparison v1:'+index.to_bytes(8,'big')).digest() for index in range((4<<20)//32))
    for request in requests:
        expected=payload[:request['size']]
        if request['operation']=='U':expected=hashlib.sha256(expected).digest()
        assert request['sha256']==hashlib.sha256(expected).hexdigest(),'APPLICATION_SHA256_FAILED'
    for proof in proofs:
        stats=proof['reliability']
        mux=proof['mux']
        assert proof['error']=='<nil>' and not stats['Terminal'] and stats['SendDepth']==0 and stats['DataSent']==stats['Performance']['ReleasedBlocks'],'TWO_END_DRAIN_FAILED'
        assert mux['Window']==window and mux['Opened']==mux['OpenOK']==17 and mux['ActiveStreams']==mux['RetainedBytes']==mux['ActiveSockets']==mux['OpenErrors']==mux['Resets']==mux['ProtocolErrors']==0,'MUX_COMPLETION_FAILED'
    assert proofs[0]['mux']['SentBytes']==proofs[1]['mux']['ReceivedBytes']==131541,'UPSTREAM_BYTES_FAILED'
    assert proofs[1]['mux']['SentBytes']==proofs[0]['mux']['ReceivedBytes']==8454560,'DOWNSTREAM_BYTES_FAILED'
    for sender,receiver in [(proofs[0],proofs[1]),(proofs[1],proofs[0])]:
        first,second=sender['packing'],receiver['packing']
        assert first['QueueBytes']==0 and first['Accepted']==first['Sent']==second['Received'],'PACKER_TAIL_FAILED'
        assert first['InputSHA256']==first['OutputSHA256']==second['ReceiveSHA256'],'CIPHERTEXT_COMPLETION_FAILED'
