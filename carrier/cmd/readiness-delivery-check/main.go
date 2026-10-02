package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

func main() {
	var input struct {
		Response json.RawMessage `json:"response"`
		Public   []byte          `json:"public"`
		Anchor   []byte          `json:"anchor"`
		Now      int64           `json:"now"`
	}
	decoder := json.NewDecoder(io.LimitReader(os.Stdin, 70000))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&input) != nil || len(input.Public) != 64 || input.Now <= 0 {
		os.Exit(1)
	}
	if decoder.Decode(new(any)) != io.EOF {
		os.Exit(1)
	}
	if _, _, err := wholedevice.ValidateDelivery(input.Response, input.Public, input.Anchor, time.Unix(input.Now, 0)); err != nil {
		os.Exit(1)
	}
	fmt.Println("compatible")
}
