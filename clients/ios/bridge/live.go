package bridge

import (
	"context"

	"github.com/Joker20380/family_connect/carrier/underlay"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

type Material struct {
	Profile   []byte `json:"profile"`
	Directory []byte `json:"directory"`
	Resolver  string `json:"resolver"`
	Interface string `json:"interface"`
}

func Live(material Material) Opener {
	return func(ctx context.Context) (*wholedevice.Session, error) {
		defer clear(material.Profile)
		defer clear(material.Directory)
		protect, err := boundInterface(material.Interface)
		if err != nil {
			return nil, ErrUnderlay
		}
		network, err := underlay.New(ctx, material.Resolver, protect)
		if err != nil {
			return nil, ErrUnderlay
		}
		session, err := wholedevice.OpenProvisioned(ctx, material.Profile, material.Directory, network, func(string) {})
		if err != nil {
			network.Close()
			return nil, err
		}
		context.AfterFunc(ctx, network.Close)
		return session, nil
	}
}
