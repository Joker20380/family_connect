package sessionprofile

import (
	"context"
	"errors"
	"github.com/Joker20380/family_connect/carrier/localwrite"
	"github.com/Joker20380/family_connect/carrier/reliablestream"
)

type Profile uint8

const (
	P0 Profile = iota
	P1
	P2
)

type key struct{}

func Parse(value string) (Profile, error) {
	switch value {
	case "", "P0":
		return P0, nil
	case "P1":
		return P1, nil
	case "P2":
		return P2, nil
	}
	return P0, errors.New("invalid session profile")
}
func (profile Profile) Name() string { return [...]string{"P0", "P1", "P2"}[profile] }
func With(ctx context.Context, profile Profile) context.Context {
	return context.WithValue(ctx, key{}, profile)
}
func From(ctx context.Context) Profile { profile, _ := ctx.Value(key{}).(Profile); return profile }
func (profile Profile) Reliable() reliablestream.Config {
	config := reliablestream.DefaultConfig()
	if profile == P1 || profile == P2 {
		config.SendWindow, config.ReceiveWindow = 32, 32
	}
	return config
}
func (profile Profile) LocalWrite(ctx context.Context) context.Context {
	if profile == P2 {
		return localwrite.WithCompletion(ctx)
	}
	return ctx
}
