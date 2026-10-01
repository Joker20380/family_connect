package bootstrap

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sync"
	"time"

	"golang.org/x/sys/unix"

	"github.com/Joker20380/family_connect/carrier/roombroker"
)

const MaxDirectory = 8192
const MaxSeeds = 4
const MaxAge = time.Hour

type Seed struct {
	Transport string `json:"transport"`
	JoinURL   string `json:"join_url"`
	Gateway   string `json:"gateway"`
}

type Directory struct {
	Version   int       `json:"version"`
	Family    string    `json:"family"`
	IssuedAt  time.Time `json:"issued_at"`
	ExpiresAt time.Time `json:"expires_at"`
	Seeds     []Seed    `json:"seeds"`
}

var directoryTimestamp = regexp.MustCompile(`^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,9})?(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$`)

func (directory Directory) MarshalJSON() ([]byte, error) {
	type plain Directory
	directory.IssuedAt = directory.IssuedAt.UTC()
	directory.ExpiresAt = directory.ExpiresAt.UTC()
	return json.Marshal(plain(directory))
}

func (directory *Directory) UnmarshalJSON(raw []byte) error {
	type plain Directory
	var decoded plain
	value := struct {
		*plain
		IssuedAt  string `json:"issued_at"`
		ExpiresAt string `json:"expires_at"`
	}{plain: &decoded}
	if strictJSON(raw, &value, MaxDirectory) != nil || !directoryTimestamp.MatchString(value.IssuedAt) || !directoryTimestamp.MatchString(value.ExpiresAt) {
		return roombroker.Code("directory_rejected")
	}
	issued, issuedErr := time.Parse(time.RFC3339Nano, value.IssuedAt)
	expires, expiresErr := time.Parse(time.RFC3339Nano, value.ExpiresAt)
	if issuedErr != nil || expiresErr != nil {
		return roombroker.Code("directory_rejected")
	}
	decoded.IssuedAt, decoded.ExpiresAt = issued.UTC(), expires.UTC()
	*directory = Directory(decoded)
	return nil
}

func (Seed) String() string        { return "[bootstrap seed redacted]" }
func (Seed) GoString() string      { return "[bootstrap seed redacted]" }
func (Directory) String() string   { return "[bootstrap directory redacted]" }
func (Directory) GoString() string { return "[bootstrap directory redacted]" }

func hexID(value string, size int) bool {
	raw, err := hex.DecodeString(value)
	return err == nil && len(raw) == size && hex.EncodeToString(raw) == value
}

func strictJSON(raw []byte, target any, limit int) error {
	if len(raw) == 0 || len(raw) > limit {
		return roombroker.Code("invalid_message")
	}
	var inspect func(*json.Decoder) error
	inspect = func(decoder *json.Decoder) error {
		token, err := decoder.Token()
		if err != nil {
			return err
		}
		switch token {
		case json.Delim('{'):
			seen := map[string]bool{}
			for decoder.More() {
				key, err := decoder.Token()
				name, ok := key.(string)
				if err != nil || !ok || seen[name] {
					return roombroker.Code("invalid_message")
				}
				seen[name] = true
				if err := inspect(decoder); err != nil {
					return err
				}
			}
			_, err = decoder.Token()
		case json.Delim('['):
			for decoder.More() {
				if err := inspect(decoder); err != nil {
					return err
				}
			}
			_, err = decoder.Token()
		}
		return err
	}
	if inspect(json.NewDecoder(bytes.NewReader(raw))) != nil {
		return roombroker.Code("invalid_message")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if decoder.Decode(target) != nil || decoder.Decode(new(any)) != io.EOF {
		return roombroker.Code("invalid_message")
	}
	return nil
}

func ParseDirectory(raw []byte, family, gateway string, now time.Time) (Directory, error) {
	var directory Directory
	if strictJSON(raw, &directory, MaxDirectory) != nil || directory.Version != 1 ||
		!hexID(family, 16) || directory.Family != family || !hexID(gateway, 16) ||
		directory.IssuedAt.After(now) || !directory.ExpiresAt.After(now) ||
		!directory.ExpiresAt.After(directory.IssuedAt) || directory.ExpiresAt.Sub(directory.IssuedAt) > MaxAge ||
		len(directory.Seeds) < 1 || len(directory.Seeds) > MaxSeeds {
		return Directory{}, roombroker.Code("directory_rejected")
	}
	seen := map[string]bool{}
	for _, seed := range directory.Seeds {
		if seed.Transport != "telemost-webrtc" || !roombroker.ValidJoinURL(seed.JoinURL) || seed.Gateway != gateway || seen[seed.JoinURL] {
			return Directory{}, roombroker.Code("directory_rejected")
		}
		seen[seed.JoinURL] = true
	}
	return directory, nil
}

type Cache struct {
	mu                    sync.Mutex
	Path, Family, Gateway string
}

func (cache *Cache) load(now time.Time) (Directory, error) {
	info, err := os.Lstat(cache.Path)
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || info.Size() > MaxDirectory {
		return Directory{}, roombroker.Code("cache_unavailable")
	}
	raw, err := os.ReadFile(cache.Path)
	if err != nil {
		return Directory{}, roombroker.Code("cache_unavailable")
	}
	return ParseDirectory(raw, cache.Family, cache.Gateway, now)
}

func (cache *Cache) Load(now time.Time) (Directory, error) {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	lock, err := cache.lock()
	if err != nil {
		return Directory{}, err
	}
	defer lock.Close()
	return cache.load(now)
}

func (cache *Cache) lock() (*os.File, error) {
	file, err := os.OpenFile(cache.Path+".lock", os.O_CREATE|os.O_RDWR|unix.O_NOFOLLOW, 0600)
	if err != nil {
		return nil, roombroker.Code("cache_unavailable")
	}
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 || unix.Flock(int(file.Fd()), unix.LOCK_EX|unix.LOCK_NB) != nil {
		file.Close()
		return nil, roombroker.Code("cache_busy_or_unprotected")
	}
	return file, nil
}

func (cache *Cache) Store(raw []byte, now time.Time) error {
	cache.mu.Lock()
	defer cache.mu.Unlock()
	lock, lockErr := cache.lock()
	if lockErr != nil {
		return lockErr
	}
	defer lock.Close()
	directory, err := ParseDirectory(raw, cache.Family, cache.Gateway, now)
	if err != nil {
		return err
	}
	previous, err := cache.load(now)
	if err == nil && !directory.IssuedAt.After(previous.IssuedAt) {
		old, _ := json.Marshal(previous)
		fresh, _ := json.Marshal(directory)
		if bytes.Equal(old, fresh) {
			return nil
		}
		return roombroker.Code("directory_stale")
	}
	pending := cache.Path + ".pending"
	if err := os.Remove(pending); err != nil && !os.IsNotExist(err) {
		return roombroker.Code("cache_write")
	}
	file, err := os.OpenFile(pending, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return roombroker.Code("cache_write")
	}
	defer os.Remove(file.Name())
	defer file.Close()
	if _, err = file.Write(raw); err == nil {
		err = file.Sync()
	}
	if err == nil {
		err = file.Close()
	}
	if err == nil {
		err = os.Rename(file.Name(), cache.Path)
	}
	if err != nil {
		return roombroker.Code("cache_write")
	}
	folder, err := os.Open(filepath.Dir(cache.Path))
	if err != nil {
		return roombroker.Code("cache_write")
	}
	defer folder.Close()
	if folder.Sync() != nil {
		return roombroker.Code("cache_write")
	}
	return nil
}
