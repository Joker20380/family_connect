package roombroker

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"net"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
)

const OnlineRenewalContract = "MESH_SAME_HOLDER_ONLINE_V1"

type PublicationReceipt struct {
	Contract string `json:"contract"`
	Gateway  string `json:"gateway"`
	Profile  string `json:"profile_sha256"`
	Instance string `json:"instance"`
}

func ObservePublication(ctx context.Context, socket, path string) (func(), error) {
	if !filepath.IsAbs(socket) {
		return nil, Code("observer_path")
	}
	listener, err := net.Listen("unix", socket)
	if err != nil {
		return nil, err
	}
	if err = os.Chmod(socket, 0600); err != nil {
		listener.Close()
		return nil, err
	}
	var nonce [32]byte
	if _, err = rand.Read(nonce[:]); err != nil {
		listener.Close()
		return nil, err
	}
	instance := hex.EncodeToString(nonce[:])
	var workers sync.WaitGroup
	done := make(chan struct{})
	stop := context.AfterFunc(ctx, func() { listener.Close() })
	go func() {
		defer close(done)
		for {
			connection, err := listener.Accept()
			if err != nil {
				return
			}
			workers.Add(1)
			func() {
				defer workers.Done()
				defer connection.Close()
				connection.SetDeadline(time.Now().Add(5 * time.Second))
				var request struct {
					Candidate *familysession.Credentials `json:"candidate"`
				}
				decoder := json.NewDecoder(io.LimitReader(connection, 65536))
				decoder.DisallowUnknownFields()
				if decoder.Decode(&request) != nil {
					return
				}
				if decoder.Decode(new(any)) != io.EOF {
					return
				}
				raw, err := LoadCredentials(path)
				if err != nil {
					return
				}
				defer clear(raw)
				var current familysession.Credentials
				if json.Unmarshal(raw, &current) != nil {
					return
				}
				if _, _, err := familysession.MuxConfiguration(raw, true, true); err != nil {
					return
				}
				if request.Candidate != nil && familysession.ValidateLocalSuccessor(raw, *request.Candidate) != nil {
					return
				}
				sum := sha256.Sum256(raw)
				json.NewEncoder(connection).Encode(PublicationReceipt{OnlineRenewalContract, current.Gateway, hex.EncodeToString(sum[:]), instance})
			}()
		}
	}()
	return func() { stop(); listener.Close(); <-done; workers.Wait() }, nil
}
