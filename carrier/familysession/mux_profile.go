package familysession

const MuxCredit128Protocol = "family-connect-mux-credit128-v1"

func (session *Session) MuxWindow() (int, error) {
	if session.connection == nil || !session.connection.ConnectionState().HandshakeComplete {
		return 0, ErrRejected
	}
	switch session.connection.ConnectionState().NegotiatedProtocol {
	case Protocol:
		return 65536, nil
	case MuxCredit128Protocol:
		return 131072, nil
	default:
		return 0, ErrRejected
	}
}
