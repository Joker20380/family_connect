package desktopmesh

import (
	"bytes"
	"encoding/hex"
	"strings"
	"testing"
)

func TestAcceptedHealthDNSQueryAndValidation(test *testing.T) {
	query := HealthDNSQuery(0x1234, "fc-"+strings.Repeat("a", 32))
	expected, _ := hex.DecodeString("1234010000010000000000002366632d" + strings.Repeat("61", 32) + "076578616d706c6503636f6d0000010001")
	if !bytes.Equal(query, expected) {
		test.Fatal("health DNS wire changed")
	}
	for _, code := range []byte{0, 3} {
		reply := bytes.Clone(query)
		reply[2], reply[3] = 0x81, 0x80|code
		if !HealthDNSValid(query, reply) {
			test.Fatal("valid no-error/NXDOMAIN response rejected")
		}
		for _, change := range []func([]byte){func(raw []byte) { raw[0] ^= 1 }, func(raw []byte) { raw[2] |= 2 },
			func(raw []byte) { raw[3] = 2 }, func(raw []byte) { raw[5] = 2 }, func(raw []byte) { raw[15] ^= 1 }} {
			bad := bytes.Clone(reply)
			change(bad)
			if HealthDNSValid(query, bad) {
				test.Fatal("malformed health DNS accepted")
			}
		}
		if HealthDNSValid(query, reply[:len(reply)-1]) || HealthDNSValid(query, make([]byte, 1233)) || HealthDNSValid(nil, reply) {
			test.Fatal("unbounded/short health reply accepted")
		}
	}
	for _, label := range []string{"example.com", "fc-" + strings.Repeat("G", 32), "fc-" + strings.Repeat("a", 31)} {
		if HealthDNSQuery(1, label) != nil {
			test.Fatal("invalid health label accepted")
		}
	}
}
