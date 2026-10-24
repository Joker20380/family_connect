package tcpforward

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"io"
	"testing"
	"time"
	"unsafe"
)

func lifecycleMux(test *testing.T, window int) *Mux {
	ctx, cancel := context.WithCancel(context.Background())
	test.Cleanup(cancel)
	return &Mux{window: window, ctx: ctx, cancel: cancel, config: MuxConfig{Lifecycle: true}, streams: make(map[uint32]*MuxStream), changed: make(chan struct{})}
}

func lifecycleRetire(mux *Mux, id uint32) *MuxStream {
	stream := mux.makeStreamLocked(id)
	stream.opened = true
	mux.lifeLocked("opened", id, openOK, "peer")
	stream.sendCredit -= 24
	stream.resetLocked(ErrReset)
	stream.send = nil
	mux.lifeLocked("send_done", id, resetFrame, "local")
	mux.removeLocked(id)
	return stream
}

func lifecycleCredit(id uint32, credit int) muxFrame {
	payload := make([]byte, 4)
	binary.BigEndian.PutUint32(payload, uint32(credit))
	return muxFrame{muxWindowUpdate, id, payload}
}

func TestLifecycle101CrossingContract(test *testing.T) {
	for _, window := range []int{65536, 131072} {
		mux := lifecycleMux(test, window)
		retired := lifecycleRetire(mux, 47)
		neighbor := mux.makeStreamLocked(49)
		neighbor.opened = true
		for _, frame := range []muxFrame{lifecycleCredit(47, 24), {dataFrame, 47, []byte("in flight")}, {finFrame, 47, nil}, {resetFrame, 47, nil}} {
			mux.dispatchLocked(frame)
		}
		snapshot := mux.lifeSnapshotLocked()
		if snapshot.Expected != 4 || snapshot.Violations != 0 || snapshot.Unclassified != 0 || mux.stats.ProtocolErrors != 4 {
			test.Fatalf("unexpected classification %+v", snapshot)
		}
		if retired.receive != nil || retired.send != nil || retired.used != 0 || mux.streams[47] != nil {
			test.Fatal("resurrected resources")
		}
		mux.dispatchLocked(muxFrame{dataFrame, 49, []byte("neighbor")})
		output := make([]byte, 8)
		count, err := neighbor.Read(output)
		if err != nil || !bytes.Equal(output[:count], []byte("neighbor")) {
			test.Fatal("neighbor")
		}
		mux.dispatchLocked(muxFrame{resetFrame, 47, nil})
		if mux.lifeSnapshotLocked().Violations != 1 {
			test.Fatal("duplicate after ordered terminal hidden")
		}
	}
}

func TestLifecycle101NegativeContract(test *testing.T) {
	for _, window := range []int{65536, 131072} {
		for _, name := range []string{"credit", "fin", "data_fin", "close", "malformed", "peer_reset", "protocol"} {
			test.Run(name, func(test *testing.T) {
				mux := lifecycleMux(test, window)
				lifecycleRetire(mux, 7)
				record := &mux.life.removed[0]
				frame := muxFrame{finFrame, 7, nil}
				switch name {
				case "credit":
					frame = lifecycleCredit(7, 25)
				case "fin":
					record.RemoteFIN = true
				case "data_fin":
					record.RemoteFIN = true
					frame = muxFrame{dataFrame, 7, []byte("bad")}
				case "close":
					frame = muxFrame{closeFrame, 7, nil}
				case "malformed":
					frame = muxFrame{resetFrame, 7, []byte("bad")}
				case "peer_reset":
					record.PeerTerminal = true
				case "protocol":
					record.Reason = "protocol"
				}
				mux.dispatchLocked(frame)
				if mux.lifeSnapshotLocked().Violations != 1 || mux.stats.ProtocolErrors != 1 {
					test.Fatal("violation waived")
				}
			})
		}
	}
}

func TestLifecycle101GracefulTailAndAbort(test *testing.T) {
	for _, window := range []int{65536, 131072} {
		mux := lifecycleMux(test, window)
		stream := mux.makeStreamLocked(51)
		stream.opened = true
		mux.lifeLocked("opened", 51, openOK, "peer")
		mux.dispatchLocked(muxFrame{dataFrame, 51, []byte("tail")})
		mux.dispatchLocked(muxFrame{finFrame, 51, nil})
		if err := stream.CloseWrite(); err != nil {
			test.Fatal(err)
		}
		if stream.terminal != nil || stream.used != 4 {
			test.Fatal("half-close discarded tail")
		}
		output, err := io.ReadAll(stream)
		if err != nil || string(output) != "tail" {
			test.Fatal("tail", err)
		}
		stream.finishLocked(io.EOF)
		mux.removeLocked(51)
		mux.dispatchLocked(muxFrame{resetFrame, 51, nil})
		if mux.lifeSnapshotLocked().Expected != 1 {
			test.Fatal("crossed final reset")
		}
		mux.dispatchLocked(muxFrame{dataFrame, 51, []byte("bad")})
		if mux.lifeSnapshotLocked().Violations != 1 {
			test.Fatal("DATA after graceful close")
		}
	}
}

func TestLifecycle101BoundsExpiryAndGeneration(test *testing.T) {
	mux := lifecycleMux(test, 131072)
	for index := uint32(1); index < 2001; index += 2 {
		lifecycleRetire(mux, index)
		mux.dispatchLocked(muxFrame{resetFrame, index, nil})
	}
	snapshot := mux.lifeSnapshotLocked()
	if len(snapshot.Incidents) != 32 || snapshot.IncidentDropped != 968 || snapshot.Expected != 1000 {
		test.Fatal("incident bounds")
	}
	if snapshot.Incidents[0].Stream.ID != 1 {
		test.Fatal("first context evicted by bulk")
	}
	snapshot.Incidents[0].Stream.SendDone[6] = 0
	if mux.lifeSnapshotLocked().Incidents[0].Stream.SendDone[6] == 0 {
		test.Fatal("aliased snapshot")
	}
	encoded, err := json.Marshal(mux.lifeSnapshotLocked())
	if err != nil || len(encoded) > 98304 || unsafe.Sizeof(mux.life) > 128*1024 {
		test.Fatal("export/memory bound", len(encoded), unsafe.Sizeof(mux.life))
	}
	fresh := lifecycleMux(test, 131072)
	fresh.dispatchLocked(muxFrame{resetFrame, 1999, nil})
	if fresh.lifeSnapshotLocked().Unclassified != 1 || fresh.stats.ProtocolErrors != 1 {
		test.Fatal("old session blessed")
	}
	lifecycleRetire(fresh, 7)
	fresh.life.removed[0].Removed = time.Now().Add(-61 * time.Second).UnixMilli()
	fresh.dispatchLocked(muxFrame{resetFrame, 7, nil})
	if fresh.lifeSnapshotLocked().Unclassified != 2 {
		test.Fatal("expiry waived")
	}
}

func TestLifecycle101LiveViolationAndPendingAbort(test *testing.T) {
	for _, window := range []int{65536, 131072} {
		mux := lifecycleMux(test, window)
		stream := mux.makeStreamLocked(1)
		stream.opened = true
		mux.lifeLocked("opened", 1, openOK, "peer")
		mux.dispatchLocked(lifecycleCredit(1, 1))
		if mux.lifeSnapshotLocked().Violations != 1 || stream.terminal != ErrProtocol {
			test.Fatal("live credit overflow")
		}
		stream = mux.makeStreamLocked(3)
		stream.opened = true
		mux.lifeLocked("opened", 3, openOK, "peer")
		stream.resetLocked(ErrReset)
		mux.dispatchLocked(muxFrame{finFrame, 3, nil})
		if mux.lifeSnapshotLocked().Expected != 1 || len(stream.send) != 1 || stream.send[0].kind != resetFrame {
			test.Fatal("pending reset crossing")
		}
		if count, err := stream.Write([]byte("late worker")); count != 0 || err != ErrReset {
			test.Fatal("late worker resurrected stream")
		}
	}
}
