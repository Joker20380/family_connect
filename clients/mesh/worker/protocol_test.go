package worker

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"testing"
)

func frame(raw []byte) []byte {
	result := make([]byte, 4+len(raw))
	binary.BigEndian.PutUint32(result[:4], uint32(len(raw)))
	copy(result[4:], raw)
	return result
}

func TestStrictBoundedPrivateProtocol(test *testing.T) {
	for _, raw := range []string{
		`{"schema":1,"id":1,"action":"status","exec":"bad"}`,
		`{"schema":1,"id":1,"id":2,"action":"status"}`,
		`{"schema":1,"id":1,"action":"start","start":{"readiness":{"key":1,"key":2}}}`,
		`{"schema":2,"id":1,"action":"status"}`,
		`{"schema":1,"id":0,"action":"status"}`,
		`{"schema":1,"id":1,"action":"shell"}`,
		`{"schema":1,"id":1,"action":"start"}`,
		`{"schema":1,"id":1,"action":"status","start":{}}`,
		`{"schema":1,"id":1,"action":"status"} {}`,
		`null`,
		strings.Repeat("[", 18) + strings.Repeat("]", 18),
	} {
		if request, err := ReadRequest(bytes.NewReader(frame([]byte(raw)))); err == nil {
			request.Start.Erase()
			test.Fatal("malformed command accepted")
		}
	}
	for _, raw := range [][]byte{nil, {0, 0, 0, 0}, {255, 255, 255, 255}, {0, 0, 0, 10, '{', '}'}} {
		if _, err := ReadRequest(bytes.NewReader(raw)); err == nil {
			test.Fatal("invalid frame accepted")
		}
	}
	request, err := ReadRequest(bytes.NewReader(frame([]byte(`{"schema":1,"id":12,"action":"status"}`))))
	if err != nil || request.ID != 12 || request.Action != "status" {
		test.Fatal("valid command rejected", err)
	}
}

func TestCommandFormattingAndErasure(test *testing.T) {
	start := &Start{Identity: []byte("SECRET_IDENTITY"), Readiness: []byte(`{"join_url":"SECRET_ROOM"}`), Anchor: []byte("ANCHOR")}
	request := Request{Schema: Schema, ID: 1, Action: "start", Start: start}
	if strings.Contains(fmt.Sprintf("%+v %#v %s %+v", request, request, request, start), "SECRET") {
		test.Fatal("command formatting leaked material")
	}
	start.Erase()
	for _, data := range [][]byte{start.Identity, start.Readiness, start.Anchor} {
		for _, value := range data {
			if value != 0 {
				test.Fatal("material was not erased")
			}
		}
	}
}

type shortWriter struct{}

func (shortWriter) Write(raw []byte) (int, error) { return len(raw) - 1, nil }

func TestReplyFramingAndShortWrites(test *testing.T) {
	reply := Reply{Schema: Schema, ID: 13, OK: true, State: "DISCONNECTED"}
	var output bytes.Buffer
	if WriteReply(&output, reply) != nil {
		test.Fatal("write")
	}
	raw := output.Bytes()
	if int(binary.BigEndian.Uint32(raw[:4])) != len(raw)-4 {
		test.Fatal("framing")
	}
	var decoded Reply
	if json.Unmarshal(raw[4:], &decoded) != nil || decoded.ID != 13 {
		test.Fatal("reply")
	}
	if WriteReply(shortWriter{}, reply) != io.ErrShortWrite {
		test.Fatal("partial write hidden")
	}
	if WriteReply(&output, Reply{Snapshot: map[string]any{"oversize": strings.Repeat("x", MaxReply)}}) == nil {
		test.Fatal("unbounded reply")
	}
}
