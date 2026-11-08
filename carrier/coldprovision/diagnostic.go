package coldprovision

import (
	"context"
	"crypto/tls"
	"errors"
	"io"
	"net"
	"os"
	"sync"
	"syscall"
	"time"

	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

type DiagnosticSnapshot struct {
	Handle       int64  `json:"handle"`
	GoEntered    bool   `json:"go_entered"`
	BudgetKnown  bool   `json:"budget_known"`
	Stage        string `json:"stage"`
	LastSuccess  string `json:"last_success"`
	FirstFailure string `json:"first_failure"`
	Reason       string `json:"reason"`
	ProviderStep string `json:"provider_step"`
	HTTPStatus   int    `json:"http_status"`
	Errno        int    `json:"errno"`
	Security     bool   `json:"security"`
	ElapsedMS    int64  `json:"elapsed_ms"`
	RemainingMS  int64  `json:"remaining_ms"`
	Protected    uint64 `json:"protected"`
	Denied       uint64 `json:"denied"`
	Closed       bool   `json:"closed"`
	Released     bool   `json:"released"`
}

type Diagnostic struct {
	mu       sync.Mutex
	started  time.Time
	deadline time.Time
	value    DiagnosticSnapshot
}

type diagnosticKey struct{}

func NewDiagnostic(budget time.Duration) *Diagnostic {
	now := time.Now()
	return &Diagnostic{started: now, deadline: now.Add(budget), value: DiagnosticSnapshot{GoEntered: true, BudgetKnown: true, LastSuccess: "GO_ENTRY", Stage: "GO_ENTRY", Reason: "NONE"}}
}

func WithDiagnostic(ctx context.Context, diagnostic *Diagnostic) context.Context {
	return context.WithValue(ctx, diagnosticKey{}, diagnostic)
}

func diagnosticFrom(ctx context.Context) *Diagnostic {
	diagnostic, _ := ctx.Value(diagnosticKey{}).(*Diagnostic)
	return diagnostic
}

func (diagnostic *Diagnostic) Handle(handle int64) {
	diagnostic.mu.Lock()
	diagnostic.value.Handle = handle
	diagnostic.mu.Unlock()
}

func (diagnostic *Diagnostic) Stage(stage string, success bool) {
	if diagnostic == nil {
		return
	}
	diagnostic.mu.Lock()
	defer diagnostic.mu.Unlock()
	if diagnostic.value.FirstFailure != "" {
		return
	}
	switch stage {
	case "LOCATOR", "UNDERLAY", "TELEMOST_CREATE", "TELEMOST_CONNECT", "CARRIER_OPEN", "PACKET_EXCHANGE", "RELIABLE_STREAM", "TLS_HANDSHAKE", "REQUEST_VALIDATE", "REQUEST_WRITE", "RESPONSE_READ", "RESPONSE_VALIDATE":
		diagnostic.value.Stage = stage
		if success {
			diagnostic.value.LastSuccess = stage
		}
	}
}

func (diagnostic *Diagnostic) Failure(err error) {
	if diagnostic == nil || err == nil {
		return
	}
	diagnostic.mu.Lock()
	defer diagnostic.mu.Unlock()
	if diagnostic.value.FirstFailure != "" {
		return
	}
	diagnostic.value.FirstFailure = diagnostic.value.Stage
	diagnostic.value.Reason = reasonCode(err)
	var errno syscall.Errno
	if errors.As(err, &errno) {
		diagnostic.value.Errno = int(errno)
	}
	if diagnostic.value.Stage == "TLS_HANDSHAKE" && errors.Is(err, ErrRejected) {
		diagnostic.value.Reason = "TLS_TRUST"
	}
	var certificate *tls.CertificateVerificationError
	diagnostic.value.Security = errors.Is(err, ErrRejected) || errors.As(err, &certificate)
	var provider *telemost.ConnectionFailure
	if errors.As(err, &provider) {
		switch provider.Step {
		case "HTTP_CONNECT", "HTTP_STATUS", "HTTP_DECODE", "HTTP_VALIDATE", "PEER_SETUP", "TRANSPORT_SETUP", "SIGNAL_CONNECT", "SIGNAL_HELLO", "MEDIA_READY":
			diagnostic.value.ProviderStep = provider.Step
		default:
			diagnostic.value.ProviderStep = "UNKNOWN"
		}
		if provider.Status >= 100 && provider.Status <= 599 {
			diagnostic.value.HTTPStatus = provider.Status
		}
	}
}

func reasonCode(err error) string {
	var certificate *tls.CertificateVerificationError
	var dns *net.DNSError
	var provider *telemost.ConnectionFailure
	switch {
	case errors.As(err, &certificate):
		return "TLS_TRUST"
	case errors.Is(err, ErrRejected):
		return "REJECTED"
	case errors.Is(err, context.Canceled):
		return "CANCELLED"
	case errors.Is(err, context.DeadlineExceeded), errors.Is(err, os.ErrDeadlineExceeded):
		return "DEADLINE"
	case errors.As(err, &dns):
		return "DNS"
	case errors.Is(err, syscall.ECONNREFUSED):
		return "CONNECTION_REFUSED"
	case errors.Is(err, syscall.EACCES), errors.Is(err, syscall.EPERM):
		return "PERMISSION_DENIED"
	case errors.Is(err, syscall.ENETUNREACH), errors.Is(err, syscall.EHOSTUNREACH):
		return "NETWORK_UNREACHABLE"
	case errors.Is(err, syscall.ECONNRESET):
		return "CONNECTION_RESET"
	case errors.Is(err, underlay.ErrDenied):
		return "SOCKET_DENIED"
	case errors.Is(err, io.EOF):
		return "EOF"
	case errors.Is(err, io.ErrUnexpectedEOF):
		return "UNEXPECTED_EOF"
	case errors.Is(err, io.ErrClosedPipe), errors.Is(err, net.ErrClosed):
		return "CLOSED"
	case errors.Is(err, telemost.ErrAPI):
		return "PROVIDER_HTTP"
	case errors.As(err, &provider):
		switch provider.Code {
		case "HTTP_TRANSPORT", "PROVIDER_RESPONSE", "SIGNAL_TRANSPORT", "CARRIER_ERROR", "DEADLINE":
			return provider.Code
		default:
			return "IO"
		}
	default:
		return "IO"
	}
}

func (diagnostic *Diagnostic) Protect(accepted bool) {
	result := 0
	if accepted {
		result = 1
	}
	diagnostic.ProtectResult(result)
}

func (diagnostic *Diagnostic) ProtectResult(result int) {
	diagnostic.mu.Lock()
	defer diagnostic.mu.Unlock()
	if result == 1 {
		diagnostic.value.Protected++
		return
	}
	diagnostic.value.Denied++
	if diagnostic.value.FirstFailure == "" {
		diagnostic.value.FirstFailure = "SOCKET_PROTECT_BIND"
		diagnostic.value.Reason = "SOCKET_DENIED"
		switch result {
		case -1:
			diagnostic.value.Reason = "JNI_ENVIRONMENT"
		case -2:
			diagnostic.value.Reason = "JNI_CALLBACK_MISSING"
		case -3:
			diagnostic.value.Reason = "JNI_CALLBACK_EXCEPTION"
		}
	}
}

func (diagnostic *Diagnostic) Close(released bool) {
	diagnostic.mu.Lock()
	defer diagnostic.mu.Unlock()
	if released {
		diagnostic.value.Released = true
	} else {
		diagnostic.value.Closed = true
	}
}

func (diagnostic *Diagnostic) Snapshot() DiagnosticSnapshot {
	diagnostic.mu.Lock()
	defer diagnostic.mu.Unlock()
	value := diagnostic.value
	value.ElapsedMS = max(0, time.Since(diagnostic.started).Milliseconds())
	value.RemainingMS = max(0, time.Until(diagnostic.deadline).Milliseconds())
	return value
}
