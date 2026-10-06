//go:build !fc_owner_diagnostic

package sessiontrace

import (
	"context"
	"time"
)

type correlationControl struct{}

func CorrelationEnabled() bool                       { return false }
func (recorder *Recorder) CorrelationMedia(Boundary) {}

func (recorder *Recorder) CorrelationCommand(string, string) string { return `{"error":"disabled"}` }

func (recorder *Recorder) correlationBoundary(Boundary, time.Time) {}
func (recorder *Recorder) correlationEvent(Event)                  {}
func StartDiagnosticControl(context.Context, *Recorder, string)    {}
