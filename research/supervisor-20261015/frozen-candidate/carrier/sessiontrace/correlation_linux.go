//go:build fc_owner_diagnostic && linux

package sessiontrace

import (
	"context"
	"io"
	"net"
	"os"
	"path/filepath"
	"time"

	"golang.org/x/sys/unix"
)

func StartDiagnosticControl(ctx context.Context, recorder *Recorder, role string) {
	context.AfterFunc(ctx, recorder.closeCorrelation)
	directory := os.Getenv("FC_DIAGNOSTIC_CONTROL_DIR")
	if directory == "" {
		return
	}
	_, _ = recorder.serveCorrelation(ctx, directory, role)
}

func (recorder *Recorder) serveCorrelation(ctx context.Context, directory, role string) (string, error) {
	if !Allowed(role, "client|gateway") {
		return "", correlationRejected
	}
	var info unix.Stat_t
	if err := unix.Lstat(directory, &info); err != nil || info.Mode&unix.S_IFMT != unix.S_IFDIR || info.Mode&0777 != 0700 || info.Uid != uint32(os.Geteuid()) {
		return "", correlationRejected
	}
	tag := recorder.Snapshot().SessionTag
	if len(tag) != 64 {
		return "", correlationRejected
	}
	path := filepath.Join(directory, tag+".sock")
	listener, err := net.ListenUnix("unix", &net.UnixAddr{Name: path, Net: "unix"})
	if err != nil {
		return "", correlationRejected
	}
	if err := os.Chmod(path, 0600); err != nil {
		listener.Close()
		return "", correlationRejected
	}
	stop := context.AfterFunc(ctx, func() { recorder.closeCorrelation(); listener.Close() })
	go func() {
		defer stop()
		defer listener.Close()
		defer recorder.closeCorrelation()
		for {
			connection, err := listener.AcceptUnix()
			if err != nil {
				return
			}
			recorder.handleCorrelation(connection, role)
			connection.Close()
		}
	}()
	return path, nil
}

func (recorder *Recorder) handleCorrelation(connection *net.UnixConn, role string) {
	connection.SetDeadline(time.Now().Add(time.Second))
	authorized := false
	raw, err := connection.SyscallConn()
	if err == nil {
		err = raw.Control(func(descriptor uintptr) {
			credentials, failure := unix.GetsockoptUcred(int(descriptor), unix.SOL_SOCKET, unix.SO_PEERCRED)
			authorized = failure == nil && credentials.Uid == uint32(os.Geteuid())
		})
	}
	if err != nil || !authorized {
		return
	}
	rawRequest, failure := io.ReadAll(io.LimitReader(connection, 16*1024+1))
	if failure != nil {
		return
	}
	io.WriteString(connection, recorder.CorrelationCommand(string(rawRequest), role))
}
