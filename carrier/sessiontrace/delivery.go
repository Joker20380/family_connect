package sessiontrace

const DeliveryLimit = 8

type Flow struct {
	SendBase    uint64 `json:"send_base"`
	SendNext    uint64 `json:"send_next"`
	ReceiveNext uint64 `json:"receive_next"`
	ReceiveMask uint32 `json:"receive_mask"`
	ACKSeen     bool   `json:"ack_seen"`
	ACKBase     uint64 `json:"ack_base"`
	ACKMask     uint32 `json:"ack_mask"`
	Pending     uint32 `json:"pending"`
	Buffered    uint32 `json:"buffered"`
	HeadRetries uint32 `json:"head_retries"`
	HeadSacked  bool   `json:"head_sacked"`
}

type Fragment struct {
	Sender       uint32 `json:"sender"`
	Message      uint32 `json:"message"`
	Total        uint32 `json:"total"`
	Mask         uint32 `json:"mask"`
	DataKnown    bool   `json:"data_known"`
	DataSequence uint64 `json:"data_sequence"`
}

type Assembly struct {
	Fragments uint64 `json:"fragments"`
	Completed uint64 `json:"completed"`
	Expired   uint64 `json:"expired"`
	Malformed uint64 `json:"malformed"`
	Duplicate uint64 `json:"duplicate"`
	Conflict  uint64 `json:"conflict"`
	Capacity  uint64 `json:"capacity"`
	CRCFailed uint64 `json:"crc_failed"`
	Recent    uint64 `json:"recent"`
	Pending   uint32 `json:"pending"`
	RTP       uint64 `json:"rtp"`
	RTPGaps   uint64 `json:"rtp_gaps"`
	VP8Frames uint64 `json:"vp8_frames"`
}

type Delivery struct {
	Boundaries *Boundaries `json:"boundaries,omitempty"`
	Flow       *Flow       `json:"flow,omitempty"`
	Assembly   *Assembly   `json:"assembly,omitempty"`
	Pending    *Fragment   `json:"pending,omitempty"`
	Queued     *Fragment   `json:"queued,omitempty"`
	Written    *Fragment   `json:"written,omitempty"`
	Received   *Fragment   `json:"received,omitempty"`
}

func copyValue[Value any](value *Value) *Value {
	if value == nil {
		return nil
	}
	copy := *value
	return &copy
}

func CloneDelivery(value *Delivery) *Delivery {
	if value == nil {
		return nil
	}
	return &Delivery{Flow: copyValue(value.Flow), Assembly: copyValue(value.Assembly),
		Boundaries: cloneBoundaries(value.Boundaries),
		Pending:    copyValue(value.Pending), Queued: copyValue(value.Queued),
		Written: copyValue(value.Written), Received: copyValue(value.Received)}
}

func cloneBoundaries(value *Boundaries) *Boundaries {
	if value == nil {
		return nil
	}
	return &Boundaries{Dropped: value.Dropped, Events: append([]Boundary(nil), value.Events...)}
}

func cloneEvent(value Event) Event {
	value.Delivery = CloneDelivery(value.Delivery)
	return value
}
