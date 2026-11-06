package coldprovision

import (
	"context"
	"crypto/tls"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/roombroker"
	"github.com/Joker20380/family_connect/carrier/telemost"
	"github.com/Joker20380/family_connect/carrier/underlay"
)

func Telemost(network *underlay.Network) bootstrap.SeedConnector {
	return func(lifetime, ready context.Context, room roombroker.Room) (familysession.PacketEndpoint, error) {
		if network == nil {
			return nil, ErrRejected
		}
		carrier, err := telemost.NewOwned(lifetime, telemost.Config{RoomURL: room.JoinURL, DisplayName: "Family provisioning", Mode: telemost.ModeVP8, MaxVideoTracks: 4, Underlay: network})
		if err != nil {
			return nil, err
		}
		if err = carrier.Connect(ready); err != nil {
			carrier.Close()
			return nil, err
		}
		return carrier, nil
	}
}

type Config struct {
	Anchor                []byte
	Node, Family, Gateway string
	Lifetime              time.Duration
	Identity              tls.Certificate
	Publish               func(bootstrap.Directory) ([]byte, error)
}

func Run(ctx context.Context, config Config, provider roombroker.RoomProvider, connect bootstrap.SeedConnector, backend Backend) error {
	if config.Publish == nil || backend == nil || len(config.Identity.Certificate) != 1 {
		return ErrRejected
	}
	var expires time.Time
	manager := bootstrap.SeedManager{Publish: func(directory bootstrap.Directory) error {
		raw, err := config.Publish(directory)
		if err != nil {
			return ErrRejected
		}
		address, _, err := Verify(raw, config.Anchor, config.Node, time.Now())
		if err != nil {
			return err
		}
		server, err := certificate(address.ServerCertificate)
		if err != nil || string(server.Raw) != string(config.Identity.Certificate[0]) || len(directory.Seeds) != 1 || address.Room != directory.Seeds[0].JoinURL || address.ExpiresAt > directory.ExpiresAt.Unix() {
			return ErrRejected
		}
		expires = time.Unix(address.ExpiresAt, 0)
		return nil
	}}
	return manager.Run(ctx, provider, connect, config.Family, config.Gateway, config.Lifetime, func(ctx context.Context, endpoint familysession.PacketEndpoint) {
		Serve(ctx, endpoint, config.Identity, expires, config.Node, backend)
	})
}
