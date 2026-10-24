package platform

import (
	"context"
	"encoding/binary"
	"errors"
	"io"
	"net"
	"strings"
	"sync"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
	"golang.org/x/sys/windows"
	"golang.zx2c4.com/wintun"
	"gvisor.dev/gvisor/pkg/buffer"
	"gvisor.dev/gvisor/pkg/tcpip/header"
	"gvisor.dev/gvisor/pkg/tcpip/link/channel"
	"gvisor.dev/gvisor/pkg/tcpip/stack"
)

const ipUnicastInterface = 31

func (Native) Protect(underlying net.Interface, fd int) bool {
	if strings.EqualFold(underlying.Name, worker.InterfaceName) || underlying.Flags&net.FlagLoopback != 0 || underlying.Index <= 0 {
		return false
	}
	var encoded [4]byte
	binary.BigEndian.PutUint32(encoded[:], uint32(underlying.Index))
	index := int(binary.LittleEndian.Uint32(encoded[:]))
	return windows.SetsockoptInt(windows.Handle(fd), windows.IPPROTO_IP, ipUnicastInterface, index) == nil
}

func (Native) bindVPN(tunnel net.Interface, descriptor int) bool {
	if tunnel.Name != worker.InterfaceName || tunnel.Index <= 0 || tunnel.Flags&net.FlagUp == 0 {
		return false
	}
	var encoded [4]byte
	binary.BigEndian.PutUint32(encoded[:], uint32(tunnel.Index))
	index := int(binary.LittleEndian.Uint32(encoded[:]))
	return windows.SetsockoptInt(windows.Handle(descriptor), windows.IPPROTO_IP, ipUnicastInterface, index) == nil
}

type windowsDevice struct {
	adapter  *wintun.Adapter
	session  wintun.Session
	endpoint *channel.Endpoint
	stop     windows.Handle
	cancel   context.CancelFunc
	workers  sync.WaitGroup
	once     sync.Once
	ctx      context.Context
}

func (device *windowsDevice) Failed() bool { return device.ctx.Err() != nil }

func (device *windowsDevice) Stop() {
	device.cancel()
	windows.SetEvent(device.stop)
	device.workers.Wait()
}

func (Native) Attach(ctx context.Context, session *wholedevice.Session) (io.Closer, error) {
	if ctx.Err() != nil || session == nil || session.Failed() {
		return nil, wholedevice.ErrClosed
	}
	if _, err := net.InterfaceByName(worker.InterfaceName); err == nil {
		return nil, wholedevice.ErrClosed
	}
	guid := windows.GUID{Data1: 0x46434d53, Data2: 0x4831, Data3: 0x4000, Data4: [8]byte{0x80, 0x01, 0x46, 0x43, 0x4d, 0x45, 0x53, 0x48}}
	adapter, err := wintun.CreateAdapter(worker.InterfaceName, "FamilyConnect", &guid)
	if err != nil {
		return nil, err
	}
	ring, err := adapter.StartSession(0x800000)
	if err != nil {
		adapter.Close()
		return nil, err
	}
	stop, err := windows.CreateEvent(nil, 1, 0, nil)
	if err != nil {
		ring.End()
		adapter.Close()
		return nil, err
	}
	packetCtx, cancel := context.WithCancel(ctx)
	device := &windowsDevice{adapter: adapter, session: ring, endpoint: channel.New(128, worker.MTU, ""), stop: stop, cancel: cancel, ctx: packetCtx}
	path, err := startPacket(packetCtx, device.endpoint, device, session)
	if err != nil {
		return nil, err
	}
	device.workers.Add(2)
	go device.read(packetCtx)
	go device.write(packetCtx)
	return path, nil
}

func (device *windowsDevice) read(ctx context.Context) {
	defer device.workers.Done()
	for ctx.Err() == nil {
		data, err := device.session.ReceivePacket()
		if errors.Is(err, windows.ERROR_NO_MORE_ITEMS) {
			result, waitErr := windows.WaitForMultipleObjects([]windows.Handle{device.stop, device.session.ReadWaitEvent()}, false, 1000)
			if waitErr != nil || result == windows.WAIT_OBJECT_0 {
				return
			}
			continue
		}
		if err != nil {
			device.cancel()
			return
		}
		if len(data) > 0 && data[0]>>4 == 4 && len(data) <= 65535 {
			packet := stack.NewPacketBuffer(stack.PacketBufferOptions{Payload: buffer.MakeWithData(append([]byte(nil), data...))})
			device.session.ReleaseReceivePacket(data)
			device.endpoint.InjectInbound(header.IPv4ProtocolNumber, packet)
			packet.DecRef()
		} else {
			device.session.ReleaseReceivePacket(data)
		}
	}
}

func (device *windowsDevice) write(ctx context.Context) {
	defer device.workers.Done()
	for ctx.Err() == nil {
		packet := device.endpoint.ReadContext(ctx)
		if packet == nil {
			return
		}
		data, err := device.session.AllocateSendPacket(packet.Size())
		if err == nil {
			offset := 0
			for _, part := range packet.AsSlices() {
				offset += copy(data[offset:], part)
			}
			device.session.SendPacket(data)
		}
		packet.DecRef()
		if err != nil && !errors.Is(err, windows.ERROR_BUFFER_OVERFLOW) {
			device.cancel()
			return
		}
	}
}

func (device *windowsDevice) Close() error {
	device.once.Do(func() {
		device.Stop()
		device.session.End()
		device.adapter.Close()
		windows.CloseHandle(device.stop)
	})
	return nil
}
