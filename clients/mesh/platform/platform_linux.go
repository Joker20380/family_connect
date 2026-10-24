package platform

import (
	"context"
	"io"
	"net"
	"os"
	"strings"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
	"golang.org/x/sys/unix"
	"gvisor.dev/gvisor/pkg/tcpip/link/fdbased"
)

func (Native) Protect(underlying net.Interface, fd int) bool {
	if strings.EqualFold(underlying.Name, worker.InterfaceName) || underlying.Flags&net.FlagLoopback != 0 || underlying.Index <= 0 {
		return false
	}
	if unix.SetsockoptString(fd, unix.SOL_SOCKET, unix.SO_BINDTODEVICE, underlying.Name) != nil {
		return false
	}
	return unix.SetsockoptInt(fd, unix.SOL_SOCKET, unix.SO_MARK, worker.UnderlayMark) == nil
}

func (Native) bindVPN(tunnel net.Interface, descriptor int) bool {
	if tunnel.Name != worker.InterfaceName || tunnel.Index <= 0 || tunnel.Flags&net.FlagUp == 0 {
		return false
	}
	return unix.SetsockoptString(descriptor, unix.SOL_SOCKET, unix.SO_BINDTODEVICE, tunnel.Name) == nil &&
		unix.SetsockoptInt(descriptor, unix.SOL_SOCKET, unix.SO_MARK, 0) == nil
}

type linuxDevice struct {
	*os.File
	index int
}

func (device *linuxDevice) Failed() bool {
	current, err := net.InterfaceByName(worker.InterfaceName)
	return err != nil || current.Index != device.index
}

func (Native) Attach(ctx context.Context, session *wholedevice.Session) (io.Closer, error) {
	if ctx.Err() != nil || session == nil || session.Failed() {
		return nil, wholedevice.ErrClosed
	}
	if _, err := net.InterfaceByName(worker.InterfaceName); err == nil {
		return nil, wholedevice.ErrClosed
	}
	fd, err := unix.Open("/dev/net/tun", unix.O_RDWR|unix.O_CLOEXEC, 0)
	if err != nil {
		return nil, err
	}
	device := os.NewFile(uintptr(fd), "mesh-tun")
	request, err := unix.NewIfreq(worker.InterfaceName)
	if err == nil {
		request.SetUint16(unix.IFF_TUN | unix.IFF_NO_PI | unix.IFF_TUN_EXCL)
		err = unix.IoctlIfreq(fd, unix.TUNSETIFF, request)
	}
	if err == nil {
		err = unix.SetNonblock(fd, true)
	}
	if err != nil {
		device.Close()
		return nil, err
	}
	link, err := net.InterfaceByName(worker.InterfaceName)
	if err != nil {
		device.Close()
		return nil, err
	}
	endpoint, err := fdbased.New(&fdbased.Options{FDs: []int{fd}, MTU: worker.MTU, RXChecksumOffload: true})
	if err != nil {
		device.Close()
		return nil, err
	}
	return startPacket(ctx, endpoint, &linuxDevice{File: device, index: link.Index}, session)
}
