package desktopmesh

import (
	"bytes"
	"encoding/binary"
	"strings"
)

func HealthDNSQuery(identifier uint16, label string) []byte {
	if len(label) != 35 || !strings.HasPrefix(label, "fc-") {
		return nil
	}
	for _, character := range label[3:] {
		if !(character >= 'a' && character <= 'f' || character >= '0' && character <= '9') {
			return nil
		}
	}
	query := make([]byte, 12, 64)
	binary.BigEndian.PutUint16(query, identifier)
	query[2], query[5] = 1, 1
	for _, part := range []string{label, "example", "com"} {
		query = append(query, byte(len(part)))
		query = append(query, part...)
	}
	return append(query, 0, 0, 1, 0, 1)
}

func HealthDNSValid(query, reply []byte) bool {
	if len(query) < 12 || len(reply) < len(query) || len(reply) > 1232 || !bytes.Equal(query[:2], reply[:2]) {
		return false
	}
	flags := binary.BigEndian.Uint16(reply[2:4])
	code := flags & 15
	return flags&0xfa00 == 0x8000 && (code == 0 || code == 3) && reply[4] == 0 && reply[5] == 1 &&
		bytes.Equal(query[12:], reply[12:len(query)])
}
