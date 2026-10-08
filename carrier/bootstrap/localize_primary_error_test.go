package bootstrap

import (
	"context"
	"errors"
	"testing"
)

type primaryErrorEndpoint struct {
	failure error
}

func (endpoint primaryErrorEndpoint) SendContext(context.Context, []byte) error { return nil }
func (endpoint primaryErrorEndpoint) Recv(context.Context) ([]byte, error) {
	return nil, endpoint.failure
}
func (endpoint primaryErrorEndpoint) Close() error { return nil }

func TestLocalizeBootstrapHELLOPreservesPrimaryFailure(test *testing.T) {
	primary := context.DeadlineExceeded
	_, actual := requestTransport(context.Background(), primaryErrorEndpoint{failure: primary})
	if !errors.Is(actual, primary) {
		test.Fatalf("primary HELLO receive error erased: got %T (%v); errors.Is(deadline)=false", actual, actual)
	}
}
