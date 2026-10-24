package automatic

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
	"net"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Joker20380/family_connect/carrier/desktopauto"
	"github.com/Joker20380/family_connect/desktopbridge/worker"
)

type outputFrame struct {
	Reply  *Reply      `json:"reply,omitempty"`
	Call   *HostCall   `json:"host_call,omitempty"`
	Cancel *HostCancel `json:"host_cancel,omitempty"`
}

type harness struct {
	peer       net.Conn
	done       chan error
	write      sync.Mutex
	identifier uint64
}

func newHarness(test *testing.T, drain time.Duration) *harness {
	test.Helper()
	server, peer := net.Pipe()
	current := &harness{peer: peer, done: make(chan error, 1)}
	go func() { current.done <- serve(context.Background(), server, server, drain) }()
	test.Cleanup(func() {
		peer.Close()
		select {
		case <-current.done:
		case <-time.After(time.Second):
			test.Error("automatic process did not drain on EOF")
		}
	})
	return current
}

func (current *harness) send(test *testing.T, field string, value any) {
	test.Helper()
	current.write.Lock()
	defer current.write.Unlock()
	current.peer.SetWriteDeadline(time.Now().Add(time.Second))
	if err := encoded(current.peer, field, value); err != nil {
		test.Fatal("write failed", err)
	}
}

func (current *harness) command(test *testing.T, action string, generation uint64) uint64 {
	test.Helper()
	current.identifier++
	command := Command{Schema: Schema, ID: current.identifier, Action: action, Generation: generation}
	if action == "connect" {
		available := true
		command.Network = &available
	}
	current.send(test, "command", command)
	return command.ID
}

func (current *harness) next(test *testing.T) outputFrame {
	test.Helper()
	current.peer.SetReadDeadline(time.Now().Add(3 * time.Second))
	var frame outputFrame
	if err := worker.ReadControlMessage(current.peer, &frame, MaxFrame); err != nil {
		test.Fatal("read failed", err)
	}
	return frame
}

func (current *harness) accept(test *testing.T, call *HostCall, candidates ...desktopauto.Candidate) {
	test.Helper()
	if call == nil || call.Schema != Schema || call.ID == 0 || call.BudgetMS <= 0 || call.BudgetMS > 300000 {
		test.Fatal("invalid bounded host request", call)
	}
	accepted := true
	current.send(test, "host_reply", HostReply{Schema: Schema, ID: call.ID, OK: &accepted, Candidates: candidates})
}

func (current *harness) connected(test *testing.T) {
	test.Helper()
	current.command(test, "connect", 1)
	for _, operation := range []string{"configure", "close", "open", "remember"} {
		frame := current.next(test)
		if frame.Call == nil || frame.Call.Operation != operation || frame.Call.Generation != 1 {
			test.Fatal("wrong host sequence", operation, frame)
		}
		if operation == "configure" {
			current.accept(test, frame.Call, desktopauto.AWG)
		} else {
			current.accept(test, frame.Call)
		}
	}
	frame := current.next(test)
	if frame.Reply == nil || !frame.Reply.OK || frame.Reply.Snapshot.State != desktopauto.Connected ||
		frame.Reply.Snapshot.Selected != desktopauto.AWG || !frame.Reply.Snapshot.DesiredConnected {
		test.Fatal("not connected after verified host readiness", frame)
	}
}

func TestPolicyExecutesTypedHostAndDisconnects(test *testing.T) {
	current := newHarness(test, time.Second)
	current.connected(test)
	current.command(test, "status", 0)
	if reply := current.next(test).Reply; reply == nil || reply.Snapshot.State != desktopauto.Connected {
		test.Fatal("status lost live state")
	}
	current.command(test, "disconnect", 1)
	for _, operation := range []string{"close", "release"} {
		frame := current.next(test)
		if frame.Call == nil || frame.Call.Operation != operation {
			test.Fatal("unverified release sequence", frame)
		}
		current.accept(test, frame.Call)
	}
	frame := current.next(test)
	if frame.Reply == nil || !frame.Reply.OK || frame.Reply.Snapshot.State != desktopauto.Disconnected || frame.Reply.Snapshot.DesiredConnected {
		test.Fatal("disconnect did not release")
	}
}

func TestImmediateCancelDrainsHostBeforeCleanup(test *testing.T) {
	current := newHarness(test, time.Second)
	connect := current.command(test, "connect", 1)
	configured := current.next(test).Call
	if configured == nil || configured.Operation != "configure" {
		test.Fatal("expected configure")
	}
	disconnect := current.command(test, "disconnect", 1)
	frame := current.next(test)
	if frame.Cancel == nil || frame.Cancel.ID != configured.ID {
		test.Fatal("missing explicit host cancellation", frame)
	}
	current.command(test, "status", 0)
	if reply := current.next(test).Reply; reply == nil || reply.Snapshot.DesiredConnected {
		test.Fatal("cancel did not immediately clear user intent")
	}
	current.accept(test, configured, desktopauto.AWG)
	replies := map[uint64]bool{}
	operations := []string{}
	for !replies[connect] || !replies[disconnect] {
		frame = current.next(test)
		if frame.Call != nil {
			operations = append(operations, frame.Call.Operation)
			if frame.Call.Operation == "open" {
				test.Fatal("late configure completion opened a session")
			}
			current.accept(test, frame.Call)
		} else if frame.Reply != nil {
			if !frame.Reply.OK || frame.Reply.Snapshot.DesiredConnected {
				test.Fatal("cancelled generation was resurrected")
			}
			replies[frame.Reply.ID] = true
		} else {
			test.Fatal("unexpected frame", frame)
		}
	}
	if len(operations) == 0 || operations[len(operations)-1] != "release" {
		test.Fatal("cancel did not finish cleanup", operations)
	}
}

func TestDisconnectBeforeFirstHostRequestIsNotLost(test *testing.T) {
	current := newHarness(test, time.Second)
	connect := current.command(test, "connect", 7)
	disconnect := current.command(test, "disconnect", 7)
	configured := current.next(test).Call
	if configured == nil || configured.Operation != "configure" {
		test.Fatal("missing first host request")
	}
	frame := current.next(test)
	if frame.Cancel == nil || frame.Cancel.ID != configured.ID {
		test.Fatal("early disconnect raced past Connect initialization", frame)
	}
	current.accept(test, configured)
	finished := map[uint64]bool{}
	for !finished[connect] || !finished[disconnect] {
		frame = current.next(test)
		if frame.Call != nil {
			if frame.Call.Operation != "close" && frame.Call.Operation != "release" {
				test.Fatal("cancelled generation started a candidate")
			}
			current.accept(test, frame.Call)
		} else if frame.Reply != nil {
			if !frame.Reply.OK || frame.Reply.Snapshot.DesiredConnected {
				test.Fatal("early disconnect rejected", frame)
			}
			finished[frame.Reply.ID] = true
		} else {
			test.Fatal("unexpected cancel frame")
		}
	}
}

func TestCleanupFailureDoesNotReleaseOrPermitNewConnect(test *testing.T) {
	current := newHarness(test, time.Second)
	current.connected(test)
	current.command(test, "disconnect", 1)
	call := current.next(test).Call
	if call == nil || call.Operation != "close" {
		test.Fatal("missing cleanup")
	}
	denied := false
	current.send(test, "host_reply", HostReply{Schema: Schema, ID: call.ID, OK: &denied, Failure: desktopauto.Internal})
	if reply := current.next(test).Reply; reply == nil || reply.Snapshot.State != desktopauto.Failed || reply.Snapshot.DesiredConnected {
		test.Fatal("cleanup failure lost")
	}
	current.command(test, "connect", 2)
	if reply := current.next(test).Reply; reply == nil || reply.Error != "BUSY" {
		test.Fatal("cleanup failure allowed a new session")
	}
}

func TestDuplicateReplyRejectedEvenAfterDeliveryWasConsumed(test *testing.T) {
	call := &pendingCall{identifier: 1, operation: "close", reply: make(chan HostReply, 1)}
	host := &remoteHost{pending: call}
	ok := true
	reply := HostReply{Schema: Schema, ID: 1, OK: &ok}
	if host.receive(reply) != nil {
		test.Fatal("valid response rejected")
	}
	<-call.reply
	if !errors.Is(host.receive(reply), worker.ErrProtocol) {
		test.Fatal("duplicate reply accepted")
	}
}

func TestUnacknowledgedHostCancelTerminatesInsteadOfOverlapping(test *testing.T) {
	current := newHarness(test, 25*time.Millisecond)
	current.command(test, "connect", 1)
	if current.next(test).Call == nil {
		test.Fatal("missing configure")
	}
	current.command(test, "disconnect", 1)
	if current.next(test).Cancel == nil {
		test.Fatal("missing cancel")
	}
	current.peer.SetReadDeadline(time.Now().Add(time.Second))
	var frame outputFrame
	if worker.ReadControlMessage(current.peer, &frame, MaxFrame) == nil {
		test.Fatal("uncooperative host allowed another operation", frame)
	}
}

func TestStaleBusyAndTerminalAuthorization(test *testing.T) {
	current := newHarness(test, time.Second)
	connect := current.command(test, "connect", 2)
	configure := current.next(test).Call
	current.command(test, "retry", 2)
	if reply := current.next(test).Reply; reply == nil || reply.Error != "BUSY" {
		test.Fatal("overlapping attempt was queued")
	}
	current.command(test, "disconnect", 1)
	if reply := current.next(test).Reply; reply == nil || reply.Error != "STALE" {
		test.Fatal("old callback was not rejected")
	}
	denied := false
	current.send(test, "host_reply", HostReply{Schema: Schema, ID: configure.ID, OK: &denied, Failure: desktopauto.Auth})
	for {
		frame := current.next(test)
		if frame.Call != nil {
			if frame.Call.Operation != "close" {
				test.Fatal("authorization failure reached a weaker fallback", frame)
			}
			current.accept(test, frame.Call)
			continue
		}
		if frame.Reply == nil || frame.Reply.ID != connect || frame.Reply.Snapshot.State != desktopauto.Failed || frame.Reply.Snapshot.FirstReason != desktopauto.Auth {
			test.Fatal("authorization failure lost", frame)
		}
		break
	}
}

func TestLostTransportUsesSamePolicyRecovery(test *testing.T) {
	current := newHarness(test, time.Second)
	current.connected(test)
	current.identifier++
	current.send(test, "command", Command{Schema: Schema, ID: current.identifier, Action: "lost", Generation: 1, Reason: desktopauto.Network})
	for {
		frame := current.next(test)
		if frame.Call != nil {
			if frame.Call.Operation == "release" || frame.Call.Operation == "configure" {
				test.Fatal("recovery lost guard or reconfigured policy", frame)
			}
			current.accept(test, frame.Call)
			continue
		}
		if frame.Reply == nil || !frame.Reply.OK || frame.Reply.Snapshot.State != desktopauto.Connected || !frame.Reply.Snapshot.DesiredConnected {
			test.Fatal("immediate recovery not connected", frame)
		}
		break
	}
}

func TestDuplicateOrWrongHostReplyClosesSession(test *testing.T) {
	current := newHarness(test, time.Second)
	current.command(test, "connect", 1)
	call := current.next(test).Call
	ok := true
	current.send(test, "host_reply", HostReply{Schema: Schema, ID: call.ID + 1, OK: &ok})
	current.peer.SetReadDeadline(time.Now().Add(time.Second))
	var frame outputFrame
	if worker.ReadControlMessage(current.peer, &frame, MaxFrame) == nil {
		test.Fatal("wrong response ID accepted")
	}
}

func TestProtocolRejectsUnknownDuplicateOversizedAndMixedFrames(test *testing.T) {
	for _, text := range []string{
		`{}`, `{"command":null}`, `{"command":{"schema":1,"id":1,"action":"exec"}}`,
		`{"command":{"schema":1,"id":1,"id":2,"action":"status"}}`,
		`{"Command":{"schema":1,"id":1,"action":"status"}}`,
		`{"command":{"Schema":1,"id":1,"action":"status"}}`,
		`{"command":{"schema":1,"id":1,"ID":2,"action":"status"}}`,
		`{"command":{"schema":1,"id":1,"action":"status","preferred":""}}`,
		`{"command":{"schema":1,"id":1,"action":"status","generation":0}}`,
		`{"command":{"schema":1,"id":1,"action":"status","reason":null}}`,
		`{"host_reply":{"schema":1,"id":1,"OK":true}}`,
		`{"host_reply":{"schema":1,"id":1,"ok":true,"candidates":null}}`,
		`{"command":{"schema":1,"id":1,"action":"status","shell":"bad"}}`,
		`{"command":{"schema":1,"id":1,"action":"connect","generation":1}}`,
		`{"command":{"schema":1,"id":1,"action":"status"},"host_reply":{"schema":1,"id":1,"ok":true}}`,
		`{"host_reply":{"schema":1,"id":1,"ok":true,"failure":"AUTH"}}`,
		`{"host_reply":{"schema":1,"id":1,"ok":false,"failure":"AUTH","temporary_bootstrap":true}}`,
		`{"host_reply":{"schema":1,"id":1,"ok":true,"candidates":["restricted"]}}`,
		`{"host_reply":{"schema":1,"id":1,"ok":true,"candidates":["awg","awg"]}}`,
		`{"host_reply":{"schema":1,"id":1,"ok":null}}`,
		strings.Repeat("x", MaxFrame+1),
	} {
		var frame bytes.Buffer
		binary.Write(&frame, binary.BigEndian, uint32(len(text)))
		frame.WriteString(text)
		if _, err := read(&frame); !errors.Is(err, worker.ErrProtocol) {
			test.Fatal("accepted invalid frame", text[:min(len(text), 80)])
		}
	}
}

func TestNoSecretsOrUnboundedDiagnosticsInProtocol(test *testing.T) {
	value, err := json.Marshal(Reply{Schema: Schema, ID: 1, Snapshot: desktopauto.Snapshot{State: desktopauto.Connected}})
	if err != nil || bytes.Contains(value, []byte("identity")) || bytes.Contains(value, []byte("token")) || len(value) > MaxFrame {
		test.Fatal("protocol unexpectedly contains material")
	}
	if _, err := read(bytes.NewReader(nil)); !errors.Is(err, worker.ErrProtocol) && !errors.Is(err, io.EOF) {
		test.Fatal(err)
	}
}
