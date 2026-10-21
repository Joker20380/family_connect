package familysession

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"sync"
	"testing"
	"time"
)

type labTLSPoint struct {
	Level      string
	Connection *stream
	Side       string
	Phase      string
	Data       []byte
	Sequence   uint64
}

func (connection *stream) Write(payload []byte) (int, error) {
	labTLSObserve("tls_write", connection, payload)
	return connection.Conn.Write(payload)
}

func TestLabTLSShortOrigin(test *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	var mutex sync.Mutex
	phase := "handshake"
	var points []labTLSPoint
	labTLSObserve = func(level string, connection *stream, data []byte) {
		mutex.Lock()
		defer mutex.Unlock()
		points = append(points, labTLSPoint{Level: level, Connection: connection, Phase: phase, Data: bytes.Clone(data)})
	}
	defer func() { labTLSObserve = func(string, *stream, []byte) {} }()
	clientEndpoint, serverEndpoint := pair()
	for side, endpoint := range map[string]*endpoint{"client": clientEndpoint, "server": serverEndpoint} {
		endpoint.transform = func(raw []byte) []byte {
			if len(raw) >= 64 && raw[4] == 2 {
				mutex.Lock()
				points = append(points, labTLSPoint{Level: "rs_data", Side: side, Phase: phase, Data: bytes.Clone(raw[64:]), Sequence: binary.BigEndian.Uint64(raw[40:])})
				mutex.Unlock()
			}
			return raw
		}
	}
	clientProfile, serverProfile := profiles(test)
	ready := make(chan *Session, 1)
	failures := make(chan error, 1)
	go func() {
		server, err := Open(ctx, serverEndpoint, encoded(serverProfile), true)
		ready <- server
		failures <- err
	}()
	client, err := Open(ctx, clientEndpoint, encoded(clientProfile), false)
	if err != nil {
		test.Fatal(err)
	}
	server := <-ready
	if err = <-failures; err != nil {
		test.Fatal(err)
	}
	defer client.Close()
	defer server.Close()
	for _, direction := range []string{"client", "server"} {
		sender, receiver := client, server
		if direction == "server" {
			sender, receiver = server, client
		}
		mutex.Lock()
		phase = direction + "_bulk"
		mutex.Unlock()
		completed := make(chan error, 1)
		go func() {
			for index := 0; index < 200; index++ {
				data := bytes.Repeat([]byte{byte(index)}, 16384)
				if err := sender.SendContext(ctx, data); err != nil {
					completed <- err
					return
				}
			}
			completed <- nil
		}()
		for index := 0; index < 200; index++ {
			data, err := receiver.Recv(ctx)
			if err != nil || !bytes.Equal(data, bytes.Repeat([]byte{byte(index)}, 16384)) {
				test.Fatal(direction, index, err)
			}
		}
		if err = <-completed; err != nil {
			test.Fatal(err)
		}
	}
	mutex.Lock()
	snapshot := append([]labTLSPoint(nil), points...)
	mutex.Unlock()
	for _, direction := range []string{"client", "server"} {
		connection := client.stream
		if direction == "server" {
			connection = server.stream
		}
		for _, period := range []string{"handshake", direction + "_bulk"} {
			flattened := map[string][]byte{}
			histograms := map[string]map[int]int{}
			segments := map[string][][]byte{}
			seen := map[uint64]bool{}
			for _, point := range snapshot {
				if point.Phase != period {
					continue
				}
				if point.Level == "rs_data" {
					if point.Side != direction || seen[point.Sequence] {
						continue
					}
					seen[point.Sequence] = true
				} else if point.Connection != connection {
					continue
				}
				if histograms[point.Level] == nil {
					histograms[point.Level] = map[int]int{}
				}
				histograms[point.Level][len(point.Data)]++
				flattened[point.Level] = append(flattened[point.Level], point.Data...)
				segments[point.Level] = append(segments[point.Level], point.Data)
			}
			if !bytes.Equal(flattened["tls_write"], flattened["bridge_read"]) || !bytes.Equal(flattened["tls_write"], flattened["rs_data"]) {
				test.Fatal("ciphertext stream boundary mismatch", direction, period)
			}
			verified22, verified34 := 0, 0
			offset := 0
			boundaries := map[int]int{}
			recordHistograms := map[int]int{}
			cipher := flattened["tls_write"]
			for offset < len(cipher) {
				if len(cipher)-offset < 5 {
					test.Fatal("partial record header")
				}
				size := int(binary.BigEndian.Uint16(cipher[offset+3:offset+5])) + 5
				if offset+size > len(cipher) {
					test.Fatal("partial record")
				}
				boundaries[offset] = size
				recordHistograms[size]++
				offset += size
			}
			offset = 0
			for _, segment := range segments["rs_data"] {
				if len(segment) == 22 && boundaries[offset-16384] == 16406 {
					verified22++
				}
				if len(segment) == 34 && boundaries[offset] == 34 {
					verified34++
				}
				offset += len(segment)
			}
			if period != "handshake" && (verified22 < 180 || verified34 < 180) {
				test.Fatal("steady state not reproduced", verified22, verified34)
			}
			appGroups := [][]int{}
			for _, point := range snapshot {
				if point.Phase != period || point.Connection != connection {
					continue
				}
				if point.Level == "app_plaintext" {
					appGroups = append(appGroups, []int{})
				}
				if point.Level == "tls_write" && len(appGroups) > 0 {
					last := len(appGroups) - 1
					appGroups[last] = append(appGroups[last], len(point.Data))
				}
			}
			matchedGroups := 0
			for _, group := range appGroups {
				if len(group) == 2 && group[0] == 16406 && group[1] == 34 {
					matchedGroups++
				}
			}
			if period != "handshake" && matchedGroups != 195 {
				test.Fatal("application to TLS record correlation failed", matchedGroups)
			}
			result := map[string]any{"direction": direction, "period": period, "histograms": histograms, "record_histograms": recordHistograms, "ciphertext_bytes": len(flattened["tls_write"]), "byte_exact_all_boundaries": true, "verified_tail22": verified22, "verified_record34": verified34, "application_tls_groups": appGroups, "matched_16406_34_groups": matchedGroups, "cipher_suite": client.ConnectionState().CipherSuite}
			encoded, _ := json.Marshal(result)
			fmt.Println("LAB_TLS " + string(encoded))
		}
	}
}
