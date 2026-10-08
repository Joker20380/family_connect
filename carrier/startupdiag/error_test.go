package startupdiag

import (
	"context"
	"errors"
	"testing"
)

func TestPreservedErrorHasLegacyCategoryAndOriginalIdentity(test *testing.T) {
	legacy := errors.New("public category")
	actual := Preserve(legacy, context.DeadlineExceeded)
	if !errors.Is(actual, context.DeadlineExceeded) || !errors.Is(actual, legacy) || Legacy(actual) != legacy || actual.Error() != legacy.Error() {
		test.Fatal("lost compatibility or cause")
	}
}
