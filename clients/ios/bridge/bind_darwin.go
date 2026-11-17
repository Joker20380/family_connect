package bridge

import (
	"net"
	"strings"
	"syscall"
)

func boundInterface(name string) (func(int) bool, error) {
	if !strings.HasPrefix(name, "en") && !strings.HasPrefix(name, "pdp_ip") {
		return nil, ErrUnderlay
	}
	iface, err := net.InterfaceByName(name)
	if err != nil || iface.Index <= 0 || iface.Flags&net.FlagUp == 0 || iface.Flags&net.FlagLoopback != 0 {
		return nil, ErrUnderlay
	}
	addresses, err := iface.Addrs()
	if err != nil {
		return nil, ErrUnderlay
	}
	hasIPv4 := false
	for _, address := range addresses {
		ip, _, err := net.ParseCIDR(address.String())
		if err == nil && ip.To4() != nil && !ip.IsLoopback() && !ip.IsUnspecified() {
			hasIPv4 = true
		}
	}
	if !hasIPv4 {
		return nil, ErrUnderlay
	}
	return func(fd int) bool {
		current, err := net.InterfaceByName(name)
		if err != nil || current.Index != iface.Index || current.Flags&net.FlagUp == 0 {
			return false
		}
		if syscall.SetsockoptInt(fd, syscall.IPPROTO_IP, syscall.IP_BOUND_IF, iface.Index) != nil {
			return false
		}
		bound, err := syscall.GetsockoptInt(fd, syscall.IPPROTO_IP, syscall.IP_BOUND_IF)
		return err == nil && bound == iface.Index
	}, nil
}
