package tcpforward

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

func Serve(ctx context.Context, session *familysession.Session, policy Policy, metrics *Metrics) error {
	if session == nil {
		return familysession.ErrRejected
	}
	var err error
	policy, err = gatewayPolicy(policy)
	if err != nil {
		return err
	}
	if err := session.ClaimTCP(true); err != nil {
		return err
	}
	if metrics == nil {
		metrics = &Metrics{}
	}
	defer func() { metrics.update(func(stats *Stats) { stats.Destination = policy.Metrics.Snapshot() }) }()
	return serve(ctx, session, policy, metrics, net.DefaultResolver, func(ctx context.Context, network, address string) (socket, error) {
		connection, err := (&net.Dialer{KeepAlive: 30 * time.Second}).DialContext(ctx, network, address)
		if err != nil {
			return nil, err
		}
		return connection.(*net.TCPConn), nil
	})
}

func serve(ctx context.Context, endpoint familysession.PacketEndpoint, policy Policy, metrics *Metrics, lookup resolver, dial dialer) (result error) {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	defer endpoint.Close()
	stop := context.AfterFunc(ctx, func() { endpoint.Close() })
	defer stop()
	defer func() {
		metrics.update(func(stats *Stats) {
			if result != nil {
				stats.CloseReason = "failure"
			} else if stats.CloseReason == "" {
				stats.CloseReason = "clean"
			}
		})
	}()
	kind, payload, err := receive(ctx, endpoint)
	if err != nil {
		return err
	}
	metrics.update(func(stats *Stats) { stats.OpenRequests++ })
	var request OpenRequest
	var connection socket
	started := time.Now()
	if kind != openFrame || decodeJSON(payload, &request) != nil {
		err = &OpenError{Code: "malformed_request"}
	} else {
		connection, err = connect(ctx, request, policy, lookup, dial)
	}
	metrics.update(func(stats *Stats) { stats.ConnectMS = float64(time.Since(started)) / float64(time.Millisecond) })
	if err != nil {
		var failure *OpenError
		if !errors.As(err, &failure) {
			failure = &OpenError{Code: "connect_failed"}
		}
		metrics.update(func(stats *Stats) { stats.OpenErrors++; stats.CloseReason = failure.Code })
		body, _ := json.Marshal(failure)
		if sendErr := endpoint.SendContext(ctx, encode(openError, body)); sendErr != nil {
			return sendErr
		}
		waitPeerClose(ctx, endpoint)
		return nil
	}
	metrics.update(func(stats *Stats) { stats.OpenOK++; stats.ActiveSockets = 1 })
	defer func() { connection.Close(); metrics.update(func(stats *Stats) { stats.ActiveSockets = 0 }) }()
	stopSocket := context.AfterFunc(ctx, func() { connection.Close() })
	defer stopSocket()
	if err := endpoint.SendContext(ctx, encode(openOK, nil)); err != nil {
		return err
	}
	reverse := make(chan error, 1)
	readEOF := make(chan struct{})
	go func() {
		err := fromTarget(ctx, endpoint, connection, metrics, readEOF)
		if err != nil {
			metrics.update(func(stats *Stats) { stats.Resets++ })
			_ = boundedControl(endpoint, resetFrame)
			connection.Close()
			timer := time.NewTimer(10 * time.Second)
			select {
			case <-ctx.Done():
			case <-timer.C:
				cancel()
			}
			timer.Stop()
		}
		reverse <- err
	}()
	defer func() { cancel(); connection.Close(); <-reverse }()
	finished := false
	for {
		kind, payload, err = receive(ctx, endpoint)
		if err != nil {
			return err
		}
		switch kind {
		case dataFrame:
			if finished {
				return ErrProtocol
			}
			metrics.update(func(stats *Stats) { stats.DataReceived++ })
			metrics.retain(headerSize + len(payload))
			writeErr := writeTarget(connection, payload, metrics)
			metrics.retain(-headerSize - len(payload))
			if writeErr != nil {
				_ = boundedControl(endpoint, resetFrame)
				return writeErr
			}
		case finFrame:
			if finished {
				return ErrProtocol
			}
			finished = true
			metrics.update(func(stats *Stats) { stats.LocalFIN++ })
			if err := connection.CloseWrite(); err != nil {
				return err
			}
		case closeFrame:
			if !finished {
				return ErrProtocol
			}
			select {
			case <-readEOF:
			default:
				return ErrProtocol
			}
			select {
			case err := <-reverse:
				reverse <- err
				if err != nil {
					return err
				}
			case <-ctx.Done():
				return ctx.Err()
			}
			connection.Close()
			metrics.update(func(stats *Stats) { stats.ActiveSockets = 0 })
			if err := endpoint.SendContext(ctx, encode(closeFrame, nil)); err != nil {
				return err
			}
			waitPeerClose(ctx, endpoint)
			return nil
		case resetFrame:
			metrics.update(func(stats *Stats) { stats.Resets++ })
			return ErrReset
		default:
			return ErrProtocol
		}
	}
}

func waitPeerClose(ctx context.Context, endpoint familysession.PacketEndpoint) {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()
	_, _ = endpoint.Recv(ctx)
}

func fromTarget(ctx context.Context, endpoint familysession.PacketEndpoint, connection socket, metrics *Metrics, readEOF chan struct{}) error {
	buffer := make([]byte, MaxData)
	metrics.retain(MaxData)
	defer metrics.retain(-MaxData)
	for {
		count, err := connection.Read(buffer)
		metrics.update(func(stats *Stats) { stats.TCPReads++ })
		if count > 0 {
			frame := encode(dataFrame, buffer[:count])
			metrics.retain(len(frame))
			sendErr := endpoint.SendContext(ctx, frame)
			metrics.retain(-len(frame))
			if sendErr != nil {
				return sendErr
			}
			metrics.update(func(stats *Stats) { stats.FromTarget += uint64(count); stats.DataSent++ })
		}
		if err == io.EOF {
			close(readEOF)
			metrics.update(func(stats *Stats) { stats.RemoteFIN++; stats.EOFs++ })
			return endpoint.SendContext(ctx, encode(finFrame, nil))
		}
		if err != nil {
			return err
		}
	}
}

func writeTarget(connection io.Writer, payload []byte, metrics *Metrics) error {
	for len(payload) > 0 {
		count, err := connection.Write(payload)
		if count < 0 || count > len(payload) {
			return io.ErrShortWrite
		}
		metrics.update(func(stats *Stats) {
			stats.TCPWrites++
			stats.ToTarget += uint64(count)
			if count < len(payload) {
				stats.PartialWrites++
			}
		})
		payload = payload[count:]
		if err != nil {
			return err
		}
		if count == 0 {
			return io.ErrNoProgress
		}
	}
	return nil
}
