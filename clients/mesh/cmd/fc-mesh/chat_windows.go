package main

import (
	"github.com/Joker20380/family_connect/desktopbridge/worker"
	"net"
)

const chatEndpoint = "NOT_INTEGRATED"

func inheritedChat(value string) (net.Conn, error) { return nil, worker.ErrProtocol }
