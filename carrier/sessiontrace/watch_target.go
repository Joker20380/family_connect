package sessiontrace

type WatchTarget struct {
	Direction string `json:"direction"`
	Sequence  uint64 `json:"sequence"`
	Attempt   uint32 `json:"attempt"`
}
