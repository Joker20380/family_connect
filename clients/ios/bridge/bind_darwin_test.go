package bridge

import (
	"net"
	"syscall"
	"testing"
)

func TestDarwinSocketBindingReadback(test *testing.T) {
	interfaces, err := net.Interfaces()
	if err != nil {
		test.Fatal(err)
	}
	for _, iface := range interfaces {
		protect, err := boundInterface(iface.Name)
		if err != nil {
			continue
		}
		fd, err := syscall.Socket(syscall.AF_INET, syscall.SOCK_DGRAM, 0)
		if err != nil {
			test.Fatal(err)
		}
		defer syscall.Close(fd)
		if !protect(fd) {
			test.Fatal("bind rejected on eligible interface")
		}
		index, err := syscall.GetsockoptInt(fd, syscall.IPPROTO_IP, syscall.IP_BOUND_IF)
		if err != nil || index != iface.Index {
			test.Fatal("bound interface readback", err)
		}
		if protect(-1) {
			test.Fatal("invalid descriptor accepted")
		}
		return
	}
	test.Fatal("runner has no eligible IPv4 interface; positive binding check NOT_RUN")
}
