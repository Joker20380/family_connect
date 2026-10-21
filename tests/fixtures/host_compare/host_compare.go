package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"io"
	"net"
	"strconv"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

func hostPayload() []byte {
	payload := make([]byte, 4<<20)
	for offset := 0; offset < len(payload); offset += sha256.Size {
		seed := []byte("Family Connect isolated host comparison v1:")
		seed = binary.BigEndian.AppendUint64(seed, uint64(offset/sha256.Size))
		digest := sha256.Sum256(seed)
		copy(payload[offset:], digest[:])
	}
	return payload
}

func hostFixtureRequest(connection net.Conn, payload []byte) error {
	if err := connection.SetDeadline(time.Now().Add(150 * time.Second)); err != nil {
		return err
	}
	header := make([]byte, 5)
	if _, err := io.ReadFull(connection, header); err != nil {
		return err
	}
	size := int(binary.BigEndian.Uint32(header[1:]))
	if size != 65536 && size != 2<<20 && size != 4<<20 {
		return errors.New("fixture size rejected")
	}
	switch header[0] {
	case 'D':
		_, err := io.Copy(connection, bytes.NewReader(payload[:size]))
		return err
	case 'E', 'U':
		if size != 65536 {
			return errors.New("fixture reverse size rejected")
		}
		received := make([]byte, size)
		if _, err := io.ReadFull(connection, received); err != nil {
			return err
		}
		if !bytes.Equal(received, payload[:size]) {
			return errors.New("fixture reverse corruption")
		}
		if header[0] == 'E' {
			_, err := io.Copy(connection, bytes.NewReader(received))
			return err
		}
		digest := sha256.Sum256(received)
		_, err := io.Copy(connection, bytes.NewReader(digest[:]))
		return err
	default:
		return errors.New("fixture operation rejected")
	}
}

func hostFixture(ctx context.Context, port int, emit func(map[string]any) error) (func(), error) {
	listener, err := net.Listen("tcp4", net.JoinHostPort("127.0.0.1", strconv.Itoa(port)))
	if err != nil {
		return nil, err
	}
	ctx, cancel := context.WithCancel(ctx)
	payload := hostPayload()
	var workers sync.WaitGroup
	workers.Add(1)
	go func() {
		defer workers.Done()
		<-ctx.Done()
		listener.Close()
	}()
	workers.Add(1)
	go func() {
		defer workers.Done()
		for index := 0; index < 8; index++ {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			workers.Add(1)
			go func() {
				defer workers.Done()
				defer connection.Close()
				stop := context.AfterFunc(ctx, func() { connection.Close() })
				defer stop()
				err := hostFixtureRequest(connection, payload)
				_ = emit(map[string]any{"event": "host_fixture_result", "passed": err == nil})
			}()
		}
		listener.Close()
	}()
	return func() { cancel(); workers.Wait() }, nil
}

func muxHostCompare(ctx context.Context, mux *tcpforward.Mux, port int, snapshot func() map[string]any, emit func(map[string]any) error) error {
	if port < 1 || port > 65535 {
		return errors.New("fixture port invalid")
	}
	payload := hostPayload()
	phaseStart := time.Now()
	request := func(name string, operation byte, size int) error {
		started := time.Now()
		requestContext, cancel := context.WithTimeout(ctx, 150*time.Second)
		defer cancel()
		stream, err := mux.OpenTCP(requestContext, tcpforward.OpenRequest{Host: "127.0.0.1", Port: port})
		if err != nil {
			_ = emit(map[string]any{"event": "host_request", "name": name, "passed": false, "error": "open", "full_seconds": time.Since(started).Seconds()})
			return err
		}
		stop := context.AfterFunc(requestContext, func() { stream.Close() })
		defer stop()
		defer stream.Close()
		opened := time.Now()
		before := mux.PerformanceSnapshot()
		header := binary.BigEndian.AppendUint32([]byte{operation}, uint32(size))
		_, err = io.Copy(stream, bytes.NewReader(header))
		if err == nil && operation != 'D' {
			_, err = io.Copy(stream, bytes.NewReader(payload[:size]))
		}
		expected := payload[:size]
		if operation == 'U' {
			digest := sha256.Sum256(expected)
			expected = digest[:]
		}
		received := make([]byte, len(expected))
		firstByte := time.Now()
		count := 0
		if err == nil {
			count, err = io.ReadFull(stream, received[:1])
			firstByte = time.Now()
		}
		if err == nil {
			remaining, readErr := io.ReadFull(stream, received[1:])
			count += remaining
			err = readErr
		}
		ended := time.Now()
		if err == nil && !bytes.Equal(received, expected) {
			err = errors.New("byte mismatch")
		}
		digest := sha256.Sum256(received[:count])
		failure := ""
		if err != nil {
			failure = "transfer_or_integrity"
		}
		_ = emit(map[string]any{"event": "host_request", "name": name, "operation": string(operation), "size": size, "received": count, "sha256": hex.EncodeToString(digest[:]), "passed": err == nil, "error": failure, "start_ns": started.Sub(phaseStart).Nanoseconds(), "end_ns": ended.Sub(phaseStart).Nanoseconds(), "full_seconds": ended.Sub(started).Seconds(), "open_seconds": opened.Sub(started).Seconds(), "first_byte_seconds": firstByte.Sub(started).Seconds(), "body_seconds": ended.Sub(firstByte).Seconds(), "stream": stream.Stats(), "mux_before": before, "mux_after": mux.PerformanceSnapshot(), "transport": snapshot()})
		return err
	}
	for _, input := range []struct {
		name      string
		operation byte
		size      int
	}{{"control_echo", 'E', 65536}, {"single", 'D', 4 << 20}} {
		if err := request(input.name, input.operation, input.size); err != nil {
			return err
		}
	}
	completed := make(chan error, 2)
	for index := 0; index < 2; index++ {
		go func() { completed <- request("parallel_"+strconv.Itoa(index), 'D', 2<<20) }()
	}
	var failure error
	for index := 0; index < 2; index++ {
		if err := <-completed; err != nil {
			failure = err
		}
	}
	if failure != nil {
		return failure
	}
	return request("reverse_control", 'U', 65536)
}
