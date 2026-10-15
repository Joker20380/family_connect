//go:build fc_messenger_lab

package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"net/netip"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/pion/webrtc/v4"
)

func main() {
	directory := flag.String("directory", "", "synthetic fixture directory")
	mailbox := flag.String("mailbox", "127.0.0.1:38872", "loopback mailbox")
	api := flag.String("api", "127.0.0.1:38873", "loopback HTTPS API")
	flag.Parse()
	services := map[string]netip.AddrPort{}
	for name, value := range map[string]string{"chat-mailbox": *mailbox, "chat-api": *api} {
		address, err := netip.ParseAddrPort(value)
		if err != nil || !address.Addr().IsLoopback() {
			log.Fatal("loopback services required")
		}
		services[name+".family-connect.invalid"] = address
	}
	var lock sync.Mutex
	var cancelActive context.CancelFunc
	var generation int
	http.HandleFunc("/offer", func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != "POST" {
			http.Error(writer, "method", 405)
			return
		}
		var offer webrtc.SessionDescription
		if json.NewDecoder(http.MaxBytesReader(writer, request.Body, 65536)).Decode(&offer) != nil {
			http.Error(writer, "offer", 400)
			return
		}
		lock.Lock()
		if cancelActive != nil {
			cancelActive()
		}
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Hour)
		cancelActive = cancel
		generation++
		id := generation
		lock.Unlock()
		session, peer, err := telemost.MessengerLabPeer(ctx, nil)
		if err != nil {
			cancel()
			http.Error(writer, "peer", 503)
			return
		}
		if err = peer.SetRemoteDescription(offer); err != nil {
			cancel()
			session.Close()
			http.Error(writer, "remote", 400)
			return
		}
		answer, err := telemost.MessengerLabDescription(ctx, peer, false)
		if err != nil {
			cancel()
			session.Close()
			http.Error(writer, "answer", 503)
			return
		}
		go func() {
			defer cancel()
			defer session.Close()
			if err := session.MessengerLabConnected(ctx); err != nil {
				return
			}
			profile, err := os.ReadFile(filepath.Join(*directory, "gateway.json"))
			if err != nil {
				log.Print(err)
				return
			}
			defer clear(profile)
			secured, err := familysession.Open(ctx, session, profile, true)
			if err != nil {
				log.Printf("family %d %v", id, err)
				return
			}
			defer secured.Close()
			mux, err := tcpforward.NewMux(ctx, secured, true, tcpforward.MuxConfig{MaxStreams: 8, Policy: tcpforward.Policy{Services: services}})
			if err != nil {
				log.Print(err)
				return
			}
			defer mux.Close()
			fmt.Printf("carrier_ready generation=%d\n", id)
			stop := context.AfterFunc(ctx, func() { mux.Close() })
			defer stop()
			log.Printf("carrier_done generation=%d %v", id, mux.Wait())
		}()
		writer.Header().Set("Content-Type", "application/json")
		json.NewEncoder(writer).Encode(answer)
	})
	server := &http.Server{Addr: "127.0.0.1:38871", ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 15 * time.Second}
	log.Fatal(server.ListenAndServe())
}
