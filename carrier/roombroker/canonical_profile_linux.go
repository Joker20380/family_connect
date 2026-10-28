package roombroker

import (
	"errors"
	"io"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/unix"
)

func canonicalExtendedMetadata(descriptor int, directory bool) bool {
	size, err := unix.Flistxattr(descriptor, nil)
	if err != nil || size < 0 || size > 65536 {
		return false
	}
	names := make([]byte, max(size, 1))
	count, err := unix.Flistxattr(descriptor, names)
	if err != nil || count != 0 {
		return false
	}
	flags, err := unix.IoctlGetInt(descriptor, unix.FS_IOC_GETFLAGS)
	if err != nil {
		return errors.Is(err, unix.ENOTTY) || errors.Is(err, unix.EOPNOTSUPP)
	}
	structural := 0x80000
	if directory {
		structural |= 0x1000
	}
	return flags & ^structural == 0
}

func canonicalNoMounts(parent string) bool {
	raw, err := os.ReadFile("/proc/self/mountinfo")
	if err != nil {
		return false
	}
	decode := strings.NewReplacer(`\040`, " ", `\011`, "\t", `\012`, "\n", `\134`, `\`)
	for _, line := range strings.Split(string(raw), "\n") {
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) < 6 {
			return false
		}
		mounted := decode.Replace(fields[4])
		relative, err := filepath.Rel(parent, mounted)
		if err != nil || relative == "." || relative != ".." && !strings.HasPrefix(relative, "../") {
			return false
		}
	}
	return true
}

func canonicalParent(path string) (int, unix.Stat_t, error) {
	var metadata unix.Stat_t
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || path == "/" {
		return -1, metadata, Code("credentials_rejected")
	}
	parent := filepath.Dir(path)
	if !canonicalNoMounts(parent) {
		return -1, metadata, Code("credentials_rejected")
	}
	descriptor, err := unix.Open("/", unix.O_RDONLY|unix.O_DIRECTORY|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0)
	if err != nil {
		return -1, metadata, Code("credentials_rejected")
	}
	components := strings.Split(strings.TrimPrefix(parent, "/"), "/")
	for index := -1; index < len(components); index++ {
		if index >= 0 && components[index] != "" {
			next, err := unix.Openat(descriptor, components[index], unix.O_RDONLY|unix.O_DIRECTORY|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0)
			unix.Close(descriptor)
			if err != nil {
				return -1, metadata, Code("credentials_rejected")
			}
			descriptor = next
		}
		if unix.Fstat(descriptor, &metadata) != nil || metadata.Uid != 0 || metadata.Mode&unix.S_IFMT != unix.S_IFDIR ||
			metadata.Mode&0022 != 0 || !canonicalExtendedMetadata(descriptor, true) {
			unix.Close(descriptor)
			return -1, metadata, Code("credentials_rejected")
		}
	}
	if metadata.Mode&07777 != 0750 || metadata.Gid == 0 {
		unix.Close(descriptor)
		return -1, metadata, Code("credentials_rejected")
	}
	return descriptor, metadata, nil
}

func canonicalRegular(metadata unix.Stat_t, parent unix.Stat_t) bool {
	return metadata.Mode&unix.S_IFMT == unix.S_IFREG && metadata.Mode&07777 == 0640 && metadata.Uid == 0 &&
		metadata.Gid == parent.Gid && metadata.Nlink == 1 && metadata.Size > 0 && metadata.Size <= 48<<10 &&
		metadata.Dev == parent.Dev
}

func sameCanonicalFile(before, after unix.Stat_t) bool {
	return before.Dev == after.Dev && before.Ino == after.Ino && before.Size == after.Size && before.Mode == after.Mode &&
		before.Uid == after.Uid && before.Gid == after.Gid && before.Nlink == after.Nlink &&
		before.Mtim == after.Mtim && before.Ctim == after.Ctim
}

func loadCanonicalProfile(path string) ([]byte, error) {
	parent, boundary, err := canonicalParent(path)
	if err != nil {
		return nil, err
	}
	defer unix.Close(parent)
	descriptor, err := unix.Openat(parent, filepath.Base(path), unix.O_RDONLY|unix.O_NOFOLLOW|unix.O_NONBLOCK|unix.O_CLOEXEC, 0)
	if err != nil {
		return nil, Code("credentials_rejected")
	}
	source := os.NewFile(uintptr(descriptor), "canonical-profile")
	defer source.Close()
	var before, after, named unix.Stat_t
	if unix.Fstat(descriptor, &before) != nil || !canonicalRegular(before, boundary) || !canonicalExtendedMetadata(descriptor, false) {
		return nil, Code("credentials_rejected")
	}
	raw, err := io.ReadAll(io.LimitReader(source, (48<<10)+1))
	if err != nil || len(raw) != int(before.Size) || unix.Fstat(descriptor, &after) != nil || !sameCanonicalFile(before, after) ||
		unix.Fstatat(parent, filepath.Base(path), &named, unix.AT_SYMLINK_NOFOLLOW) != nil || !sameCanonicalFile(before, named) {
		clear(raw)
		return nil, Code("credentials_rejected")
	}
	checked, current, err := canonicalParent(path)
	if err != nil {
		clear(raw)
		return nil, Code("credentials_rejected")
	}
	unix.Close(checked)
	if boundary.Dev != current.Dev || boundary.Ino != current.Ino || boundary.Uid != current.Uid ||
		boundary.Gid != current.Gid || boundary.Mode != current.Mode {
		clear(raw)
		return nil, Code("credentials_rejected")
	}
	return raw, nil
}
