//go:build linux

package roombroker

import (
	"errors"
	"io"
	"os"
	"strings"

	"golang.org/x/sys/unix"
)

func muxOperatorValue(name string) (string, error) {
	directory := os.Getenv("FC_DIAGNOSTIC_CONTROL_DIR")
	if directory == "" {
		return "", nil
	}
	descriptor, err := unix.Open(directory, unix.O_RDONLY|unix.O_DIRECTORY|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0)
	if err != nil {
		return "", Code("mux_profile_configuration")
	}
	defer unix.Close(descriptor)
	var info unix.Stat_t
	if unix.Fstat(descriptor, &info) != nil || info.Uid != uint32(os.Geteuid()) || info.Mode&0777 != 0700 {
		return "", Code("mux_profile_configuration")
	}
	fileDescriptor, err := unix.Openat(descriptor, name, unix.O_RDONLY|unix.O_NOFOLLOW|unix.O_NONBLOCK|unix.O_CLOEXEC, 0)
	if errors.Is(err, unix.ENOENT) {
		return "", nil
	}
	if err != nil {
		return "", Code("mux_profile_configuration")
	}
	file := os.NewFile(uintptr(fileDescriptor), name)
	defer file.Close()
	if unix.Fstat(fileDescriptor, &info) != nil || info.Uid != uint32(os.Geteuid()) || info.Mode&0777 != 0600 || info.Mode&unix.S_IFMT != unix.S_IFREG {
		return "", Code("mux_profile_configuration")
	}
	raw, err := io.ReadAll(io.LimitReader(file, 33))
	if err != nil || len(raw) > 32 {
		return "", Code("mux_profile_configuration")
	}
	return strings.TrimSpace(string(raw)), nil
}

func muxCreditPolicy() (bool, error) {
	value, err := muxOperatorValue("mux-profile")
	if err != nil {
		return false, err
	}
	switch value {
	case "", "LEGACY64":
		return false, nil
	case "CREDIT128":
		return true, nil
	default:
		return false, Code("mux_profile_configuration")
	}
}

func muxCountersEnabled() bool {
	value, err := muxOperatorValue("mux-counters")
	return err == nil && value == "ON"
}
