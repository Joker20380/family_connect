package main

import (
	"net"
	"os"
	"strconv"

	"github.com/Joker20380/family_connect/desktopbridge/worker"
	"golang.org/x/sys/unix"
)

const chatEndpoint = "inherited-unix-stream"

func inheritedChat(value string) (net.Conn, error) {
	descriptor, err := strconv.Atoi(value)
	if err != nil || descriptor < 3 || descriptor > 1048576 {
		return nil, worker.ErrProtocol
	}
	file := os.NewFile(uintptr(descriptor), "chat-private-ipc")
	if file == nil {
		return nil, worker.ErrProtocol
	}
	connection, err := net.FileConn(file)
	file.Close()
	if err != nil {
		return nil, worker.ErrProtocol
	}
	stream, ok := connection.(*net.UnixConn)
	if !ok || stream.LocalAddr().Network() != "unix" {
		connection.Close()
		return nil, worker.ErrProtocol
	}
	raw, err := stream.SyscallConn()
	valid := false
	if err == nil {
		err = raw.Control(func(descriptor uintptr) {
			credential, check := unix.GetsockoptUcred(int(descriptor), unix.SOL_SOCKET, unix.SO_PEERCRED)
			valid = check == nil && credential.Uid == uint32(os.Geteuid())
		})
	}
	if err != nil || !valid {
		connection.Close()
		return nil, worker.ErrProtocol
	}
	return connection, nil
}
