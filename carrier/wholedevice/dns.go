package wholedevice

import (
	"bytes"
	"context"
	"time"
)

func (session *Session) HandleDNSDatagram(query []byte, host string, port uint16, respond func([]byte) error) {
	if !session.Allow("udp", host, port) || len(query) < 12 || len(query) > 4096 || respond == nil {
		return
	}
	if !session.admitFlow(session.dnsSlots) {
		return
	}
	request := bytes.Clone(query)
	go func() {
		defer session.releaseFlow(session.dnsSlots)
		ctx, cancel := context.WithTimeout(session.ctx, 10*time.Second)
		defer cancel()
		session.Counters.DNS.Add(1)
		answer, err := session.plane.QueryDNS(ctx, request)
		if err == nil && ctx.Err() == nil && len(answer) >= 12 && len(answer) <= 4096 {
			respond(answer)
		}
	}()
}
