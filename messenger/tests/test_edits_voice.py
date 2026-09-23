import os,base64
from pathlib import Path
import pytest
import LXMF
from messenger.local import LocalChat,LocalError
from messenger import codec

@pytest.fixture
def pair(tmp_path,chat_runtime):
    a=LocalChat(tmp_path/'a',os.urandom(32),create=True);b=LocalChat(tmp_path/'b',os.urandom(32),create=True)
    for own,other in ((a,b),(b,a)):
        card=other.profile();own.trust_contact(card['public'],card['fingerprint'])
    yield a,b
    a.close();b.close()

def raw(local,ident):return bytes.fromhex(next(m for m in local._store.messages() if m['id']==ident)['packed'])

def test_edit_out_of_order_ownership_and_notification(pair):
    a,b=pair;address=b.profile()['address'];sender=a.profile()['address']
    ident=a.queue(address,'First');edit=a.edit_message(address,ident,'Second')
    assert b._chat.receive(raw(a,edit));assert b.history(sender)['total']==0
    b._chat.receive(raw(a,ident));history=b.history(sender)
    assert history['total']==1 and history['messages'][0]['text']=='Second' and history['messages'][0]['edited']
    b.mark_inbox([ident],'read');assert b.inbox()[0]['read']
    second=a.edit_message(address,ident,'Third');b._chat.receive(raw(a,second))
    assert b.history(sender)['messages'][0]['text']=='Third' and not b.inbox()[0]['read']
    b.mark_inbox([ident],'read');assert not b._chat.receive(raw(a,second));assert b.inbox()[0]['read']
    with pytest.raises(LocalError):b.edit_message(sender,ident,'Forgery')
    assert a.history(address)['total']==1

def test_other_contact_cannot_edit_or_reset_read(pair,tmp_path):
    a,b=pair;c=LocalChat(tmp_path/'c',os.urandom(32),create=True)
    try:
        card=c.profile();b.trust_contact(card['public'],card['fingerprint']);card=b.profile();c.trust_contact(card['public'],card['fingerprint'])
        ident=a.queue(b.profile()['address'],'Original');b._chat.receive(raw(a,ident));b.mark_inbox([ident],'read')
        forged=c._chat.queue(bytes.fromhex(b.profile()['address']),'Forged',fields={LXMF.FIELD_CUSTOM_DATA:dict(fc=1,type='edit',target=ident,revision=99)})
        b._chat.receive(raw(c,forged));assert b.history(a.profile()['address'])['messages'][0]['text']=='Original';assert b.inbox()[0]['read']
    finally:c.close()

def test_opus_roundtrip_and_bounded_history(pair):
    a,b=pair;voice=(Path(__file__).parent/'fixtures/voice-tone.opus').read_bytes();assert codec.opus_duration(voice)==1000
    ident=a.queue_audio(b.profile()['address'],base64.b64encode(voice).decode());b._chat.receive(raw(a,ident))
    history=b.history(a.profile()['address'])['messages'][0]
    assert history['kind']=='audio' and history['duration_ms']==1000 and 'audio' not in history
    assert base64.b64decode(b.audio(ident)['audio'])==voice
    with pytest.raises(LocalError):a.edit_message(b.profile()['address'],ident,'Caption')
    with pytest.raises(LocalError):a.queue_audio(b.profile()['address'],base64.b64encode(b'not opus').decode())
    with pytest.raises(ValueError):codec.opus_duration(voice[:-1])
    assert not b._chat.receive(raw(a,ident))


def long_voice_fixture():
    import struct
    raw=(Path(__file__).parent/'fixtures/voice-tone.opus').read_bytes();offset=0
    for _ in range(2):
        count=raw[offset+26];offset=offset+27+count+sum(raw[offset+27:offset+27+count])
    prefix=raw[:offset];page=bytearray(raw[offset:]);pages=[]
    for i in range(60):
        copy=bytearray(page);copy[5]=4 if i==59 else 0;copy[6:14]=struct.pack('<Q',(i+1)*48000);copy[18:22]=struct.pack('<I',i+2);copy[22:26]=bytes(4);crc=0
        for byte in copy:
            crc^=byte<<24
            for _ in range(8):crc=((crc<<1)^0x04c11db7 if crc&0x80000000 else crc<<1)&0xffffffff
        copy[22:26]=struct.pack('<I',crc);pages.append(bytes(copy))
    return prefix+b''.join(pages)


def test_long_audio_and_legacy_transfer_budget(tmp_path):
    from messenger.relay import Spool
    voice=long_voice_fixture();assert 70000<len(voice)<codec.MAX_AUDIO;assert codec.opus_duration(voice)==60000
    spool=Spool(tmp_path/'spool')
    try:
        recipient=b'r'*16;blob=recipient+b'x'*len(voice);ident=spool.put(b's'*16,blob)
        assert spool.get(recipient,[[ident],[],48])==[]
        assert spool.get(recipient,[[ident],[],192])==[blob]
    finally:spool.close()


def android_stopped_voice():
    """OggWriter flushes complete pages but does not set EOS on stop()."""
    import struct
    voice = bytearray((Path(__file__).parent/'fixtures/voice-tone.opus').read_bytes())
    offset = 0
    while offset < len(voice):
        start = offset
        count = voice[start+26]
        header = start+27+count
        offset = header+sum(voice[start+27:header])
    page = bytearray(voice[start:])
    page[5] &= ~4
    page[22:26] = bytes(4)
    struct.pack_into('<I', page, 22, codec._ogg_crc(page))
    return bytes(voice[:start])+bytes(page)


def test_android_stopped_voice_is_finalized_before_signed_delivery(pair):
    a, b = pair
    voice = android_stopped_voice()
    with pytest.raises(ValueError):
        codec.opus_duration(voice)
    ident = a.queue_audio(b.profile()['address'], base64.b64encode(voice).decode())
    assert b._chat.receive(raw(a, ident))
    received = base64.b64decode(b.audio(ident)['audio'])
    original = (Path(__file__).parent/'fixtures/voice-tone.opus').read_bytes()
    assert received == original
    assert codec.finalize_recorded_opus(received) == received
    assert b.history(a.profile()['address'])['messages'][0]['duration_ms'] == 1000


def test_recording_finalization_rejects_corrupt_and_truncated_pages():
    voice = android_stopped_voice()
    for invalid in (voice[:-1], voice+b'junk', voice[:80], voice[:-1]+bytes([voice[-1]^1])):
        with pytest.raises(ValueError):
            codec.finalize_recorded_opus(invalid)
