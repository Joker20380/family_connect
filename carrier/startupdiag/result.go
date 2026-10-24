package startupdiag

type Result struct {
	Schema                    int                 `json:"schema"`
	Attempt                   int64               `json:"attempt"`
	StartedUnixMS             int64               `json:"started_unix_ms"`
	ObservedMS                int64               `json:"observed_ms"`
	CompletedMS               int64               `json:"completed_ms"`
	Complete                  bool                `json:"complete"`
	Status                    string              `json:"status"`
	Stage                     string              `json:"stage"`
	Cause                     string              `json:"cause"`
	DirectoryFingerprint      string              `json:"directory_fingerprint,omitempty"`
	Observation               *Observation        `json:"observation,omitempty"`
	LocalStop                 *LocalStop          `json:"local_stop,omitempty"`
	BootstrapExchanges        []BootstrapExchange `json:"bootstrap_exchanges,omitempty"`
	BootstrapExchangesDropped uint64              `json:"bootstrap_exchanges_dropped,omitempty"`
}

const BootstrapExchangeLimit = 4

type BootstrapExchange struct {
	Tag                 string `json:"bootstrap_exchange_tag"`
	FamilyAuthenticated bool   `json:"family_authenticated"`
}

type Observation struct {
	BootstrapExchangeTag string `json:"bootstrap_exchange_tag,omitempty"`
	Point                string `json:"point"`
	ErrorCategory        string `json:"error_category"`
	ContextState         string `json:"context_state"`
	StopAtObservation    string `json:"stop_at_observation"`
	ElapsedMS            int64  `json:"elapsed_ms"`
}

type LocalStop struct {
	Source    string `json:"source"`
	ElapsedMS int64  `json:"elapsed_ms"`
}
