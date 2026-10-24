import math
import os
from pathlib import Path
import struct
import time
from types import SimpleNamespace

import pytest

from messenger.codec import opus_duration, radio_duration
from provisioning.chat_audio import AudioError, OPUS, RADIO, Player, RadioCodec, Recorder, decode, encode, _element


pytestmark = pytest.mark.skipif(os.environ.get('FC_TEST_LINUX_AUDIO') != '1',
                                reason='explicit Linux GStreamer/Codec2 runtime gate')


def tone(rate, millis=1000, amplitude=6000):
    return b''.join(struct.pack('<h', int(amplitude * math.sin(index * 2 * math.pi * 440 / rate)))
                    for index in range(rate * millis // 1000))


@pytest.mark.parametrize('mode', [OPUS, *RADIO])
def test_real_codecs_accepted_wire_limits_and_playback(mode):
    rate = 16000 if mode == OPUS else 8000
    encoded = encode(tone(rate), mode)
    assert 0 < len(encoded) < 131072
    duration = opus_duration(bytes(encoded)) if mode == OPUS else radio_duration(bytes(encoded), mode)
    assert duration == 1000
    pcm, decoded_rate = decode(encoded, mode)
    assert decoded_rate == rate
    assert len(pcm) == rate * 2
    assert any(pcm)
    player = Player(encoded, mode, sink_factory=lambda: _element('fakesink', sync=True))
    try:
        player.play()
        time.sleep(.1)
        assert player.position()[1]
        player.pause()
        time.sleep(.05)
        paused = player.position()[0]
        time.sleep(.05)
        assert abs(player.position()[0] - paused) < 25
        player.seek(700)
        assert player.paused
        player.pause()
        deadline = time.monotonic() + 3
        while player.position()[1] and time.monotonic() < deadline:
            time.sleep(.02)
        assert player.position() == (1000, False)
    finally:
        player.close()
    assert not player.data and player.pipeline is None


def test_accepted_android_opus_fixture_decodes_with_real_library():
    raw = (Path(__file__).resolve().parents[1] / 'messenger/tests/fixtures/voice-tone.opus').read_bytes()
    pcm, rate = decode(raw, OPUS)
    assert rate == 16000 and len(pcm) == 32000


@pytest.mark.parametrize('mode', RADIO)
def test_radio_padding_normalization_and_maximum(mode):
    codec = RadioCodec()
    raw = tone(8000, 103, 24000)
    peak = max(abs(value[0]) for value in struct.iter_unpack('<h', raw))
    normalized = b''.join(struct.pack('<h', int(value[0] * 8191 / peak)) for value in struct.iter_unpack('<h', raw))
    assert codec.transform(raw, mode) == codec.transform(normalized, mode)
    encoded = encode(raw, mode)
    samples = RADIO[mode][1]
    pcm, _ = decode(encoded, mode)
    assert len(pcm) == ((len(raw) // 2 + samples - 1) // samples) * samples * 2
    with pytest.raises(AudioError):
        encode(bytes(960002), mode)
    with pytest.raises(AudioError):
        codec.transform(bytes(480000 // samples * RADIO[mode][2] + RADIO[mode][2]), mode, decode=True)


def test_capture_is_bounded_and_cancel_wipes_without_queue_or_files():
    recorder = Recorder(OPUS, source_factory=lambda: _element('audiotestsrc', num_buffers=100, samplesperbuffer=160))
    assert recorder.finished.wait(5)
    encoded = recorder.finish()
    assert opus_duration(bytes(encoded)) == 1000 and not recorder.data
    recorder = Recorder(7, source_factory=lambda: _element('audiotestsrc', is_live=True))
    time.sleep(.1)
    assert recorder.finish(cancel=True) is None
    assert recorder.finished.is_set() and not recorder.data and not recorder.thread.is_alive()
    recorder = Recorder(7, source_factory=lambda: _element('audiotestsrc', num_buffers=3100, samplesperbuffer=160))
    assert recorder.finished.wait(10)
    assert len(recorder.data) == 960000
    recorder.finish(cancel=True)


def test_short_or_invalid_recordings_fail_closed():
    recorder = Recorder(OPUS, source_factory=lambda: _element('audiotestsrc', num_buffers=1, samplesperbuffer=160))
    assert recorder.finished.wait(5)
    with pytest.raises(AudioError, match='audio_too_short'):
        recorder.finish()
    assert not recorder.data
    for mode in (True, -1, 0, '16', None):
        with pytest.raises(AudioError):
            encode(bytes(1000), mode)
        with pytest.raises(AudioError):
            decode(bytes(1000), mode)
    for raw in (b'', b'not audio', bytes(131073)):
        with pytest.raises(ValueError):
            decode(raw, OPUS)


def test_output_change_stops_playback_instead_of_rerouting_to_speaker():
    raw = (Path(__file__).resolve().parents[1] / 'messenger/tests/fixtures/voice-tone.opus').read_bytes()
    player = Player(raw, OPUS, sink_factory=lambda: _element('fakesink', sync=True))
    stopped = []
    try:
        player.play()
        player.monitor = SimpleNamespace(get_bus=lambda: SimpleNamespace(pop_filtered=lambda _: True),
                                         stop=lambda: stopped.append(True))
        with pytest.raises(AudioError, match='audio_output_changed'):
            player.position()
        assert stopped == [True] and player.pipeline is None and player.monitor is None
    finally:
        player.close()
