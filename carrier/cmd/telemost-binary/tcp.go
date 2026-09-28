package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/sha256"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type tcpConfig struct {
	Host          string  `json:"host"`
	Port          int     `json:"port"`
	TimeoutMS     int     `json:"timeout_ms"`
	Mode          string  `json:"mode"`
	Bytes         int     `json:"bytes"`
	Seconds       int     `json:"seconds"`
	Mbit          float64 `json:"mbit"`
	Path          string  `json:"path"`
	ExpectedError string  `json:"expected_error"`
}

func readTCPConfig(path string) (tcpConfig, error) {
	var config tcpConfig
	info, err := os.Stat(path)
	if err != nil || !info.Mode().IsRegular() || info.Size() > 2048 {
		return config, errors.New("invalid TCP test configuration")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return config, err
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&config) != nil || decoder.Decode(new(any)) != io.EOF || (config.Mode != "echo" && config.Mode != "https" && config.Mode != "open_error" && config.Mode != "remote_close" && config.Mode != "remote_reset" && config.Mode != "remote_half_close") || config.Bytes < 0 || config.Bytes > 64<<20 || config.Seconds < 0 || config.Seconds > 600 || config.Mbit < 0 || config.Mbit > 1.5 || len(config.Path) > 1024 || strings.ContainsAny(config.Path, "\r\n ") {
		return config, errors.New("invalid TCP test configuration")
	}
	if config.Mode == "echo" && config.Bytes == 0 && config.Seconds == 0 {
		return config, errors.New("empty TCP test")
	}
	if config.Seconds != 0 && config.Mbit == 0 {
		return config, errors.New("sustained TCP requires pacing")
	}
	if config.Mode == "https" && config.Path != "" && !strings.HasPrefix(config.Path, "/") {
		return config, errors.New("invalid HTTPS path")
	}
	return config, nil
}

func tcpProbe(ctx context.Context, session *familysession.Session, path string, snapshot func() map[string]any, emit func(map[string]any) error) error {
	config, err := readTCPConfig(path)
	if err != nil {
		return err
	}
	started := time.Now()
	stream, err := tcpforward.OpenTCP(ctx, session, tcpforward.OpenRequest{Host: config.Host, Port: config.Port, TimeoutMS: config.TimeoutMS})
	if err != nil {
		var failure *tcpforward.OpenError
		if errors.As(err, &failure) {
			passed := config.Mode == "open_error" && failure.Code == config.ExpectedError
			_ = emit(map[string]any{"event": "tcp_open_error", "code": failure.Code, "expected": passed})
			if passed {
				return emit(map[string]any{"event": "tcp_result", "status": "PASS", "scenario": "open_error", "transport": snapshot()})
			}
		}
		return errors.New("TCP OPEN failed")
	}
	defer stream.Close()
	stopTCP := tcpMetrics(ctx, stream.Stats, snapshot, emit)
	defer stopTCP()
	_ = emit(map[string]any{"event": "tcp_open", "connect_ms": float64(time.Since(started)) / float64(time.Millisecond)})
	result := map[string]any{"event": "tcp_result", "scenario": config.Mode, "status": "FAIL"}
	if config.Mode == "https" {
		err = tcpHTTPS(ctx, stream, config, result)
	} else if config.Mode == "echo" {
		err = tcpEcho(ctx, stream, config, result)
	} else if config.Mode == "remote_close" || config.Mode == "remote_reset" || config.Mode == "remote_half_close" {
		err = tcpFault(stream, config, result)
	} else {
		err = errors.New("expected OPEN_ERROR")
	}
	closeErr := stream.Close()
	if err == nil {
		err = closeErr
	}
	if err == nil {
		result["status"] = "PASS"
	}
	result["duration_s"] = time.Since(started).Seconds()
	result["stats"], result["transport"] = stream.Stats(), snapshot()
	if emitErr := emit(result); emitErr != nil {
		return emitErr
	}
	return err
}

func tcpMetrics(ctx context.Context, stats func() tcpforward.Stats, snapshot func() map[string]any, emit func(map[string]any) error) func() {
	ctx, cancel := context.WithCancel(ctx)
	done := make(chan struct{})
	var once sync.Once
	go func() {
		defer close(done)
		ticker := time.NewTicker(5 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				if emit(map[string]any{"event": "tcp_sample", "stats": stats(), "transport": snapshot()}) != nil {
					return
				}
			}
		}
	}()
	return func() { once.Do(func() { cancel(); <-done }) }
}

func tcpFault(stream *tcpforward.Stream, config tcpConfig, result map[string]any) error {
	if config.Mode == "remote_reset" {
		if _, err := stream.Write(make([]byte, 1024)); err != nil {
			return err
		}
	}
	payload, err := io.ReadAll(io.LimitReader(stream, 65537))
	if config.Mode == "remote_reset" {
		if !errors.Is(err, tcpforward.ErrReset) {
			return errors.New("remote reset not observed")
		}
		result["remote_reset"] = true
		return nil
	}
	if err != nil || len(payload) != 0 {
		return errors.New("clean EOF not observed")
	}
	if config.Mode == "remote_half_close" {
		if _, err := stream.Write([]byte("after FIN")); err != nil {
			return err
		}
		result["write_after_remote_fin"] = true
	}
	result["remote_eof"] = true
	return stream.CloseWrite()
}

type tcpByteStream interface {
	io.ReadWriteCloser
	CloseWrite() error
}
type tlsStream struct{ tcpByteStream }
type testAddress string

func (address testAddress) Network() string       { return "family-tcp" }
func (address testAddress) String() string        { return string(address) }
func (connection tlsStream) LocalAddr() net.Addr  { return testAddress("client") }
func (connection tlsStream) RemoteAddr() net.Addr { return testAddress("target") }
func (connection tlsStream) SetDeadline(time.Time) error {
	return errors.New("test adapter uses session context deadline")
}
func (connection tlsStream) SetReadDeadline(time.Time) error {
	return errors.New("test adapter uses session context deadline")
}
func (connection tlsStream) SetWriteDeadline(time.Time) error {
	return errors.New("test adapter uses session context deadline")
}

func tcpHTTPS(ctx context.Context, stream tcpByteStream, config tcpConfig, result map[string]any) error {
	secure := tls.Client(tlsStream{stream}, &tls.Config{ServerName: config.Host, MinVersion: tls.VersionTLS12})
	if err := secure.HandshakeContext(ctx); err != nil {
		return errors.New("end-site TLS handshake failed")
	}
	result["end_site_tls_verified"], result["end_site_tls_version"] = true, secure.ConnectionState().Version
	path := config.Path
	if path == "" {
		path = "/"
	}
	request, err := http.NewRequest("GET", "https://"+net.JoinHostPort(config.Host, stringPort(config.Port))+path, nil)
	if err != nil {
		return errors.New("HTTPS request invalid")
	}
	request.Close = true
	if err := request.Write(secure); err != nil {
		return err
	}
	response, err := http.ReadResponse(bufio.NewReaderSize(secure, 16<<10), request)
	if err != nil {
		return errors.New("HTTPS response invalid")
	}
	defer response.Body.Close()
	digest := sha256.New()
	count, err := io.Copy(digest, io.LimitReader(response.Body, 16<<20+1))
	if err != nil || count > 16<<20 {
		return errors.New("HTTPS body truncated or oversized")
	}
	result["http_status"], result["download_bytes"], result["download_sha256"] = response.StatusCode, count, hex.EncodeToString(digest.Sum(nil))
	if response.StatusCode < 200 || response.StatusCode >= 400 {
		return errors.New("HTTPS status not accepted")
	}
	_, err = io.Copy(io.Discard, io.LimitReader(secure, 65537))
	if err != nil {
		return err
	}
	if err := stream.CloseWrite(); err != nil {
		return err
	}
	_, err = io.Copy(io.Discard, io.LimitReader(stream, 65537))
	return err
}

func stringPort(port int) string { encoded, _ := json.Marshal(port); return string(encoded) }

func fillTCP(buffer []byte, offset int64) {
	for index := range buffer {
		position := offset + int64(index)
		buffer[index] = byte(position*31 + position/251)
	}
}

func tcpEcho(ctx context.Context, stream *tcpforward.Stream, config tcpConfig, result map[string]any) error {
	type sentResult struct {
		bytes int64
		hash  string
		err   error
	}
	sent := make(chan sentResult, 1)
	started := time.Now()
	go func() {
		buffer := make([]byte, tcpforward.MaxData)
		digest := sha256.New()
		var total int64
		var err error
		defer func() { sent <- sentResult{total, hex.EncodeToString(digest.Sum(nil)), err} }()
		for (config.Seconds > 0 && time.Since(started) < time.Duration(config.Seconds)*time.Second) || (config.Seconds == 0 && total < int64(config.Bytes)) {
			size := len(buffer)
			if config.Seconds == 0 {
				size = min(size, config.Bytes-int(total))
			}
			fillTCP(buffer[:size], total)
			var count int
			count, err = stream.Write(buffer[:size])
			total += int64(count)
			digest.Write(buffer[:count])
			if err != nil {
				return
			}
			if config.Mbit > 0 {
				delay := time.Until(started.Add(time.Duration(float64(total) * 8 / (config.Mbit * 1e6) * float64(time.Second))))
				if delay > 0 {
					timer := time.NewTimer(delay)
					select {
					case <-timer.C:
					case <-ctx.Done():
						timer.Stop()
						err = ctx.Err()
						return
					}
				}
			}
		}
		err = stream.CloseWrite()
	}()
	var total int64
	digest := sha256.New()
	buffer, expected := make([]byte, 17003), make([]byte, 17003)
	var failure error
	for {
		count, err := stream.Read(buffer)
		if count > 0 {
			fillTCP(expected[:count], total)
			if !bytes.Equal(buffer[:count], expected[:count]) {
				failure = errors.New("TCP byte mismatch")
				break
			}
			total += int64(count)
			digest.Write(buffer[:count])
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			failure = err
			break
		}
	}
	if failure != nil {
		stream.Close()
	}
	write := <-sent
	hash := hex.EncodeToString(digest.Sum(nil))
	result["upload_bytes"], result["download_bytes"] = write.bytes, total
	result["upload_sha256"], result["download_sha256"] = write.hash, hash
	result["transfer_s"], result["useful_bidirectional_mbit"] = time.Since(started).Seconds(), float64(total+write.bytes)*8/time.Since(started).Seconds()/1e6
	result["byte_equal"] = failure == nil && write.err == nil && write.bytes == total && hash == write.hash
	if failure != nil {
		return failure
	}
	if write.err != nil {
		return write.err
	}
	if write.bytes != total || hash != write.hash {
		return errors.New("TCP byte count/hash mismatch")
	}
	return nil
}
