//go:build !darwin

package bridge

func boundInterface(string) (func(int) bool, error) { return nil, ErrUnderlay }
