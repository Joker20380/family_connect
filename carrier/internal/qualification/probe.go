package qualification

import (
	"context"
	"encoding/json"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
)

func AdmissionProbe(parent context.Context, provider Provider, profilePath, directoryPath string) error {
	profile, err := os.ReadFile(profilePath)
	if err != nil {
		return err
	}
	defer clear(profile)
	raw, err := os.ReadFile(directoryPath)
	if err != nil {
		return err
	}
	var directory bootstrap.Directory
	if err := json.Unmarshal(raw, &directory); err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(parent, 40*time.Second)
	defer cancel()
	event := func(value string) {
		json.NewEncoder(os.Stdout).Encode(map[string]any{"event": value, "at": time.Now().UTC()})
	}
	_, err = bootstrap.RecoverWithConnector(ctx, directory, profile, event, provider.Seed)
	if err == nil {
		event("admission_allowed")
	}
	return err
}
