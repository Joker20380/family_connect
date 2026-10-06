//go:build fc_owner_diagnostic

package sessiontrace

const BoundaryStages = "reliable_send|carrier_queued|carrier_written|rtp_written|rtp_received|vp8_reassembled|carrier_message_completed|reliable_data_accepted|reliable_consumed|ack_generated|ack_sent|ack_received|base_advanced"

type Boundary struct {
	Index        uint64 `json:"index"`
	AtMS         int64  `json:"at_ms"`
	Direction    string `json:"direction"`
	Stage        string `json:"stage"`
	Result       string `json:"result"`
	DataKnown    bool   `json:"data_known,omitempty"`
	DataSequence uint64 `json:"data_sequence,omitempty"`
	AttemptKnown bool   `json:"attempt_known,omitempty"`
	Attempt      uint32 `json:"attempt,omitempty"`
	MessageKnown bool   `json:"message_known,omitempty"`
	Sender       uint32 `json:"sender,omitempty"`
	Message      uint32 `json:"message,omitempty"`
	Fragment     uint32 `json:"fragment,omitempty"`
	Total        uint32 `json:"total,omitempty"`
	FrameKnown   bool   `json:"frame_known,omitempty"`
	Timestamp    uint32 `json:"timestamp,omitempty"`
	MediaTrack   uint32 `json:"media_track,omitempty"`
	FirstRTP     uint16 `json:"first_rtp,omitempty"`
	LastRTP      uint16 `json:"last_rtp,omitempty"`
	Packets      uint32 `json:"packets,omitempty"`
	PictureKnown bool   `json:"picture_known,omitempty"`
	PictureID    uint16 `json:"picture_id,omitempty"`
	ACKBase      uint64 `json:"ack_base,omitempty"`
	ACKMask      uint32 `json:"ack_mask,omitempty"`
}

type Snapshot struct {
	Watch             *EvidenceWatch `json:"evidence_watch,omitempty"`
	Fault             *FaultReceipt  `json:"fault,omitempty"`
	Boundaries        *Boundaries    `json:"boundaries,omitempty"`
	DeliveryDropped   uint64         `json:"delivery_dropped"`
	SessionTag        string         `json:"session_tag"`
	CorrelationStatus string         `json:"correlation_status"`
	Events            []Event        `json:"trace"`
	FirstFailure      *Event         `json:"first_failure,omitempty"`
	Dropped           uint64         `json:"trace_dropped"`
	ExportDropped     uint64         `json:"export_dropped"`
}

type Delivery struct {
	Watch      *EvidenceWatch `json:"evidence_watch,omitempty"`
	Boundaries *Boundaries    `json:"boundaries,omitempty"`
	Flow       *Flow          `json:"flow,omitempty"`
	Assembly   *Assembly      `json:"assembly,omitempty"`
	Pending    *Fragment      `json:"pending,omitempty"`
	Queued     *Fragment      `json:"queued,omitempty"`
	Written    *Fragment      `json:"written,omitempty"`
	Received   *Fragment      `json:"received,omitempty"`
}
