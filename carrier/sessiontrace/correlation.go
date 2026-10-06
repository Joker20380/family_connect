//go:build fc_owner_diagnostic

package sessiontrace

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"time"
)

const CorrelationSchema = 1

func CorrelationEnabled() bool { return true }

func (recorder *Recorder) CorrelationMedia(point Boundary) {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	point.AtMS = time.Now().UnixMilli()
	recorder.correlationBoundary(point, time.Now())
}

const CandidateLimit = 4
const CorrelationFragments = 8

type CorrelationKey struct {
	Session    string `json:"session"`
	Direction  string `json:"direction"`
	Sequence   uint64 `json:"sequence"`
	Attempt    uint32 `json:"attempt"`
	Generation string `json:"generation"`
}

type MediaIdentity struct {
	Fragment  uint32 `json:"fragment"`
	Total     uint32 `json:"total"`
	Picture   uint16 `json:"picture"`
	Timestamp uint32 `json:"timestamp"`
	First     uint16 `json:"first"`
	Last      uint16 `json:"last"`
	Packets   uint32 `json:"packets"`
}

type CorrelationDescriptor struct {
	Key     CorrelationKey  `json:"key"`
	Sender  uint32          `json:"sender"`
	Message uint32          `json:"message"`
	Media   []MediaIdentity `json:"media"`
}

type ProvisionalCandidate struct {
	callbacks     *ReceiverEvidence
	Sender        uint32                   `json:"sender"`
	Message       uint32                   `json:"message"`
	SequenceKnown bool                     `json:"sequence_known"`
	Media         map[uint32]MediaIdentity `json:"media"`
	Reconstructed map[uint32]bool          `json:"reconstructed"`
	Completed     bool                     `json:"completed"`
	FirstAtMS     int64                    `json:"first_at_ms"`
	LastAtMS      int64                    `json:"last_at_ms"`
}

type CorrelationReceipt struct {
	MediaComplete bool                   `json:"media_complete,omitempty"`
	Reliable      *ReceiverEvidence      `json:"reliable,omitempty"`
	Schema        int                    `json:"schema"`
	Key           CorrelationKey         `json:"key"`
	State         string                 `json:"state"`
	ExpiresAtMS   int64                  `json:"expires_at_ms"`
	Candidates    []ProvisionalCandidate `json:"candidates"`
	Descriptor    *CorrelationDescriptor `json:"descriptor,omitempty"`
}

type correlationWatch struct {
	legacy        *watchControl
	timer         *time.Timer
	excluded      [64][2]uint32
	excludedCount uint64
	value         CorrelationReceipt
	local         string
	deadline      time.Time
	identity      *Boundary
}

type correlationControl struct {
	watches map[string]*correlationWatch
	closed  bool
}

var correlationRejected = errors.New("diagnostic correlation rejected")

func (recorder *Recorder) closeCorrelation() {
	if recorder == nil {
		return
	}
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	recorder.correlation.closed = true
	for _, watch := range recorder.correlation.watches {
		watch.purge("CLOSED")
	}
}

func validGeneration(value string) bool {
	decoded, err := hex.DecodeString(value)
	return err == nil && len(decoded) == 16 && len(value) == 32
}

func (recorder *Recorder) PrearmCorrelation(key CorrelationKey, local string) (CorrelationReceipt, error) {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	if recorder.closing || recorder.correlation.closed || recorder.value.CorrelationStatus != "VALID" || key.Session != recorder.value.SessionTag ||
		!Allowed(key.Direction, "client_to_gateway|gateway_to_client") || !Allowed(local, "tx|rx") || key.Attempt > 32 ||
		key.Sequence == ^uint64(0) || recorder.correlation.watches[key.Direction] != nil {
		return CorrelationReceipt{}, correlationRejected
	}
	if local == "rx" {
		if key.Generation != "" {
			return CorrelationReceipt{}, correlationRejected
		}
		var nonce [16]byte
		if _, err := rand.Read(nonce[:]); err != nil {
			return CorrelationReceipt{}, correlationRejected
		}
		key.Generation = hex.EncodeToString(nonce[:])
	} else if !validGeneration(key.Generation) {
		return CorrelationReceipt{}, correlationRejected
	}
	if recorder.correlation.watches == nil {
		recorder.correlation.watches = make(map[string]*correlationWatch, 2)
	}
	deadline := time.Now().Add(EvidenceWatchTTL)
	watch := &correlationWatch{legacy: &recorder.watch, local: local, deadline: deadline, value: CorrelationReceipt{Schema: CorrelationSchema, Key: key, State: "ARMED", ExpiresAtMS: deadline.UnixMilli(), Candidates: []ProvisionalCandidate{}}}
	recorder.correlation.watches[key.Direction] = watch
	watch.timer = time.AfterFunc(EvidenceWatchTTL, func() { recorder.mu.Lock(); defer recorder.mu.Unlock(); watch.expire(time.Now()) })
	return cloneCorrelation(watch.value), nil
}

func (watch *correlationWatch) purge(state string) {
	if watch.local == "tx" && watch.legacy != nil && watch.legacy.value != nil && watch.legacy.value.Target.Sequence == watch.value.Key.Sequence && watch.legacy.value.Target.Attempt == watch.value.Key.Attempt {
		*watch.legacy = watchControl{}
	}
	if watch.timer != nil {
		watch.timer.Stop()
	}
	watch.excluded = [64][2]uint32{}
	watch.excludedCount = 0
	watch.value.Candidates = nil
	watch.value.Descriptor = nil
	watch.value.Reliable = nil
	watch.value.MediaComplete = false
	watch.identity = nil
	watch.value.State = state
}

func (watch *correlationWatch) expire(now time.Time) {
	if !now.Before(watch.deadline) && Allowed(watch.value.State, "ARMED|BOUND|CARRIER_COMPLETE|RELIABLE_ACCEPTED|CONSUMED|ACK_GENERATED|ACK_SENT|COMPLETE") {
		watch.purge("EXPIRED")
	}
}

func (recorder *Recorder) CorrelationStatus(key CorrelationKey, cleanup bool) (CorrelationReceipt, error) {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	watch := recorder.correlation.watches[key.Direction]
	if watch == nil || key != watch.value.Key {
		return CorrelationReceipt{}, correlationRejected
	}
	watch.expire(time.Now())
	if cleanup {
		watch.purge("CLEANED")
	}
	return cloneCorrelation(watch.value), nil
}

func validMedia(media []MediaIdentity) bool {
	if len(media) == 0 || len(media) > CorrelationFragments {
		return false
	}
	for index, point := range media {
		if point.Fragment != uint32(index) || point.Total != uint32(len(media)) || point.Picture > 32767 || point.Packets == 0 || point.Packets > 256 || uint32(uint16(point.Last-point.First))+1 != point.Packets {
			return false
		}
	}
	return true
}

func (recorder *Recorder) BindCorrelation(descriptor CorrelationDescriptor) (CorrelationReceipt, error) {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	watch := recorder.correlation.watches[descriptor.Key.Direction]
	if watch == nil {
		return CorrelationReceipt{}, correlationRejected
	}
	watch.expire(time.Now())
	if watch.local != "rx" || descriptor.Key != watch.value.Key || watch.value.State != "ARMED" || !validMedia(descriptor.Media) {
		return CorrelationReceipt{}, correlationRejected
	}
	descriptor.Media = append([]MediaIdentity(nil), descriptor.Media...)
	watch.value.Descriptor = &descriptor
	watch.value.State = "BOUND"
	watch.complete()
	return cloneCorrelation(watch.value), nil
}

func (watch *correlationWatch) complete() {
	descriptor := watch.value.Descriptor
	if descriptor == nil {
		return
	}
	for _, candidate := range watch.value.Candidates {
		if candidate.Sender != descriptor.Sender || candidate.Message != descriptor.Message || !candidate.SequenceKnown || !candidate.Completed || len(candidate.Media) != len(descriptor.Media) {
			continue
		}
		for _, media := range descriptor.Media {
			if candidate.Media[media.Fragment] != media || (watch.local == "rx" && !candidate.Reconstructed[media.Fragment]) {
				return
			}
		}
		watch.value.MediaComplete = true
		if watch.local == "tx" {
			watch.value.State = "COMPLETE"
			return
		}
		watch.value.State = "CARRIER_COMPLETE"
		watch.value.Reliable = candidate.callbacks
		if candidate.callbacks == nil {
			return
		}
		watch.value.State = "RELIABLE_ACCEPTED"
		if candidate.callbacks.Consumed == nil {
			return
		}
		watch.value.State = "CONSUMED"
		if candidate.callbacks.ACK == nil {
			return
		}
		watch.value.State = "ACK_GENERATED"
		if candidate.callbacks.ACK.SentNS == 0 || candidate.callbacks.ACK.Result != "ok" {
			return
		}
		watch.value.State = "COMPLETE"
		return
	}
}

func (recorder *Recorder) correlationBoundary(point Boundary, now time.Time) {
	for _, watch := range recorder.correlation.watches {
		watch.expire(now)
		if !Allowed(watch.value.State, "ARMED|BOUND") || point.Direction != watch.local || !point.MessageKnown ||
			(!Allowed(point.Result, "ok|duplicate|recent") && !(watch.local == "tx" && point.Stage == "carrier_written" && point.Result == "incomplete")) {
			continue
		}
		identity := [2]uint32{point.Sender, point.Message}
		if point.DataKnown && point.DataSequence != watch.value.Key.Sequence {
			watch.excluded[watch.excludedCount%64] = identity
			watch.excludedCount++
			for index, candidate := range watch.value.Candidates {
				if candidate.Sender == point.Sender && candidate.Message == point.Message {
					watch.value.Candidates = append(watch.value.Candidates[:index], watch.value.Candidates[index+1:]...)
					break
				}
			}
			continue
		}
		excluded := false
		for index := uint64(0); index < min(watch.excludedCount, 64); index++ {
			if watch.excluded[index] == identity {
				excluded = true
				break
			}
		}
		if excluded {
			continue
		}
		if watch.local == "tx" {
			if point.DataKnown && point.AttemptKnown && point.Attempt == watch.value.Key.Attempt && Allowed(point.Stage, "carrier_queued|carrier_written") {
				if watch.identity != nil && (watch.identity.Sender != point.Sender || watch.identity.Message != point.Message) {
					watch.purge("CONFLICT")
					continue
				}
				copy := point
				watch.identity = &copy
			}
			if watch.identity == nil || watch.identity.Sender != point.Sender || watch.identity.Message != point.Message {
				continue
			}
		}
		if !Allowed(point.Stage, "rtp_written|rtp_correlated|vp8_reassembled|carrier_message_completed") {
			continue
		}
		if point.Total == 0 || point.Total > CorrelationFragments || point.Fragment >= point.Total {
			continue
		}
		candidateIndex := -1
		for index, candidate := range watch.value.Candidates {
			if candidate.Sender == point.Sender && candidate.Message == point.Message {
				candidateIndex = index
				break
			}
		}
		if candidateIndex < 0 {
			if len(watch.value.Candidates) == CandidateLimit {
				watch.purge("OVERFLOW")
				continue
			}
			watch.value.Candidates = append(watch.value.Candidates, ProvisionalCandidate{Sender: point.Sender, Message: point.Message, Media: map[uint32]MediaIdentity{}, Reconstructed: map[uint32]bool{}, FirstAtMS: point.AtMS})
			candidateIndex = len(watch.value.Candidates) - 1
		}
		candidate := &watch.value.Candidates[candidateIndex]
		candidate.LastAtMS = point.AtMS
		candidate.SequenceKnown = candidate.SequenceKnown || (point.DataKnown && point.DataSequence == watch.value.Key.Sequence)
		if Allowed(point.Stage, "rtp_written|rtp_correlated") && point.PictureKnown && point.FrameKnown {
			media := MediaIdentity{Fragment: point.Fragment, Total: point.Total, Picture: point.PictureID, Timestamp: point.Timestamp, First: point.FirstRTP, Last: point.LastRTP, Packets: point.Packets}
			if prior, exists := candidate.Media[point.Fragment]; exists && prior != media {
				watch.purge("CONFLICT")
				continue
			}
			candidate.Media[point.Fragment] = media
		}
		if point.Stage == "vp8_reassembled" {
			candidate.Reconstructed[point.Fragment] = true
		}
		if point.Stage == "carrier_message_completed" && point.Result == "ok" {
			candidate.Completed = true
		}
		if watch.local == "tx" && len(candidate.Media) == int(point.Total) {
			media := make([]MediaIdentity, point.Total)
			for index := range media {
				media[index] = candidate.Media[uint32(index)]
			}
			if validMedia(media) {
				candidate.Completed = true
				candidate.SequenceKnown = true
				watch.value.Descriptor = &CorrelationDescriptor{Key: watch.value.Key, Sender: candidate.Sender, Message: candidate.Message, Media: media}
			}
		}
		watch.complete()
	}
}

func (recorder *Recorder) correlationEvent(event Event) {
	if Allowed(event.Stage, "LOCAL_CLOSE|REMOTE_CLOSE|CLEANUP") || Allowed(event.State, "FAILED|CLOSED") {
		recorder.correlation.closed = true
		for _, watch := range recorder.correlation.watches {
			watch.purge("CLOSED")
		}
	}
}

func cloneCorrelation(value CorrelationReceipt) CorrelationReceipt {
	value.Reliable = cloneReceiver(value.Reliable)
	value.Candidates = append([]ProvisionalCandidate(nil), value.Candidates...)
	for index := range value.Candidates {
		candidate := &value.Candidates[index]
		candidate.callbacks = cloneReceiver(candidate.callbacks)
		media := make(map[uint32]MediaIdentity, len(candidate.Media))
		for key, item := range candidate.Media {
			media[key] = item
		}
		candidate.Media = media
		reconstructed := make(map[uint32]bool, len(candidate.Reconstructed))
		for key, item := range candidate.Reconstructed {
			reconstructed[key] = item
		}
		candidate.Reconstructed = reconstructed
	}
	if value.Descriptor != nil {
		descriptor := *value.Descriptor
		descriptor.Media = append([]MediaIdentity(nil), descriptor.Media...)
		value.Descriptor = &descriptor
	}
	return value
}
