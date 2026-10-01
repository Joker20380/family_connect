package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

func main() {
	var input struct {
		Directory json.RawMessage `json:"directory"`
		Family    string          `json:"family"`
		Gateway   string          `json:"gateway"`
		NowNS     int64           `json:"now_ns"`
		Serialize bool            `json:"serialize"`
	}
	if json.NewDecoder(io.LimitReader(os.Stdin, 20000)).Decode(&input) != nil {
		os.Exit(1)
	}
	directory, err := bootstrap.ParseDirectory(input.Directory, input.Family, input.Gateway, time.Unix(0, input.NowNS))
	if err != nil {
		fmt.Fprintln(os.Stderr, "directory_rejected")
		os.Exit(1)
	}
	if input.Serialize {
		if json.NewEncoder(os.Stdout).Encode(directory) != nil {
			os.Exit(1)
		}
	} else {
		fmt.Println("compatible")
	}
}
