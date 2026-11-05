package familysession

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"encoding/json"
	"encoding/pem"
	"errors"
	"io"
	"time"
)

const renewalDomain = "family-connect/credential-renewal/v1"
const renewalMaxMessage = 8192

var ErrUnchanged = errors.New("credential successor unchanged")

type Authorization struct {
	Generation  uint64
	State       tls.ConnectionState
	Deadline    time.Time
	credentials *renewalState
}

func (authorization Authorization) CheckPolicy(raw []byte, server bool) error {
	if _, _, err := configuration(raw, server, true); err != nil || authorization.credentials == nil {
		return ErrRejected
	}
	next, err := initialRenewalState(raw, authorization.State)
	previous := authorization.credentials
	if err != nil || !compatibleSuccessor(previous, next) {
		return ErrRejected
	}
	if next.verify(previous.local, !server) != nil || next.verify(previous.peer, server) != nil || next.verify(next.local, !server) != nil {
		return ErrRejected
	}
	return nil
}

type RenewalCandidate struct {
	Generation  uint64   `json:"generation"`
	CRL         [32]byte `json:"crl"`
	MinimumCRL  int64    `json:"minimum_crl"`
	Fingerprint [32]byte `json:"-"`
}

type RenewalGuard func(Authorization, func() error) error

type RenewalChannel interface {
	io.ReadWriteCloser
	CloseWrite() error
	Reset() error
}

type renewalState struct {
	profile    Credentials
	local      *x509.Certificate
	peer       *x509.Certificate
	authority  *x509.Certificate
	crl        *x509.RevocationList
	generation uint64
}

type renewalHello struct {
	Version     uint8  `json:"version"`
	Generation  uint64 `json:"generation"`
	Nonce       []byte `json:"nonce"`
	Certificate []byte `json:"certificate"`
	CRL         []byte `json:"crl_sha256"`
	MinimumCRL  int64  `json:"minimum_crl"`
}

type renewalMessage struct {
	Kind  string        `json:"kind"`
	Hello *renewalHello `json:"hello,omitempty"`
	Proof []byte        `json:"proof,omitempty"`
}

func initialRenewalState(raw []byte, connection tls.ConnectionState) (*renewalState, error) {
	var profile Credentials
	if json.Unmarshal(raw, &profile) != nil || len(connection.PeerCertificates) != 1 {
		return nil, ErrRejected
	}
	profile.PrivateKey = ""
	parse := func(value string) (*x509.Certificate, error) {
		block, _ := pem.Decode([]byte(value))
		if block == nil {
			return nil, ErrRejected
		}
		return x509.ParseCertificate(block.Bytes)
	}
	local, err := parse(profile.Certificate)
	if err != nil {
		return nil, ErrRejected
	}
	authority, err := parse(profile.Authority)
	if err != nil {
		return nil, ErrRejected
	}
	block, _ := pem.Decode([]byte(profile.Revocations))
	if block == nil {
		return nil, ErrRejected
	}
	crl, err := x509.ParseRevocationList(block.Bytes)
	if err != nil {
		return nil, ErrRejected
	}
	peer, err := x509.ParseCertificate(connection.PeerCertificates[0].Raw)
	if err != nil {
		return nil, ErrRejected
	}
	return &renewalState{profile: profile, local: local, peer: peer, authority: authority, crl: crl}, nil
}

func (state *renewalState) verify(certificate *x509.Certificate, server bool) error {
	roots := x509.NewCertPool()
	roots.AddCert(state.authority)
	usage := x509.ExtKeyUsageServerAuth
	hostname := "gateway.family-connect.test"
	if server {
		usage, hostname = x509.ExtKeyUsageClientAuth, ""
	}
	if _, err := certificate.Verify(x509.VerifyOptions{Roots: roots, KeyUsages: []x509.ExtKeyUsage{usage}, DNSName: hostname}); err != nil {
		return ErrRejected
	}
	return authorize(certificate, state.profile, state.crl, server)
}

func sameRenewalHolder(previous, next *x509.Certificate) bool {
	return bytes.Equal(previous.RawSubject, next.RawSubject) && bytes.Equal(previous.RawSubjectPublicKeyInfo, next.RawSubjectPublicKeyInfo) &&
		len(previous.URIs) == 1 && len(next.URIs) == 1 && previous.URIs[0].String() == next.URIs[0].String()
}

func (session *Session) prepareRenewal(raw []byte) (*renewalState, ed25519.PrivateKey, time.Time, error) {
	config, _, err := configuration(raw, session.server, true)
	if err != nil {
		return nil, nil, time.Time{}, ErrRejected
	}
	key, ok := config.Certificates[0].PrivateKey.(ed25519.PrivateKey)
	if !ok {
		return nil, nil, time.Time{}, ErrRejected
	}
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	previous := session.renewal
	if previous == nil || previous.generation == ^uint64(0) || !session.securityAlive() {
		return nil, nil, time.Time{}, ErrRejected
	}
	next, err := initialRenewalState(raw, tls.ConnectionState{PeerCertificates: []*x509.Certificate{previous.peer}})
	if err != nil || !compatibleSuccessor(previous, next) {
		return nil, nil, time.Time{}, ErrRejected
	}
	if next.verify(previous.local, !session.server) != nil || next.verify(previous.peer, session.server) != nil || next.verify(next.local, !session.server) != nil {
		return nil, nil, time.Time{}, ErrRejected
	}
	next.generation = previous.generation + 1
	return next, key, session.expiry, nil
}

func compatibleSuccessor(previous, next *renewalState) bool {
	if !bytes.Equal(next.authority.Raw, previous.authority.Raw) ||
		next.profile.Family != previous.profile.Family || next.profile.Gateway != previous.profile.Gateway ||
		next.profile.MinimumRevision != previous.profile.MinimumRevision || next.profile.MinimumCRL < previous.profile.MinimumCRL ||
		!sameRenewalHolder(previous.local, next.local) || next.crl.Number.Cmp(previous.crl.Number) < 0 ||
		next.crl.ThisUpdate.Before(previous.crl.ThisUpdate) || next.crl.NextUpdate.Before(previous.crl.NextUpdate) {
		return false
	}
	if next.crl.Number.Cmp(previous.crl.Number) == 0 && !bytes.Equal(next.crl.Raw, previous.crl.Raw) {
		return false
	}
	for _, entry := range previous.crl.RevokedCertificateEntries {
		found := false
		for _, successor := range next.crl.RevokedCertificateEntries {
			if successor.SerialNumber.Cmp(entry.SerialNumber) == 0 {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	return true
}

func (session *Session) securityAlive() bool {
	if !time.Now().Before(session.expiry) {
		return false
	}
	select {
	case <-session.stream.done:
		return false
	default:
		return true
	}
}

func securityBound(expiry, bound time.Time) time.Time {
	if bound.IsZero() {
		return expiry
	}
	return minTime(expiry, bound)
}

func (session *Session) beginSecurityIO(ctx context.Context, write bool) bool {
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	if ctx.Err() != nil || !session.securityAlive() {
		return false
	}
	bound, _ := ctx.Deadline()
	if write {
		session.writeBound = bound
		return session.connection.SetWriteDeadline(securityBound(session.expiry, bound)) == nil
	}
	session.readBound = bound
	return session.connection.SetReadDeadline(securityBound(session.expiry, bound)) == nil
}

func (session *Session) endSecurityIO(write bool) {
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	if write {
		session.writeBound = time.Time{}
	} else {
		session.readBound = time.Time{}
	}
}

func (session *Session) AuthorizationState() tls.ConnectionState {
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	return session.authorizationLocked().State
}

func (session *Session) authorizationLocked() Authorization {
	return session.authorizationFor(session.renewal, session.expiry)
}

func (session *Session) authorizationFor(next *renewalState, deadline time.Time) Authorization {
	state := session.ConnectionState()
	generation := uint64(0)
	if next != nil {
		peer, _ := x509.ParseCertificate(next.peer.Raw)
		authority, _ := x509.ParseCertificate(next.authority.Raw)
		state.PeerCertificates = []*x509.Certificate{peer}
		state.VerifiedChains = [][]*x509.Certificate{{peer, authority}}
		generation = next.generation
	}
	return Authorization{generation, state, deadline, next}
}

func (session *Session) WithAuthorization(ctx context.Context, use func(Authorization) error) error {
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	if ctx.Err() != nil || !session.securityAlive() {
		return ErrRejected
	}
	return use(session.authorizationLocked())
}

func (session *Session) Candidate(raw []byte) (RenewalCandidate, error) {
	next, key, deadline, err := session.prepareRenewal(raw)
	if err != nil {
		return RenewalCandidate{}, err
	}
	defer clear(key)
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	previous := session.renewal
	if next.generation != previous.generation+1 || !session.securityAlive() {
		return RenewalCandidate{}, ErrRejected
	}
	if bytes.Equal(next.local.Raw, previous.local.Raw) && bytes.Equal(next.crl.Raw, previous.crl.Raw) && next.profile.MinimumCRL == previous.profile.MinimumCRL {
		return RenewalCandidate{}, ErrUnchanged
	}
	if next.local.NotAfter.Before(previous.local.NotAfter) || next.local.NotBefore.Before(previous.local.NotBefore) || !minTime(next.local.NotAfter, next.crl.NextUpdate, next.authority.NotAfter).After(deadline) {
		return RenewalCandidate{}, ErrRejected
	}
	public, _ := json.Marshal(next.profile)
	return RenewalCandidate{next.generation, sha256.Sum256(next.crl.Raw), next.profile.MinimumCRL, sha256.Sum256(public)}, nil
}

func (session *Session) commitRenewal(ctx context.Context, next *renewalState, guard RenewalGuard) error {
	session.securityMu.Lock()
	defer session.securityMu.Unlock()
	previous := session.renewal
	if ctx.Err() != nil || previous == nil || next.generation != previous.generation+1 || !session.securityAlive() ||
		next.verify(previous.local, !session.server) != nil || next.verify(previous.peer, session.server) != nil ||
		next.verify(next.local, !session.server) != nil || next.verify(next.peer, session.server) != nil {
		return ErrRejected
	}
	expiry := minTime(next.local.NotAfter, next.peer.NotAfter, next.crl.NextUpdate, next.authority.NotAfter)
	if !expiry.After(session.expiry) || ctx.Err() != nil || !session.securityAlive() {
		return ErrRejected
	}
	commit := func() error {
		if ctx.Err() != nil || !session.securityAlive() {
			return ErrRejected
		}
		if session.connection.SetReadDeadline(securityBound(expiry, session.readBound)) != nil ||
			session.connection.SetWriteDeadline(securityBound(expiry, session.writeBound)) != nil {
			session.stream.stop()
			return ErrRejected
		}
		session.renewal, session.expiry = next, expiry
		return nil
	}
	if guard != nil {
		return guard(session.authorizationFor(next, expiry), commit)
	}
	return commit()
}

func writeRenewal(channel io.Writer, message renewalMessage) error {
	raw, err := json.Marshal(message)
	if err != nil || len(raw) > renewalMaxMessage {
		return ErrRejected
	}
	frame := make([]byte, 4+len(raw))
	binary.BigEndian.PutUint32(frame, uint32(len(raw)))
	copy(frame[4:], raw)
	count, err := channel.Write(frame)
	if err != nil || count != len(frame) {
		return ErrRejected
	}
	return nil
}

func readRenewal(channel io.Reader, kind string) (renewalMessage, error) {
	var header [4]byte
	if _, err := io.ReadFull(channel, header[:]); err != nil {
		return renewalMessage{}, ErrRejected
	}
	length := binary.BigEndian.Uint32(header[:])
	if length == 0 || length > renewalMaxMessage {
		return renewalMessage{}, ErrRejected
	}
	raw := make([]byte, length)
	if _, err := io.ReadFull(channel, raw); err != nil {
		return renewalMessage{}, ErrRejected
	}
	var message renewalMessage
	if json.Unmarshal(raw, &message) != nil || message.Kind != kind {
		return renewalMessage{}, ErrRejected
	}
	canonical, err := json.Marshal(message)
	if err != nil || !bytes.Equal(raw, canonical) || (kind == "hello") != (message.Hello != nil) ||
		kind == "hello" && len(message.Proof) != 0 || kind != "hello" && len(message.Proof) != ed25519.SignatureSize {
		return renewalMessage{}, ErrRejected
	}
	return message, nil
}

func renewalProof(kind string, transcript []byte) []byte {
	return append([]byte(renewalDomain+"\x00"+kind+"\x00"), transcript...)
}

func (session *Session) RenewCredentials(parent context.Context, channel RenewalChannel, raw []byte) (failure error) {
	return session.RenewCredentialsGuarded(parent, channel, raw, nil)
}

func (session *Session) RenewCredentialsGuarded(parent context.Context, channel RenewalChannel, raw []byte, guard RenewalGuard) (failure error) {
	if channel == nil {
		return ErrRejected
	}
	if !session.renewMu.TryLock() {
		channel.Reset()
		return ErrRejected
	}
	defer session.renewMu.Unlock()
	next, key, originalDeadline, err := session.prepareRenewal(raw)
	if err != nil {
		channel.Reset()
		return ErrRejected
	}
	defer clear(key)
	ctx, cancel := context.WithDeadline(parent, minTime(originalDeadline, time.Now().Add(15*time.Second)))
	defer cancel()
	stop := context.AfterFunc(ctx, func() { channel.Reset() })
	defer stop()
	defer func() {
		if failure != nil {
			channel.Reset()
			session.stream.stop()
		}
	}()
	if ctx.Err() != nil {
		return ErrRejected
	}
	nonce := make([]byte, 32)
	if _, err := rand.Read(nonce); err != nil {
		return ErrRejected
	}
	crlHash := sha256.Sum256(next.crl.Raw)
	local := &renewalHello{Version: 1, Generation: next.generation, Nonce: nonce, Certificate: next.local.Raw, CRL: crlHash[:], MinimumCRL: next.profile.MinimumCRL}
	var remote renewalMessage
	if session.server {
		remote, err = readRenewal(channel, "hello")
	} else {
		err = writeRenewal(channel, renewalMessage{Kind: "hello", Hello: local})
		if err == nil {
			remote, err = readRenewal(channel, "hello")
		}
	}
	if err != nil {
		return ErrRejected
	}
	peer := remote.Hello
	if peer.Version != 1 || peer.Generation != next.generation || len(peer.Nonce) != 32 || bytes.Equal(peer.Nonce, nonce) ||
		!bytes.Equal(peer.CRL, crlHash[:]) || peer.MinimumCRL != next.profile.MinimumCRL || len(peer.Certificate) > 4096 {
		return ErrRejected
	}
	certificate, err := x509.ParseCertificate(peer.Certificate)
	if err != nil || !sameRenewalHolder(next.peer, certificate) || next.verify(certificate, session.server) != nil {
		return ErrRejected
	}
	next.peer = certificate
	if !minTime(next.local.NotAfter, next.peer.NotAfter, next.crl.NextUpdate, next.authority.NotAfter).After(originalDeadline) {
		return ErrRejected
	}
	if session.server && writeRenewal(channel, renewalMessage{Kind: "hello", Hello: local}) != nil {
		return ErrRejected
	}
	clientHello, serverHello := local, peer
	if session.server {
		clientHello, serverHello = peer, local
	}
	binding := session.ConnectionState()
	exporter, err := binding.ExportKeyingMaterial(renewalDomain, nil, 32)
	if err != nil {
		return ErrRejected
	}
	defer clear(exporter)
	transcript, err := json.Marshal(struct {
		Client, Server *renewalHello
		Binding        []byte
	}{clientHello, serverHello, exporter})
	if err != nil {
		return ErrRejected
	}
	defer clear(transcript)
	digest := sha256.Sum256(transcript)
	peerKey, ok := next.peer.PublicKey.(ed25519.PublicKey)
	if !ok {
		return ErrRejected
	}
	send := func(kind string) error {
		return writeRenewal(channel, renewalMessage{Kind: kind, Proof: ed25519.Sign(key, renewalProof(kind, digest[:]))})
	}
	receive := func(kind string) error {
		message, err := readRenewal(channel, kind)
		if err != nil || !ed25519.Verify(peerKey, renewalProof(kind, digest[:]), message.Proof) {
			return ErrRejected
		}
		return nil
	}
	if session.server {
		if receive("client-proof") != nil || send("server-proof") != nil || receive("client-commit") != nil ||
			session.commitRenewal(ctx, next, guard) != nil || send("server-committed") != nil || receive("client-done") != nil {
			return ErrRejected
		}
	} else if send("client-proof") != nil || receive("server-proof") != nil || send("client-commit") != nil ||
		receive("server-committed") != nil || session.commitRenewal(ctx, next, guard) != nil || send("client-done") != nil {
		return ErrRejected
	}
	if channel.CloseWrite() != nil {
		return ErrRejected
	}
	var extra [1]byte
	if count, err := channel.Read(extra[:]); count != 0 || err != io.EOF || ctx.Err() != nil {
		return ErrRejected
	}
	if channel.Close() != nil {
		return ErrRejected
	}
	return nil
}
