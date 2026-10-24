package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"syscall"

	"github.com/Joker20380/family_connect/carrier/restrictedchat"
	"github.com/Joker20380/family_connect/desktopbridge/automatic"
	"github.com/Joker20380/family_connect/desktopbridge/chatipc"
	"github.com/Joker20380/family_connect/desktopbridge/direct"
	"github.com/Joker20380/family_connect/desktopbridge/materials"
	"github.com/Joker20380/family_connect/desktopbridge/normal"
	"github.com/Joker20380/family_connect/desktopbridge/platform"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

var sourceManifest = "development-unsealed"

func main() {
	if len(os.Args) == 2 && os.Args[1] == "--version" {
		json.NewEncoder(os.Stdout).Encode(map[string]any{"bridge_protocol": worker.Schema, "core_reference": "android106-native105", "source_manifest": sourceManifest,
			"materials_protocol": 1, "auto_policy_protocol": automatic.Schema, "normal_configuration_protocol": normal.Schema,
			"chat_ipc_protocol": chatipc.Schema, "private_chat_endpoint": chatEndpoint,
			"os": runtime.GOOS, "arch": runtime.GOARCH, "go": runtime.Version(), "profiles": []string{"P0", "P1"}})
		return
	}
	chatMode := len(os.Args) == 3 && os.Args[1] == "--stdio-chat-fd"
	directMode := len(os.Args) == 3 && os.Args[1] == "--chat-direct-fd" && runtime.GOOS == "linux" && os.Geteuid() == 0
	if !directMode && !chatMode && (len(os.Args) != 2 || (os.Args[1] != "--stdio" && os.Args[1] != "--materials-stdio" && os.Args[1] != "--auto-stdio" && os.Args[1] != "--normal-stdio")) {
		fmt.Fprintln(os.Stderr, "Service-owned Family Connect MESH worker; use the desktop application.")
		os.Exit(64)
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	go func() { <-ctx.Done(); os.Stdin.Close() }()
	var err error
	if directMode {
		connection, openError := inheritedChat(os.Args[2])
		err = openError
		if err == nil {
			err = direct.Serve(ctx, connection, platform.Native{})
		}
	} else if chatMode {
		connection, openError := inheritedChat(os.Args[2])
		err = openError
		if err == nil {
			owner := &restrictedchat.Owner{}
			chatContext, stopChat := context.WithCancel(ctx)
			finished := make(chan struct{})
			go func() { defer close(finished); chatipc.Serve(chatContext, connection, owner, platform.Native{}) }()
			err = worker.ServeWithOwner(ctx, os.Stdin, os.Stdout, platform.Native{}, owner)
			stopChat()
			connection.Close()
			<-finished
		}
	} else if os.Args[1] == "--normal-stdio" {
		err = normal.Serve(ctx, os.Stdin, os.Stdout, platform.Native{})
	} else if os.Args[1] == "--auto-stdio" {
		err = automatic.Serve(ctx, os.Stdin, os.Stdout)
	} else if os.Args[1] == "--materials-stdio" {
		err = materials.Serve(ctx, os.Stdin, os.Stdout, platform.Native{})
	} else {
		err = worker.Serve(ctx, os.Stdin, os.Stdout, platform.Native{})
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "MESH_WORKER_FAILED")
		os.Exit(1)
	}
}
