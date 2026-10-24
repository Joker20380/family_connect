package roombroker

import (
	"os"
	"path/filepath"
	"testing"
)

func TestMuxOperatorPolicy(test *testing.T) {
	directory := test.TempDir()
	os.Chmod(directory, 0700)
	test.Setenv("FC_DIAGNOSTIC_CONTROL_DIR", directory)
	path := filepath.Join(directory, "mux-profile")
	if enabled, err := muxCreditPolicy(); err != nil || enabled {
		test.Fatal(enabled, err)
	}
	for _, value := range []string{"LEGACY64", "CREDIT128", "unknown"} {
		if err := os.WriteFile(path, []byte(value), 0600); err != nil {
			test.Fatal(err)
		}
		enabled, err := muxCreditPolicy()
		if value == "unknown" {
			if err == nil {
				test.Fatal("invalid local policy accepted")
			}
		} else if err != nil || enabled != (value == "CREDIT128") {
			test.Fatal(enabled, err)
		}
	}
	os.Chmod(path, 0666)
	if _, err := muxCreditPolicy(); err == nil {
		test.Fatal("unprotected policy accepted")
	}
	os.Remove(path)
	os.Symlink("missing", path)
	if _, err := muxCreditPolicy(); err == nil {
		test.Fatal("symlink accepted")
	}
}
