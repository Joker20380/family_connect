package telemost

import (
	"bytes"
	"github.com/pion/webrtc/v4"
)

var (
	// vp8Keepalive is a minimal decodable VP8 keyframe (20 bytes).
	vp8Keepalive = []byte{
		0x30, 0x01, 0x00, 0x9d, 0x01, 0x2a, 0x10, 0x00,
		0x10, 0x00, 0x00, 0x47, 0x08, 0x85, 0x85, 0x88,
		0x99, 0x84, 0x88, 0xfc,
	}
	// vp8Interframe is a minimal decodable VP8 interframe (17 bytes).
	vp8Interframe = []byte{
		0xb1, 0x01, 0x00, 0x08, 0x11, 0x18, 0x00, 0x18,
		0x00, 0x18, 0x58, 0x2f, 0xf4, 0x00, 0x08, 0x00,
		0x00,
	}
)

func encodeVP8DataFrame(fragment []byte) []byte {
	out := make([]byte, 0, len(vp8Interframe)+len(fragment))
	out = append(out, vp8Interframe...)
	out = append(out, fragment...)
	return out
}

// decodeVP8Frame returns the carried fragment for a data frame, or (nil, false)
// for keepalive frames and unrecognised payloads.
func decodeVP8Frame(frame []byte) ([]byte, bool) {
	if len(frame) < 1 {
		return nil, false
	}
	switch frame[0] {
	case vp8Interframe[0]:
		if len(frame) < len(vp8Interframe)+fragmentHeaderLen || len(frame) > len(vp8Interframe)+fragmentHeaderLen+maxFragmentPayload || !bytes.HasPrefix(frame, vp8Interframe) {
			return nil, false
		}
		return frame[len(vp8Interframe):], true
	case vp8Keepalive[0]:
		return nil, false // keepalive / self-echo keyframe
	default:
		return nil, false
	}
}

// newVP8Track creates the local VP8 track published by the carrier.
func newVP8Track() (*webrtc.TrackLocalStaticSample, error) {
	return webrtc.NewTrackLocalStaticSample(
		webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8, ClockRate: 90000},
		"fc-vp8-"+newUUID(),
		"fc-"+newUUID(),
	)
}
