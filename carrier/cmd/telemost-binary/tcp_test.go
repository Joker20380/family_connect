package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestTCPConfigBounds(test *testing.T) {
	for _, scenario := range []struct {
		body  string
		valid bool
	}{
		{`{"host":"example.com","port":443,"mode":"https","path":"/"}`, true},
		{`{"host":"127.0.0.1","port":45678,"mode":"echo","seconds":300,"mbit":0.6}`, true},
		{`{"mode":"echo","seconds":300}`, false},
		{`{"mode":"echo","bytes":999999999}`, false},
		{`{"mode":"https","path":"/\r\nInjected: yes"}`, false},
		{`{"mode":"https","unknown":true}`, false},
		{`{"mode":"https"} {}`, false},
	} {
		path := filepath.Join(test.TempDir(), "tcp.json")
		if err := os.WriteFile(path, []byte(scenario.body), 0600); err != nil {
			test.Fatal(err)
		}
		_, err := readTCPConfig(path)
		if (err == nil) != scenario.valid {
			test.Fatal(scenario.body, err)
		}
	}
}

func TestTCPPayloadIndependentOfSegmentation(test *testing.T) {
	whole := make([]byte, 65536)
	fillTCP(whole, 0)
	for offset := 0; offset < len(whole); offset += 777 {
		chunk := make([]byte, min(777, len(whole)-offset))
		fillTCP(chunk, int64(offset))
		for index, value := range chunk {
			if value != whole[offset+index] {
				test.Fatal("segmentation")
			}
		}
	}
}
