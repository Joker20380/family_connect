package qualification

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/netip"
	"net/url"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
)

const packetLimit = 128 << 10

func readFrame(connection io.Reader) ([]byte, error) {
	var header [4]byte
	if _, err := io.ReadFull(connection, header[:]); err != nil {
		return nil, err
	}
	size := binary.BigEndian.Uint32(header[:])
	if size == 0 || size > packetLimit {
		return nil, fmt.Errorf("local packet size")
	}
	packet := make([]byte, size)
	_, err := io.ReadFull(connection, packet)
	return packet, err
}

func writeFrame(connection io.Writer, packet []byte) error {
	if len(packet) == 0 || len(packet) > packetLimit {
		return fmt.Errorf("local packet size")
	}
	var header [4]byte
	binary.BigEndian.PutUint32(header[:], uint32(len(packet)))
	_, err := io.Copy(connection, io.MultiReader(bytes.NewReader(header[:]), bytes.NewReader(packet)))
	return err
}

type Endpoint struct {
	connection     net.Conn
	incoming       chan []byte
	done           chan struct{}
	once           sync.Once
	write          sync.Mutex
	sent, received atomic.Uint64
}

func endpoint(ctx context.Context, connection net.Conn) *Endpoint {
	result := &Endpoint{connection: connection, incoming: make(chan []byte, 64), done: make(chan struct{})}
	stop := context.AfterFunc(ctx, func() { result.Close() })
	go func() {
		defer stop()
		defer result.Close()
		for {
			packet, err := readFrame(connection)
			if err != nil {
				return
			}
			result.received.Add(uint64(len(packet)))
			select {
			case result.incoming <- packet:
			case <-result.done:
				return
			}
		}
	}()
	return result
}

func (channel *Endpoint) Close() error {
	channel.once.Do(func() { close(channel.done); channel.connection.Close() })
	return nil
}

func (channel *Endpoint) SendContext(ctx context.Context, packet []byte) error {
	channel.write.Lock()
	defer channel.write.Unlock()
	if ctx.Err() != nil {
		return ctx.Err()
	}
	deadline, bounded := ctx.Deadline()
	if !bounded || time.Until(deadline) > 5*time.Second {
		deadline = time.Now().Add(5 * time.Second)
	}
	channel.connection.SetWriteDeadline(deadline)
	err := writeFrame(channel.connection, packet)
	if err == nil {
		channel.sent.Add(uint64(len(packet)))
	}
	return err
}

func (channel *Endpoint) Recv(ctx context.Context) ([]byte, error) {
	select {
	case packet := <-channel.incoming:
		return packet, nil
	case <-channel.done:
		return nil, io.EOF
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

func (channel *Endpoint) Stats() telemost.Stats {
	return telemost.Stats{Mode: "isolated-packet", BytesSent: channel.sent.Load(), BytesReceived: channel.received.Load()}
}

type Provider struct{ Address string }

type request struct{ Operation, Room string }

func (provider Provider) request(ctx context.Context, operation, room string) (net.Conn, []byte, error) {
	address, err := netip.ParseAddrPort(provider.Address)
	if err != nil || !address.Addr().IsLoopback() || address.Port() == 0 {
		return nil, nil, fmt.Errorf("loopback relay required")
	}
	connection, err := (&net.Dialer{}).DialContext(ctx, "tcp", provider.Address)
	if err != nil {
		return nil, nil, err
	}
	deadline, bounded := ctx.Deadline()
	if !bounded {
		deadline = time.Now().Add(5 * time.Second)
	}
	connection.SetDeadline(deadline)
	raw, _ := json.Marshal(request{operation, room})
	if err = writeFrame(connection, raw); err == nil {
		raw, err = readFrame(connection)
	}
	if err != nil {
		connection.Close()
		return nil, nil, err
	}
	connection.SetDeadline(time.Time{})
	return connection, raw, nil
}

func (provider Provider) CreateRoom(ctx context.Context) (roombroker.Room, error) {
	connection, raw, err := provider.request(ctx, "create", "")
	if err != nil {
		return roombroker.Room{}, err
	}
	connection.Close()
	var room roombroker.Room
	err = json.Unmarshal(raw, &room)
	return room, err
}

func (provider Provider) Connect(lifetime, ready context.Context, room roombroker.Room) (*Endpoint, error) {
	if !roombroker.ValidJoinURL(room.JoinURL) {
		return nil, fmt.Errorf("local room invalid")
	}
	parsed, _ := url.Parse(room.JoinURL)
	connection, raw, err := provider.request(ready, "join", strings.TrimPrefix(parsed.Path, "/j/"))
	if err != nil {
		return nil, err
	}
	if string(raw) != "joined" {
		connection.Close()
		return nil, fmt.Errorf("local room absent")
	}
	return endpoint(lifetime, connection), nil
}

func (provider Provider) Seed(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
	return provider.Connect(lifetime, ready, room)
}

func (provider Provider) Gateway(lifetime, ready context.Context, room roombroker.Room) (roombroker.GatewayCarrier, error) {
	return provider.Connect(lifetime, ready, room)
}

type relayPeer struct {
	connection net.Conn
	write      sync.Mutex
}

func Relay(ctx context.Context, listener net.Listener) error {
	ctx, cancel := context.WithCancel(ctx)
	var lock sync.Mutex
	var workers sync.WaitGroup
	rooms := map[string]map[*relayPeer]bool{}
	connections := map[net.Conn]bool{}
	stop := context.AfterFunc(ctx, func() {
		listener.Close()
		lock.Lock()
		defer lock.Unlock()
		for connection := range connections {
			connection.Close()
		}
	})
	defer func() {
		cancel()
		listener.Close()
		lock.Lock()
		for connection := range connections {
			connection.Close()
		}
		lock.Unlock()
		workers.Wait()
		stop()
	}()
	for {
		connection, err := listener.Accept()
		if err != nil {
			return err
		}
		lock.Lock()
		connections[connection] = true
		lock.Unlock()
		workers.Add(1)
		go func() {
			defer workers.Done()
			defer connection.Close()
			defer func() { lock.Lock(); delete(connections, connection); lock.Unlock() }()
			connection.SetDeadline(time.Now().Add(5 * time.Second))
			raw, err := readFrame(connection)
			var input request
			if err != nil || len(raw) > 1024 || json.Unmarshal(raw, &input) != nil {
				return
			}
			if input.Operation == "create" {
				var nonce [16]byte
				if _, err := rand.Read(nonce[:]); err != nil {
					return
				}
				identity := hex.EncodeToString(nonce[:])
				lock.Lock()
				if len(rooms) >= 256 {
					lock.Unlock()
					return
				}
				rooms[identity] = map[*relayPeer]bool{}
				lock.Unlock()
				raw, _ := json.Marshal(roombroker.Room{ID: identity, JoinURL: "https://telemost.yandex.ru/j/" + identity})
				writeFrame(connection, raw)
				return
			}
			if input.Operation != "join" {
				return
			}
			peer := &relayPeer{connection: connection}
			lock.Lock()
			room := rooms[input.Room]
			if room == nil || len(room) >= 8 {
				lock.Unlock()
				return
			}
			peer.write.Lock()
			room[peer] = true
			lock.Unlock()
			err = writeFrame(connection, []byte("joined"))
			peer.write.Unlock()
			defer func() { lock.Lock(); delete(room, peer); lock.Unlock() }()
			if err != nil {
				return
			}
			connection.SetDeadline(time.Time{})
			for {
				raw, err := readFrame(connection)
				if err != nil {
					return
				}
				lock.Lock()
				peers := make([]*relayPeer, 0, len(room))
				for other := range room {
					if other != peer {
						peers = append(peers, other)
					}
				}
				lock.Unlock()
				for _, other := range peers {
					other.write.Lock()
					other.connection.SetWriteDeadline(time.Now().Add(5 * time.Second))
					if writeFrame(other.connection, raw) != nil {
						other.connection.Close()
					}
					other.write.Unlock()
				}
			}
		}()
	}
}
