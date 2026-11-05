package familysession

import (
	"bytes"
	"context"
	"encoding/binary"
	"io"
	"testing"
	"time"
)

type rejectedRenewalChannel struct{ resets, reads, writes int }

func (channel *rejectedRenewalChannel) Read([]byte) (int, error) {
	channel.reads++
	return 0, io.EOF
}
func (channel *rejectedRenewalChannel) Write(raw []byte) (int, error) {
	channel.writes++
	return len(raw), nil
}
func (channel *rejectedRenewalChannel) Reset() error      { channel.resets++; return nil }
func (channel *rejectedRenewalChannel) CloseWrite() error { return nil }
func (channel *rejectedRenewalChannel) Close() error      { return nil }

func TestCredentialRenewalBusyAndExpiredNeverExchange(test *testing.T) {
	for _, fault := range []string{"busy", "expired", "closed"} {
		test.Run(fault, func(test *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			clientProfile, serverProfile := profiles(test)
			client, server := connect(test, ctx, clientProfile, serverProfile)
			defer client.Close()
			defer server.Close()
			switch fault {
			case "busy":
				client.renewMu.Lock()
				defer client.renewMu.Unlock()
			case "expired":
				client.securityMu.Lock()
				client.expiry = time.Now().Add(-time.Second)
				client.securityMu.Unlock()
			case "closed":
				client.Close()
			}
			before := client.SecurityDeadline()
			channel := new(rejectedRenewalChannel)
			if client.RenewCredentials(ctx, channel, encoded(clientProfile)) != ErrRejected || channel.resets != 1 || channel.reads != 0 || channel.writes != 0 {
				test.Fatal("ineligible session started an exchange")
			}
			if !client.SecurityDeadline().Equal(before) {
				test.Fatal("rejected exchange changed the original bound")
			}
		})
	}
}

func TestCredentialRenewalWireBoundsAndCanonicalEncoding(test *testing.T) {
	valid := renewalMessage{Kind: "hello", Hello: &renewalHello{Version: 1, Generation: 1}}
	var frame bytes.Buffer
	if writeRenewal(&frame, valid) != nil {
		test.Fatal("valid frame encoding failed")
	}
	if _, err := readRenewal(bytes.NewReader(frame.Bytes()), "hello"); err != nil {
		test.Fatal("valid frame decoding failed", err)
	}
	for _, fault := range []string{"empty", "oversize", "truncated", "unknown-field", "duplicate-field", "wrong-kind", "hello-proof"} {
		test.Run(fault, func(test *testing.T) {
			raw := bytes.Clone(frame.Bytes())
			switch fault {
			case "empty":
				binary.BigEndian.PutUint32(raw, 0)
			case "oversize":
				binary.BigEndian.PutUint32(raw, renewalMaxMessage+1)
			case "truncated":
				raw = raw[:len(raw)-1]
			case "unknown-field", "duplicate-field":
				field := []byte(`"extra":1,`)
				if fault == "duplicate-field" {
					field = []byte(`"kind":"hello",`)
				}
				raw = append(append(bytes.Clone(raw[:5]), field...), raw[5:]...)
				binary.BigEndian.PutUint32(raw, uint32(len(raw)-4))
			case "wrong-kind":
				raw = bytes.Replace(raw, []byte(`"kind":"hello"`), []byte(`"kind":"other"`), 1)
			case "hello-proof":
				raw = append(bytes.Clone(raw[:len(raw)-1]), []byte(`,"proof":"AA=="}`)...)
				binary.BigEndian.PutUint32(raw, uint32(len(raw)-4))
			}
			if _, err := readRenewal(bytes.NewReader(raw), "hello"); err == nil {
				test.Fatal("malformed renewal frame accepted")
			}
		})
	}
}

func FuzzCredentialRenewalFrame(test *testing.F) {
	var frame bytes.Buffer
	writeRenewal(&frame, renewalMessage{Kind: "hello", Hello: &renewalHello{Version: 1, Generation: 1}})
	test.Add(frame.Bytes())
	test.Add([]byte{0xff, 0xff, 0xff, 0xff})
	test.Fuzz(func(test *testing.T, raw []byte) {
		readRenewal(bytes.NewReader(raw), "hello")
	})
}
