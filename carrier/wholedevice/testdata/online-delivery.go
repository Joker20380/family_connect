package main

import (
	"encoding/json"
	"io"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func main() {
	var delivery struct {
		Response         json.RawMessage
		Identity, Anchor []byte
	}
	if json.NewDecoder(io.LimitReader(os.Stdin, 65536)).Decode(&delivery) != nil {
		os.Exit(1)
	}
	defer clear(delivery.Identity)
	profile, _, err := wholedevice.DeliveryMaterial(delivery.Response, delivery.Identity, delivery.Anchor, time.Now())
	if err != nil {
		os.Exit(1)
	}
	defer clear(profile)
	if _, err := os.Stdout.Write(profile); err != nil {
		os.Exit(1)
	}
}
