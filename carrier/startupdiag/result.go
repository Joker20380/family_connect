package startupdiag

type Result struct {
	Schema        int    `json:"schema"`
	Attempt       int64  `json:"attempt"`
	StartedUnixMS int64  `json:"started_unix_ms"`
	ObservedMS    int64  `json:"observed_ms"`
	CompletedMS   int64  `json:"completed_ms"`
	Complete      bool   `json:"complete"`
	Status        string `json:"status"`
	Stage         string `json:"stage"`
	Cause         string `json:"cause"`
}
