package roombroker

import (
	"bytes"
	"crypto/tls"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"testing"

	"golang.org/x/sys/unix"
)

func canonicalFixture(test *testing.T) (string, []byte) {
	test.Helper()
	if os.Geteuid() != 0 {
		test.Skip("canonical ownership qualification requires the isolated root harness")
	}
	root, err := os.MkdirTemp("/run", "canonical-profile-test-")
	if err != nil {
		test.Fatal(err)
	}
	test.Cleanup(func() { os.RemoveAll(root) })
	if err := os.Chmod(root, 0755); err != nil {
		test.Fatal(err)
	}
	parent := filepath.Join(root, "profile")
	if err := os.Mkdir(parent, 0750); err != nil {
		test.Fatal(err)
	}
	if err := os.Chown(parent, 0, 41003); err != nil {
		test.Fatal(err)
	}
	if err := os.Chmod(parent, 0750); err != nil {
		test.Fatal(err)
	}
	path := filepath.Join(parent, "profile.json")
	raw := []byte(`{"synthetic":"profile-reader-fixture"}`)
	if err := os.WriteFile(path, raw, 0640); err != nil {
		test.Fatal(err)
	}
	if err := os.Chown(path, 0, 41003); err != nil {
		test.Fatal(err)
	}
	if err := os.Chmod(path, 0640); err != nil {
		test.Fatal(err)
	}
	return path, raw
}

func TestCanonicalProfileExactRead(test *testing.T) {
	path, expected := canonicalFixture(test)
	before, err := os.Lstat(path)
	if err != nil {
		test.Fatal(err)
	}
	parent, _, parentError := canonicalParent(path)
	if parentError != nil {
		test.Fatal("canonical parent rejected", parentError)
	}
	unix.Close(parent)
	raw, err := LoadCredentials(path)
	after, statError := os.Lstat(path)
	if err != nil || statError != nil || !bytes.Equal(raw, expected) || !os.SameFile(before, after) ||
		before.Mode() != after.Mode() || !before.ModTime().Equal(after.ModTime()) {
		test.Fatal("canonical read must preserve exact bytes and metadata", err, statError)
	}
}

func TestCanonicalProfileUnsafeBoundaryRejected(test *testing.T) {
	for _, variant := range []string{"file-mode", "file-owner", "file-group", "parent-mode", "parent-owner", "parent-group",
		"ancestor-write", "symlink", "hardlink", "ancestor-symlink", "empty", "oversize", "fifo", "file-xattr", "parent-xattr"} {
		test.Run(variant, func(test *testing.T) {
			path, _ := canonicalFixture(test)
			parent := filepath.Dir(path)
			var err error
			switch variant {
			case "file-mode":
				err = os.Chmod(path, 0644)
			case "file-owner":
				err = os.Chown(path, 41001, 41003)
			case "file-group":
				err = os.Chown(path, 0, 41004)
			case "parent-mode":
				err = os.Chmod(parent, 0770)
			case "parent-owner":
				err = os.Chown(parent, 41001, 41003)
			case "parent-group":
				err = os.Chown(parent, 0, 41004)
			case "ancestor-write":
				err = os.Chmod(filepath.Dir(parent), 0777)
			case "symlink":
				if err = os.Rename(path, path+".before"); err == nil {
					err = os.Symlink(path+".before", path)
				}
			case "hardlink":
				err = os.Link(path, path+".linked")
			case "ancestor-symlink":
				linked := filepath.Join(filepath.Dir(parent), "linked")
				err = os.Symlink(parent, linked)
				path = filepath.Join(linked, "profile.json")
			case "empty":
				err = os.WriteFile(path, nil, 0640)
			case "oversize":
				err = os.WriteFile(path, bytes.Repeat([]byte{'x'}, (48<<10)+1), 0640)
			case "fifo":
				if err = os.Remove(path); err == nil {
					err = unix.Mkfifo(path, 0640)
				}
			case "file-xattr":
				err = unix.Setxattr(path, "user.synthetic", []byte("fixture"), 0)
			case "parent-xattr":
				err = unix.Setxattr(parent, "user.synthetic", []byte("fixture"), 0)
			}
			if err != nil {
				test.Fatal("fixture setup failed", err)
			}
			if raw, err := LoadCredentials(path); err == nil || len(raw) != 0 {
				test.Fatal("unsafe canonical boundary accepted")
			}
		})
	}
}

func TestCanonicalProfilePrivateModeCompatibility(test *testing.T) {
	path := filepath.Join(test.TempDir(), "legacy-private.json")
	expected := []byte(`{"synthetic":"private-mode"}`)
	if err := os.WriteFile(path, expected, 0600); err != nil {
		test.Fatal(err)
	}
	if raw, err := LoadCredentials(path); err != nil || !bytes.Equal(raw, expected) {
		test.Fatal("existing private reader compatibility changed", err)
	}
}

func TestCanonicalProfileMountBoundaryRejected(test *testing.T) {
	if canonicalNoMounts("/proc") || canonicalNoMounts("/") {
		test.Fatal("mounted boundary accepted")
	}
}

func TestCanonicalProfileFamilyTLS(test *testing.T) {
	path, _ := canonicalFixture(test)
	fixtures := os.Getenv("FC_FAMILY_TEST_FIXTURES")
	if fixtures == "" {
		test.Fatal("fresh disposable Family TLS fixtures required for canonical gateway qualification")
	}
	raw, err := os.ReadFile(filepath.Join(fixtures, "gateway.json"))
	if err != nil {
		test.Fatal(err)
	}
	if err := os.WriteFile(path, raw, 0640); err != nil {
		test.Fatal(err)
	}
	config, err := ServerTLS(path)
	if err != nil || config == nil || config.GetConfigForClient == nil {
		test.Fatal("canonical Family TLS initialization failed", err)
	}
	fresh, err := config.GetConfigForClient(&tls.ClientHelloInfo{})
	if err != nil || fresh == nil || len(fresh.Certificates) != 1 {
		test.Fatal("canonical Family TLS reload failed", err)
	}
	if err := os.Chmod(path, 0660); err != nil {
		test.Fatal(err)
	}
	if _, err := config.GetConfigForClient(&tls.ClientHelloInfo{}); err == nil {
		test.Fatal("canonical Family TLS accepted unsafe replacement metadata")
	}
}

func TestCanonicalProfileReaderProcess(test *testing.T) {
	path := os.Getenv("FC_SYNTHETIC_PROFILE_TEST")
	if path == "" {
		return
	}
	raw, err := LoadCredentials(path)
	if os.Getenv("FC_SYNTHETIC_READER_GROUP") == "present" {
		if err != nil || len(raw) == 0 {
			test.Fatal("reader group cannot read", err)
		}
	} else if err == nil || len(raw) != 0 {
		test.Fatal("unrelated publisher can read profile")
	}
	descriptor, err := unix.Open(path, unix.O_WRONLY|unix.O_NOFOLLOW, 0)
	if err == nil {
		unix.Close(descriptor)
		test.Fatal("unprivileged reader can write profile")
	}
	descriptor, err = unix.Open(filepath.Join(filepath.Dir(path), "unauthorized-temp"), unix.O_CREAT|unix.O_EXCL|unix.O_WRONLY, 0600)
	if err == nil {
		unix.Close(descriptor)
		test.Fatal("unprivileged reader can create profile sibling")
	}
}

func TestCanonicalProfileReaderAccessWithoutWrite(test *testing.T) {
	for _, role := range []string{"gateway", "snapshot", "publisher"} {
		test.Run(role, func(test *testing.T) {
			path, _ := canonicalFixture(test)
			groups := []uint32{41002}
			allowed := "absent"
			if role != "publisher" {
				groups = append(groups, 41003)
				allowed = "present"
			}
			command := exec.Command(os.Args[0], "-test.run=^TestCanonicalProfileReaderProcess$")
			command.Env = append(os.Environ(), "FC_SYNTHETIC_PROFILE_TEST="+path, "FC_SYNTHETIC_READER_GROUP="+allowed)
			command.SysProcAttr = &syscall.SysProcAttr{Credential: &syscall.Credential{Uid: 41001, Gid: 41002, Groups: groups}}
			if output, err := command.CombinedOutput(); err != nil {
				test.Fatalf("reader qualification failed: %v: %s", err, output)
			}
		})
	}
}
