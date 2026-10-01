package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func main() {
	if check() != nil {
		fmt.Fprintln(os.Stderr, "delivery compatibility failed")
		os.Exit(1)
	}
	fmt.Println("compatible")
}

func check() error {
	var input struct {
		Response json.RawMessage `json:"response"`
		Identity []byte          `json:"identity"`
		Public   []byte          `json:"public"`
		Anchor   []byte          `json:"anchor"`
		Now      int64           `json:"now"`
		NowNS    int64           `json:"now_ns"`
	}
	if err := json.NewDecoder(io.LimitReader(os.Stdin, 70000)).Decode(&input); err != nil {
		return wholedevice.ErrClosed
	}
	defer clear(input.Identity)
	now := time.Unix(input.Now, 0)
	if input.NowNS != 0 {
		now = time.Unix(0, input.NowNS)
	}
	if len(input.Public) != 0 {
		delivery, credentials, err := wholedevice.ValidateDelivery(input.Response, input.Public, input.Anchor, now)
		if err != nil {
			return err
		}
		_, err = bootstrap.ParseDirectory(delivery.Directory, credentials.Family, credentials.Gateway, now)
		return err
	}
	profile, rawDirectory, err := wholedevice.DeliveryMaterial(input.Response, input.Identity, input.Anchor, now)
	if err != nil {
		return err
	}
	defer clear(profile)
	var credentials familysession.Credentials
	if json.Unmarshal(profile, &credentials) != nil || credentials.MinimumRevision != 1 {
		return wholedevice.ErrClosed
	}
	if _, _, err = familysession.Configuration(profile, false); err != nil {
		return err
	}
	_, err = bootstrap.ParseDirectory(rawDirectory, credentials.Family, credentials.Gateway, now)
	return err
}
