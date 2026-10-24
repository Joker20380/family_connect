"""Bounded Linux voice adapter. Audio stays in memory until encrypted queueing."""
import ctypes
import threading
import time


OPUS = 16
RADIO = {7: (2, 320, 8), 8: (1, 160, 6), 9: (0, 160, 8)}
MAX_MILLIS = 60000
MAX_BYTES = 131072


class AudioError(ValueError):
    pass


def _gst():
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstApp', '1.0')
    from gi.repository import Gst, GstApp
    Gst.init(None)
    return Gst


def _element(name, **properties):
    element = _gst().ElementFactory.make(name)
    if element is None:
        raise AudioError('audio_unavailable')
    for key, value in properties.items():
        element.set_property(key.replace('_', '-'), value)
    return element


def _pipeline(elements):
    pipeline = _gst().Pipeline.new(None)
    for element in elements:
        pipeline.add(element)
    for source, target in zip(elements, elements[1:]):
        if not source.link(target):
            raise AudioError('audio_unavailable')
    return pipeline


def _caps(rate):
    return _gst().Caps.from_string(f'audio/x-raw,format=S16LE,layout=interleaved,channels=1,rate={rate}')


def _sample(sample):
    buffer = sample.get_buffer()
    return buffer.extract_dup(0, buffer.get_size())


def _failure(pipeline):
    gst = _gst()
    message = pipeline.get_bus().pop_filtered(gst.MessageType.ERROR | gst.MessageType.EOS)
    if message is not None and message.type == gst.MessageType.ERROR:
        raise AudioError('audio_failed')
    return message is not None and message.type == gst.MessageType.EOS


def _wipe(value):
    value[:] = bytes(len(value))


class RadioCodec:
    def __init__(self):
        try:
            self.library = ctypes.CDLL('libcodec2.so.1.2')
        except OSError:
            raise AudioError('audio_unavailable') from None
        signatures = {
            'codec2_create': (ctypes.c_void_p, [ctypes.c_int]),
            'codec2_destroy': (None, [ctypes.c_void_p]),
            'codec2_samples_per_frame': (ctypes.c_int, [ctypes.c_void_p]),
            'codec2_bits_per_frame': (ctypes.c_int, [ctypes.c_void_p]),
            'codec2_encode': (None, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]),
            'codec2_decode': (None, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]),
        }
        for name, (result, arguments) in signatures.items():
            function = getattr(self.library, name)
            function.restype, function.argtypes = result, arguments

    def transform(self, raw, mode, *, decode=False):
        if type(mode) is not int or mode not in RADIO:
            raise AudioError('unsupported_codec')
        selected, samples, size = RADIO[mode]
        stride = size if decode else samples * 2
        maximum = 480000 // samples * size if decode else 960000
        if not raw or len(raw) > maximum or (len(raw) % size if decode else len(raw) % 2):
            raise AudioError('invalid_audio_frames')
        handle = self.library.codec2_create(selected)
        if not handle:
            raise AudioError('audio_unavailable')
        source = bytearray(raw)
        pcm = (ctypes.c_short * samples)()
        packed = (ctypes.c_ubyte * size)()
        result = bytearray()
        try:
            if (self.library.codec2_samples_per_frame(handle) != samples or
                    self.library.codec2_bits_per_frame(handle) != size * 8):
                raise AudioError('unsupported_codec')
            if not decode:
                peak = max(abs(int.from_bytes(source[offset:offset + 2], 'little', signed=True))
                           for offset in range(0, len(source), 2))
                if peak > 8191:
                    for offset in range(0, len(source), 2):
                        value = int.from_bytes(source[offset:offset + 2], 'little', signed=True)
                        scaled = (abs(value) * 8191 // peak) * (-1 if value < 0 else 1)
                        source[offset:offset + 2] = scaled.to_bytes(2, 'little', signed=True)
            for offset in range(0, len(source), stride):
                if decode:
                    ctypes.memmove(packed, bytes(source[offset:offset + size]), size)
                    self.library.codec2_decode(handle, pcm, packed)
                    for value in pcm:
                        result.extend(value.to_bytes(2, 'little', signed=True))
                else:
                    for index in range(samples):
                        start = offset + index * 2
                        pcm[index] = int.from_bytes(source[start:start + 2], 'little', signed=True)
                    self.library.codec2_encode(handle, packed, pcm)
                    result.extend(bytes(packed))
            return result
        except Exception:
            _wipe(result)
            raise
        finally:
            _wipe(source)
            ctypes.memset(pcm, 0, ctypes.sizeof(pcm))
            ctypes.memset(packed, 0, ctypes.sizeof(packed))
            self.library.codec2_destroy(handle)


def _convert(raw, *, decode):
    gst = _gst()
    source = _element('appsrc', format=gst.Format.BYTES if decode else gst.Format.TIME)
    sink = _element('appsink', sync=False, max_buffers=4, drop=False)
    if decode:
        source.set_property('caps', gst.Caps.from_string('application/ogg'))
        demux, decoder = _element('oggdemux'), _element('opusdec')
        convert, resample = _element('audioconvert'), _element('audioresample')
        filter_caps = _element('capsfilter', caps=_caps(16000))
        pipeline = _pipeline([decoder, convert, resample, filter_caps, sink])
        pipeline.add(source)
        pipeline.add(demux)
        source.link(demux)
        demux.connect('pad-added', lambda _, pad: pad.link(decoder.get_static_pad('sink')))
    else:
        source.set_property('caps', _caps(16000))
        encoder = _element('opusenc', bitrate=12000, audio_type=2048, frame_size=20)
        pipeline = _pipeline([source, encoder, _element('oggmux'), sink])
    result = bytearray()
    limit = 16000 * 2 * 61 if decode else MAX_BYTES
    try:
        if pipeline.set_state(gst.State.PLAYING) == gst.StateChangeReturn.FAILURE:
            raise AudioError('audio_failed')
        buffer = gst.Buffer.new_wrapped(bytes(raw))
        if not decode:
            buffer.pts = 0
            buffer.duration = len(raw) * gst.SECOND // 32000
        if source.emit('push-buffer', buffer) != gst.FlowReturn.OK:
            raise AudioError('audio_failed')
        source.emit('end-of-stream')
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            sample = sink.emit('try-pull-sample', 100 * gst.MSECOND)
            _failure(pipeline)
            if sample is not None:
                chunk = _sample(sample)
                if len(result) + len(chunk) > limit:
                    raise AudioError('audio_limit')
                result.extend(chunk)
            elif sink.get_property('eos'):
                if not result:
                    raise AudioError('audio_failed')
                return result
        raise AudioError('audio_timeout')
    except Exception:
        _wipe(result)
        raise
    finally:
        pipeline.set_state(gst.State.NULL)


def encode(pcm, mode):
    if type(mode) is not int or mode not in (OPUS, *RADIO):
        raise AudioError('unsupported_codec')
    rate = 16000 if mode == OPUS else 8000
    if not pcm or len(pcm) % 2 or len(pcm) > rate * 2 * 60:
        raise AudioError('audio_limit')
    from messenger.codec import finalize_recorded_opus
    return bytearray(finalize_recorded_opus(bytes(_convert(pcm, decode=False)))) if mode == OPUS else RadioCodec().transform(pcm, mode)


def decode(raw, mode):
    from messenger.codec import opus_duration, radio_duration
    if type(mode) is not int or mode not in (OPUS, *RADIO) or not raw or len(raw) > MAX_BYTES:
        raise AudioError('invalid_audio_frames')
    if mode == OPUS:
        opus_duration(bytes(raw))
        return _convert(raw, decode=True), 16000
    radio_duration(bytes(raw), mode)
    return RadioCodec().transform(raw, mode, decode=True), 8000


class Recorder:
    def __init__(self, mode, *, source_factory=None):
        if type(mode) is not int or mode not in (OPUS, *RADIO):
            raise AudioError('unsupported_codec')
        self.mode = mode
        self.rate = 16000 if mode == OPUS else 8000
        self.data = bytearray()
        self.error = None
        self.stop_event = threading.Event()
        self.discard = False
        self.finished = threading.Event()
        self.started = time.monotonic()
        self.sink = _element('appsink', sync=False, max_buffers=4, drop=False)
        source = source_factory() if source_factory is not None else _element('autoaudiosrc')
        self.pipeline = _pipeline([source, _element('audioconvert'), _element('audioresample'),
                                   _element('capsfilter', caps=_caps(self.rate)), self.sink])
        self.thread = threading.Thread(target=self._capture, name='fc-chat-audio', daemon=True)
        self.thread.start()

    def _capture(self):
        gst = _gst()
        try:
            if self.pipeline.set_state(gst.State.PLAYING) == gst.StateChangeReturn.FAILURE:
                raise AudioError('audio_failed')
            maximum = self.rate * 2 * 60
            while not self.stop_event.is_set() and len(self.data) < maximum:
                sample = self.sink.emit('try-pull-sample', 100 * gst.MSECOND)
                _failure(self.pipeline)
                if sample is not None:
                    self.data.extend(_sample(sample)[:maximum - len(self.data)])
                elif self.sink.get_property('eos'):
                    break
                if time.monotonic() - self.started > 60:
                    break
        except Exception:
            self.error = 'audio_failed'
        finally:
            self.pipeline.set_state(gst.State.NULL)
            if self.discard:
                _wipe(self.data)
                self.data.clear()
            self.finished.set()

    def finish(self, *, cancel=False):
        self.discard = cancel
        self.stop_event.set()
        self.thread.join(2)
        if self.thread.is_alive():
            raise AudioError('audio_timeout')
        try:
            if cancel:
                return None
            if self.error:
                raise AudioError(self.error)
            if len(self.data) < self.rate * 2 * 0.4:
                raise AudioError('audio_too_short')
            return encode(self.data, self.mode)
        finally:
            _wipe(self.data)
            self.data.clear()


class Player:
    def __init__(self, raw, mode, *, sink_factory=None):
        self.data, self.rate = decode(raw, mode)
        self.sink_factory = sink_factory
        self.pipeline = None
        self.monitor = None
        self.offset = 0
        self.paused = False

    @property
    def duration_ms(self):
        return len(self.data) * 1000 // (self.rate * 2)

    def play(self, position_ms=0):
        gst = _gst()
        self.stop()
        self.offset = max(0, min(self.duration_ms, int(position_ms)))
        start = self.offset * self.rate // 1000 * 2
        if start >= len(self.data):
            return
        if self.sink_factory is None:
            self.monitor = gst.DeviceMonitor.new()
            self.monitor.add_filter('Audio/Sink', None)
            if not self.monitor.start():
                self.stop()
                raise AudioError('audio_unavailable')
        source = _element('appsrc', format=gst.Format.TIME, caps=_caps(self.rate))
        sink = self.sink_factory() if self.sink_factory is not None else _element('autoaudiosink')
        self.pipeline = _pipeline([source, _element('audioconvert'), _element('audioresample'), sink])
        self.pipeline.set_state(gst.State.PLAYING)
        buffer = gst.Buffer.new_wrapped(bytes(self.data[start:]))
        buffer.pts = 0
        buffer.duration = (len(self.data) - start) * gst.SECOND // (self.rate * 2)
        if source.emit('push-buffer', buffer) != gst.FlowReturn.OK:
            self.stop()
            raise AudioError('audio_failed')
        source.emit('end-of-stream')
        self.paused = False

    def position(self):
        if self.pipeline is None:
            return self.offset, False
        gst = _gst()
        if self.monitor is not None and self.monitor.get_bus().pop_filtered(
                gst.MessageType.DEVICE_REMOVED | gst.MessageType.DEVICE_CHANGED):
            self.stop()
            raise AudioError('audio_output_changed')
        ended = _failure(self.pipeline)
        success, position = self.pipeline.query_position(gst.Format.TIME)
        current = min(self.duration_ms, self.offset + (position // gst.MSECOND if success else 0))
        if ended:
            self.stop()
            self.offset = self.duration_ms
            return self.duration_ms, False
        return current, True

    def pause(self):
        if self.pipeline is not None:
            self.paused = not self.paused
            self.pipeline.set_state(_gst().State.PAUSED if self.paused else _gst().State.PLAYING)

    def seek(self, position_ms):
        paused = self.paused
        self.play(position_ms)
        if paused:
            self.pause()

    def stop(self):
        if self.pipeline is not None:
            self.pipeline.set_state(_gst().State.NULL)
            self.pipeline = None
        if self.monitor is not None:
            self.monitor.stop()
            self.monitor = None

    def close(self):
        self.stop()
        _wipe(self.data)
        self.data.clear()
