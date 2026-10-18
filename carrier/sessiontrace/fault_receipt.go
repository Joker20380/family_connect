package sessiontrace

type FaultReceipt struct {
	Schema       int    `json:"schema"`
	State        string `json:"state"`
	Target       string `json:"target"`
	Generation   string `json:"generation,omitempty"`
	Armed        bool   `json:"armed"`
	Consumed     bool   `json:"consumed"`
	Count        uint32 `json:"count"`
	Sequence     uint64 `json:"sequence,omitempty"`
	ArmedAtMS    int64  `json:"armed_at_ms,omitempty"`
	ConsumedAtMS int64  `json:"consumed_at_ms,omitempty"`
}
