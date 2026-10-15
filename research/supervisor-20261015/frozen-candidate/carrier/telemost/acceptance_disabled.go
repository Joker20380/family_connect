//go:build !seedacceptance || !linux

package telemost

import "github.com/gorilla/websocket"

type acceptanceBoundary struct{}

func (session *Session) researchSignalingBoundary(connection *websocket.Conn) (*websocket.Conn, error) {
	return connection, nil
}
