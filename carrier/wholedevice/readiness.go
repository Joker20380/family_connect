package wholedevice

import (
	"encoding/json"
	"os"
	"time"

	"github.com/Joker20380/family_connect/carrier/bootstrap"
	"github.com/Joker20380/family_connect/carrier/familysession"
)

type Readiness struct {
	Provisioning string `json:"restricted_provisioning"`
	Cache        string `json:"cache"`
	Valid        string `json:"structurally_valid"`
	Expired      string `json:"expired"`
	Usable       bool   `json:"usable"`
	Seeds        int    `json:"seeds"`
	Remaining    int64  `json:"remaining_seconds"`
}

func presence(path string) string {
	_, err := os.Lstat(path)
	if os.IsNotExist(err) {
		return "ABSENT"
	}
	if err != nil {
		return "UNKNOWN"
	}
	return "PRESENT"
}

func InspectReadiness(path, cachePath string, now time.Time) Readiness {
	result := Readiness{Provisioning: presence(path), Cache: presence(cachePath), Valid: "UNKNOWN", Expired: "UNKNOWN", Seeds: -1, Remaining: -1}
	raw, cache, err := profile(path, cachePath)
	if err != nil {
		return result
	}
	defer clear(raw)
	_, expiry, err := familysession.Configuration(raw, false)
	if err != nil || !expiry.After(now) {
		result.Provisioning = "INVALID"
		return result
	}
	return inspectDirectory(cache, result, now)
}

func inspectDirectory(cache *bootstrap.Cache, result Readiness, now time.Time) Readiness {
	if result.Cache != "PRESENT" {
		return result
	}
	cachePath := cache.Path
	info, err := os.Lstat(cachePath)
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || info.Size() > bootstrap.MaxDirectory {
		result.Valid = "NO"
		return result
	}
	directoryRaw, err := os.ReadFile(cachePath)
	if err != nil {
		return result
	}
	defer clear(directoryRaw)
	var directory bootstrap.Directory
	if json.Unmarshal(directoryRaw, &directory) != nil {
		result.Valid = "NO"
		return result
	}
	_, err = bootstrap.ParseDirectory(directoryRaw, cache.Family, cache.Gateway, directory.IssuedAt)
	if err != nil || directory.IssuedAt.After(now) {
		result.Valid = "NO"
		return result
	}
	result.Valid = "YES"
	result.Seeds = len(directory.Seeds)
	result.Remaining = int64(directory.ExpiresAt.Sub(now) / time.Second)
	result.Expired = "NO"
	if !directory.ExpiresAt.After(now) {
		result.Expired = "YES"
		return result
	}
	_, err = bootstrap.ParseDirectory(directoryRaw, cache.Family, cache.Gateway, now)
	result.Usable = err == nil
	return result
}
