package roombroker

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"time"

	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/tcpforward"
)

type credentialOffer struct {
	Version   int                            `json:"version"`
	Ready     bool                           `json:"ready"`
	Candidate familysession.RenewalCandidate `json:"candidate"`
}

func credentialMessage(channel io.ReadWriter, send *credentialOffer) (credentialOffer, error) {
	if send != nil {
		raw, err := json.Marshal(send)
		if err != nil {
			return credentialOffer{}, err
		}
		frame := make([]byte, 4+len(raw))
		binary.BigEndian.PutUint32(frame, uint32(len(raw)))
		copy(frame[4:], raw)
		count, err := channel.Write(frame)
		if err != nil || count != len(frame) {
			return credentialOffer{}, io.ErrShortWrite
		}
		return *send, nil
	}
	var header [4]byte
	if _, err := io.ReadFull(channel, header[:]); err != nil {
		return credentialOffer{}, err
	}
	length := binary.BigEndian.Uint32(header[:])
	if length == 0 || length > 1024 {
		return credentialOffer{}, Code("renewal_protocol")
	}
	raw := make([]byte, length)
	if _, err := io.ReadFull(channel, raw); err != nil {
		return credentialOffer{}, err
	}
	var result credentialOffer
	if json.Unmarshal(raw, &result) != nil || result.Version != 1 {
		return credentialOffer{}, Code("renewal_protocol")
	}
	canonical, _ := json.Marshal(result)
	if string(canonical) != string(raw) {
		return credentialOffer{}, Code("renewal_protocol")
	}
	return result, nil
}

func compatibleCandidate(local, remote familysession.RenewalCandidate) bool {
	return local.Generation == remote.Generation && local.CRL == remote.CRL && local.MinimumCRL == remote.MinimumCRL
}

func (binding *leaseBinding) credentialHandler(path string, secured *familysession.Session) func(context.Context, *tcpforward.MuxStream) {
	return func(parent context.Context, stream *tcpforward.MuxStream) {
		ctx, cancel := context.WithTimeout(parent, renewalTimeout)
		defer cancel()
		stop := context.AfterFunc(ctx, func() { stream.Reset() })
		defer stop()
		offer, err := credentialMessage(stream, nil)
		if err != nil {
			return
		}
		raw, err := LoadCredentials(path)
		if err != nil {
			return
		}
		defer clear(raw)
		candidate, err := secured.Candidate(raw)
		ready := err == nil && offer.Ready && compatibleCandidate(candidate, offer.Candidate)
		if ready {
			err = sessionAccess(path, secured)(ctx, func(identity Identity, _ time.Time) error {
				binding.broker.mu.Lock()
				defer binding.broker.unlock()
				if binding.current.ctx.Err() != nil || binding.current.state != Active || identity != binding.current.identity {
					return Code("unauthorized")
				}
				return nil
			})
			ready = err == nil
		}
		if _, err = credentialMessage(stream, &credentialOffer{1, ready, candidate}); err != nil {
			return
		}
		if !ready {
			_, _ = credentialMessage(stream, nil)
			return
		}
		_ = secured.RenewCredentialsGuarded(ctx, stream, raw, binding.credentialGuard(ctx, path))
	}
}

func ExchangeCredentials(parent context.Context, mux *tcpforward.Mux, secured *familysession.Session, raw []byte) (bool, error) {
	candidate, err := secured.Candidate(raw)
	if err != nil {
		return false, nil
	}
	ctx, cancel := context.WithTimeout(parent, renewalTimeout)
	defer cancel()
	stream, err := mux.OpenTCP(ctx, tcpforward.OpenRequest{Host: tcpforward.LeaseRenewalHost, Port: tcpforward.CredentialRenewalPort})
	if err != nil {
		var unsupported *tcpforward.OpenError
		if errors.As(err, &unsupported) && unsupported.Code == "policy_rejected" {
			return false, nil
		}
		return false, err
	}
	defer stream.Reset()
	stop := context.AfterFunc(ctx, func() { stream.Reset() })
	defer stop()
	if _, err = credentialMessage(stream, &credentialOffer{1, true, candidate}); err != nil {
		return false, err
	}
	offer, err := credentialMessage(stream, nil)
	if err != nil {
		return false, err
	}
	if !offer.Ready {
		_, _ = credentialMessage(stream, &credentialOffer{Version: 1})
		return false, nil
	}
	if !compatibleCandidate(candidate, offer.Candidate) {
		return false, Code("renewal_protocol")
	}
	if err = secured.RenewCredentials(ctx, stream, raw); err != nil {
		return false, err
	}
	return true, nil
}
