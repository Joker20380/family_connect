package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/binary"
	"errors"
	"net"
	"sync"
	"time"

	"github.com/amnezia-vpn/amneziawg-go/v3/tun"
)

type healthRead struct {
	packet []byte
	err    error
}
type healthRequest struct {
	source [4]byte
	port   uint16
	query  []byte
	answer chan []byte
}
type healthTun struct {
	tun.Device
	done    chan struct{}
	packets chan healthRead
	once    sync.Once
	mu      sync.Mutex
	request *healthRequest
}

func newHealthTun(device tun.Device) *healthTun {
	owned := &healthTun{Device: device, done: make(chan struct{}), packets: make(chan healthRead, 16)}
	go func() {
		buffers := make([][]byte, device.BatchSize())
		sizes := make([]int, len(buffers))
		for index := range buffers {
			buffers[index] = make([]byte, 65535)
		}
		for {
			count, err := device.Read(buffers, sizes, 0)
			for index := 0; index < count; index++ {
				select {
				case owned.packets <- healthRead{packet: bytes.Clone(buffers[index][:sizes[index]])}:
				case <-owned.done:
					return
				}
			}
			if err != nil {
				select {
				case owned.packets <- healthRead{err: err}:
				case <-owned.done:
				}
				return
			}
		}
	}()
	return owned
}

func (owned *healthTun) BatchSize() int { return 1 }
func (owned *healthTun) Read(buffers [][]byte, sizes []int, offset int) (int, error) {
	select {
	case result := <-owned.packets:
		if result.err != nil {
			return 0, result.err
		}
		if len(buffers) == 0 || len(sizes) == 0 || offset < 0 || len(buffers[0])-offset < len(result.packet) {
			return 0, errors.New("health TUN buffer")
		}
		sizes[0] = copy(buffers[0][offset:], result.packet)
		return 1, nil
	case <-owned.done:
		return 0, net.ErrClosed
	}
}

func (owned *healthTun) Write(buffers [][]byte, offset int) (int, error) {
	for index, buffer := range buffers {
		if offset < 0 || offset > len(buffer) {
			return index, errors.New("health TUN offset")
		}
		if owned.consume(buffer[offset:]) {
			continue
		}
		if _, err := owned.Device.Write([][]byte{buffer}, offset); err != nil {
			return index, err
		}
	}
	return len(buffers), nil
}

func (owned *healthTun) consume(packet []byte) bool {
	owned.mu.Lock()
	defer owned.mu.Unlock()
	request := owned.request
	if request == nil || len(packet) < 40 || packet[0] != 0x45 || packet[9] != 17 || binary.BigEndian.Uint16(packet[6:8])&0x3fff != 0 {
		return false
	}
	if int(binary.BigEndian.Uint16(packet[2:4])) != len(packet) || !bytes.Equal(packet[12:16], []byte{1, 1, 1, 1}) || !bytes.Equal(packet[16:20], request.source[:]) {
		return false
	}
	if binary.BigEndian.Uint16(packet[20:22]) != 53 || binary.BigEndian.Uint16(packet[22:24]) != request.port || int(binary.BigEndian.Uint16(packet[24:26])) != len(packet)-20 {
		return false
	}
	answer := packet[28:]
	if len(answer) < len(request.query) || !bytes.Equal(answer[:2], request.query[:2]) || !bytes.Equal(answer[12:len(request.query)], request.query[12:]) {
		return false
	}
	select {
	case request.answer <- bytes.Clone(answer):
	default:
	}
	return true
}

func checksum(packet []byte) uint16 {
	var sum uint32
	for index := 0; index+1 < len(packet); index += 2 {
		sum += uint32(binary.BigEndian.Uint16(packet[index : index+2]))
	}
	if len(packet)%2 != 0 {
		sum += uint32(packet[len(packet)-1]) << 8
	}
	for sum>>16 != 0 {
		sum = (sum & 65535) + (sum >> 16)
	}
	return ^uint16(sum)
}

func (owned *healthTun) query(source string, query []byte, budget time.Duration) []byte {
	address := net.ParseIP(source).To4()
	if address == nil || len(query) < 17 || len(query) > 512 || budget <= 0 || budget > 2500*time.Millisecond {
		return nil
	}
	request := &healthRequest{query: bytes.Clone(query), answer: make(chan []byte, 1)}
	copy(request.source[:], address)
	var random [2]byte
	if _, err := rand.Read(random[:]); err != nil {
		return nil
	}
	request.port = 49152 + binary.BigEndian.Uint16(random[:])%16384
	owned.mu.Lock()
	if owned.request != nil {
		owned.mu.Unlock()
		return nil
	}
	owned.request = request
	owned.mu.Unlock()
	defer func() { owned.mu.Lock(); owned.request = nil; owned.mu.Unlock() }()
	packet := make([]byte, 28+len(query))
	packet[0] = 0x45
	packet[8] = 64
	packet[9] = 17
	binary.BigEndian.PutUint16(packet[2:4], uint16(len(packet)))
	copy(packet[12:16], address)
	copy(packet[16:20], []byte{1, 1, 1, 1})
	binary.BigEndian.PutUint16(packet[10:12], checksum(packet[:20]))
	binary.BigEndian.PutUint16(packet[20:22], request.port)
	binary.BigEndian.PutUint16(packet[22:24], 53)
	binary.BigEndian.PutUint16(packet[24:26], uint16(8+len(query)))
	copy(packet[28:], query)
	ctx, cancel := context.WithTimeout(context.Background(), budget)
	defer cancel()
	select {
	case owned.packets <- healthRead{packet: packet}:
	case <-ctx.Done():
		return nil
	case <-owned.done:
		return nil
	}
	select {
	case answer := <-request.answer:
		return answer
	case <-ctx.Done():
		return nil
	case <-owned.done:
		return nil
	}
}

func (owned *healthTun) Close() error {
	owned.once.Do(func() { close(owned.done) })
	return owned.Device.Close()
}
