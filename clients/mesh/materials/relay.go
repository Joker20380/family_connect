package materials

import (
	"context"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopmesh"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type relayProcess struct {
	mu         sync.Mutex
	ctx        context.Context
	cancel     context.CancelFunc
	command    func(context.Context) *exec.Cmd
	process    *exec.Cmd
	input      io.WriteCloser
	output     io.ReadCloser
	scratch    string
	index      int
	identifier uint64
}

func installedRelay(ctx context.Context, index int) *relayProcess {
	executable, err := os.Executable()
	if err != nil {
		return nil
	}
	directory := filepath.Join(filepath.Dir(executable), "rns")
	archive := filepath.Join(directory, "fc-rns.pyz")
	interpreter := "/usr/bin/python3"
	if runtime.GOOS == "windows" {
		interpreter = filepath.Join(directory, "python.exe")
		info, err := os.Lstat(interpreter)
		if err != nil || !info.Mode().IsRegular() {
			return nil
		}
	}
	info, err := os.Lstat(archive)
	if err != nil || !info.Mode().IsRegular() || (runtime.GOOS != "windows" && info.Mode().Perm()&0022 != 0) {
		return nil
	}
	ctx, cancel := context.WithCancel(ctx)
	return &relayProcess{ctx: ctx, cancel: cancel, index: index, command: func(ctx context.Context) *exec.Cmd {
		return exec.CommandContext(ctx, interpreter, "-I", "-S", archive, "--stdio")
	}}
}

func (relay *relayProcess) start() error {
	scratch, err := os.MkdirTemp("", "fc-rns-child-")
	if err != nil {
		return err
	}
	defer func() {
		if relay.process == nil {
			os.RemoveAll(scratch)
		}
	}()
	process := relay.command(relay.ctx)
	process.WaitDelay = 2 * time.Second
	process.Env = []string{"LANG=C.UTF-8", "PYTHONNOUSERSITE=1", "PYTHONDONTWRITEBYTECODE=1", "TMPDIR=" + scratch, "TEMP=" + scratch, "TMP=" + scratch}
	if runtime.GOOS == "windows" {
		for _, name := range []string{"SystemRoot", "WINDIR"} {
			if value, exists := os.LookupEnv(name); exists {
				process.Env = append(process.Env, name+"="+value)
			}
		}
	}
	input, err := process.StdinPipe()
	if err != nil {
		return err
	}
	output, err := process.StdoutPipe()
	if err != nil {
		input.Close()
		return err
	}
	process.Cancel = func() error {
		input.Close()
		output.Close()
		if runtime.GOOS == "windows" {
			return process.Process.Kill()
		}
		return process.Process.Signal(os.Interrupt)
	}
	if err := process.Start(); err != nil {
		input.Close()
		output.Close()
		return err
	}
	relay.process, relay.input, relay.output, relay.scratch = process, input, output, scratch
	return nil
}

func (relay *relayProcess) request(ctx context.Context, path string, body []byte) ([]byte, error) {
	relay.mu.Lock()
	defer relay.mu.Unlock()
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if relay.ctx.Err() != nil {
		return nil, relay.ctx.Err()
	}
	deadline, valid := ctx.Deadline()
	if !valid || relay.identifier >= 4 || len(body) == 0 || len(body) > 8192 {
		return nil, desktopmesh.ErrConfiguration
	}
	remaining := time.Until(deadline).Milliseconds()
	if remaining <= 0 {
		return nil, context.DeadlineExceeded
	}
	if remaining > 200000 {
		remaining = 200000
	}
	stop := context.AfterFunc(ctx, relay.cancel)
	defer stop()
	if relay.process == nil {
		if err := relay.start(); err != nil {
			return nil, &desktopmesh.ReadinessFailure{Code: "RNS_WORKER_UNAVAILABLE"}
		}
	}
	relay.identifier++
	command := struct {
		Schema int    `json:"schema"`
		ID     uint64 `json:"id"`
		Index  int    `json:"underlying_index"`
		Budget int64  `json:"budget_ms"`
		Path   string `json:"path"`
		Body   []byte `json:"body"`
	}{1, relay.identifier, relay.index, remaining, path, body}
	var response struct {
		Schema int    `json:"schema"`
		ID     uint64 `json:"id"`
		Code   string `json:"code"`
		Body   []byte `json:"body,omitempty"`
	}
	err := worker.WriteControlReply(relay.input, command)
	if err == nil {
		err = worker.ReadControlMessage(relay.output, &response, 131072)
	}
	if ctx.Err() != nil || relay.ctx.Err() != nil {
		clear(response.Body)
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		return nil, relay.ctx.Err()
	}
	if err != nil || response.Schema != 1 || response.ID != relay.identifier {
		clear(response.Body)
		relay.cancel()
		return nil, &desktopmesh.ReadinessFailure{Code: "RNS_PROTOCOL_REJECTED"}
	}
	if response.Code == "OK" && len(response.Body) > 0 && len(response.Body) <= desktopmesh.MaxReadinessRelay {
		return response.Body, nil
	}
	clear(response.Body)
	relay.cancel()
	if response.Code == "UNAVAILABLE" && len(response.Body) == 0 {
		return nil, &desktopmesh.ReadinessFailure{Code: "RNS_UNAVAILABLE", Availability: true}
	}
	return nil, &desktopmesh.ReadinessFailure{Code: "RNS_PROTOCOL_REJECTED"}
}

func (relay *relayProcess) Close() error {
	relay.cancel()
	relay.mu.Lock()
	defer relay.mu.Unlock()
	if relay.process == nil {
		return nil
	}
	relay.input.Close()
	relay.output.Close()
	err := relay.process.Wait()
	relay.process = nil
	cleanup := os.RemoveAll(relay.scratch)
	relay.scratch = ""
	var exited *exec.ExitError
	if errors.As(err, &exited) || errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
		return cleanup
	}
	return errors.Join(err, cleanup)
}
