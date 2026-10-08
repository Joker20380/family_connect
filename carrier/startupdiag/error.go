package startupdiag

import "errors"

type primaryError struct {
	legacy  error
	primary error
}

func Preserve(legacy, primary error) error {
	if primary == nil {
		return legacy
	}
	return &primaryError{legacy: legacy, primary: primary}
}

func (failure *primaryError) Error() string   { return failure.legacy.Error() }
func (failure *primaryError) Unwrap() []error { return []error{failure.legacy, failure.primary} }

func Legacy(failure error) error {
	var preserved *primaryError
	if errors.As(failure, &preserved) {
		return preserved.legacy
	}
	return failure
}
