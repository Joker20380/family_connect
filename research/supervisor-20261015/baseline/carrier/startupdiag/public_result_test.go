package startupdiag

import (
	"context"
	"crypto/sha256"
	"fmt"
	"testing"
)

func TestFriendsStartupResultRetainsSeedCause(t *testing.T) {
	ctx := Start(context.Background(), 17)
	Failure(ctx, "SEED_ADMISSION", context.DeadlineExceeded)
	Complete(ctx, context.DeadlineExceeded)
	Cancel(ctx)
	result := Snapshot(ctx)
	if result == nil || result.Attempt != 17 || result.Stage != "SEED_ADMISSION" || result.Cause != "DEADLINE" || !result.Complete {
		t.Fatalf("friends startup result missing or replaced: %+v", result)
	}
}

func TestDirectoryFingerprintIsFirstAndDoesNotExportDirectory(t *testing.T) {
	ctx := Start(context.Background(), 18)
	Directory(ctx, []byte("private-directory"))
	Directory(ctx, []byte("replacement"))
	Complete(ctx, nil)
	Directory(ctx, []byte("cleanup"))
	if Snapshot(ctx).DirectoryFingerprint != fmt.Sprintf("%x", sha256.Sum256([]byte("private-directory"))) {
		t.Fatal("directory identity overwritten")
	}
}
