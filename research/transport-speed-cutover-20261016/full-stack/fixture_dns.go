package tcpforward

import (
	"context"

	"golang.org/x/net/dns/dnsmessage"
)

func ResearchFixtureDNS(mux *Mux) {
	mux.mu.Lock()
	defer mux.mu.Unlock()
	mux.exchange = func(ctx context.Context, query []byte) ([]byte, error) {
		var message dnsmessage.Message
		if err := message.Unpack(query); err != nil {
			return nil, err
		}
		message.Response = true
		message.Answers = []dnsmessage.Resource{{
			Header: dnsmessage.ResourceHeader{Name: message.Questions[0].Name, Type: dnsmessage.TypeA, Class: dnsmessage.ClassINET, TTL: 60},
			Body:   &dnsmessage.AResource{A: [4]byte{192, 0, 2, 1}},
		}}
		return message.Pack()
	}
}
