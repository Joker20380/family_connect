package reliablestream

import "encoding/binary"

func DataSequencePrefix(prefix []byte, length uint32) (uint64, bool) {
	if len(prefix) < HeaderSize || string(prefix[:4]) != "FRS1" || prefix[4] != dataFrame || prefix[5] != 0 {
		return 0, false
	}
	payload := uint32(binary.BigEndian.Uint16(prefix[6:8]))
	if payload == 0 || payload > MaxPayload || length != HeaderSize+payload {
		return 0, false
	}
	return binary.BigEndian.Uint64(prefix[40:48]), true
}
