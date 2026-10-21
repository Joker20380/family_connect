package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"io"
	"net"
	"testing"
	"time"
)

func TestHostFixtureExactAndBounds(test *testing.T) {
	payload := hostPayload()
	for _, operation := range []byte{'D', 'E', 'U', 'X'} {
		for _, size := range []int{65536, 2 << 20, 4 << 20, (4 << 20) + 1} {
			left, right := net.Pipe()
			done := make(chan error, 1)
			go func() { defer right.Close(); done <- hostFixtureRequest(right, payload) }()
			left.SetDeadline(time.Now().Add(5 * time.Second))
			_, err := left.Write(binary.BigEndian.AppendUint32([]byte{operation}, uint32(size)))
			if err != nil {
				test.Fatal(err)
			}
			valid := operation == 'D' && size <= len(payload) || (operation == 'E' || operation == 'U') && size == 65536
			if valid {
				expected := payload[:size]
				if operation != 'D' {
					if _, err = io.Copy(left, bytes.NewReader(expected)); err != nil {
						test.Fatal(err)
					}
				}
				if operation == 'U' {
					digest := sha256.Sum256(expected)
					expected = digest[:]
				}
				actual, readErr := io.ReadAll(left)
				if readErr != nil || !bytes.Equal(actual, expected) {
					test.Fatal("not exact", readErr)
				}
			}
			left.Close()
			if err = <-done; (err == nil) != valid {
				test.Fatal("fixture bound", operation, size, err)
			}
		}
	}
}

func TestHostFixtureCloseBlockedRead(test *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	listener, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		test.Fatal(err)
	}
	port := listener.Addr().(*net.TCPAddr).Port
	listener.Close()
	stop, err := hostFixture(ctx, port, func(map[string]any) error { return nil })
	if err != nil {
		test.Fatal(err)
	}
	connection, err := net.Dial("tcp4", net.JoinHostPort("127.0.0.1", stringPort(port)))
	if err != nil {
		stop()
		test.Fatal(err)
	}
	defer connection.Close()
	stop()
	connection.SetReadDeadline(time.Now().Add(time.Second))
	if _, err := connection.Read(make([]byte, 1)); err == nil {
		test.Fatal("fixture survived close")
	}
}
