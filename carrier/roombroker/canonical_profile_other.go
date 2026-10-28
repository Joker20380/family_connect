//go:build !linux

package roombroker

func loadCanonicalProfile(path string) ([]byte, error) {
	return nil, Code("credentials_rejected")
}
