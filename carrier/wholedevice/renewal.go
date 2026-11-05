package wholedevice

import (
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

func (session *Session) startMaintenance(secured *familysession.Session, mux *tcpforward.Mux, setupID string) {
	session.credentials = roombroker.NewSessionMaintenance(session.ctx, mux, secured, setupID, session.Close)
	go session.credentials.Run()
}

func (session *Session) OfferCredentialsWithCommit(raw []byte, committed func()) bool {
	return session.credentials != nil && !session.Failed() && session.credentials.Offer(raw, committed)
}
