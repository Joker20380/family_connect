//go:build !fc_owner_diagnostic

package sessiontrace

import "time"

type watchControl struct{}

func (point *Boundary) RecordPicture(known bool, picture uint16)             {}
func (recorder *Recorder) RecordConsumed(sequence, base uint64, mask uint32) {}
func (recorder *Recorder) RecordBaseAdvanced(base uint64, mask uint32)       {}
func (recorder *Recorder) EnableEvidenceWatch(target WatchTarget) bool       { return false }
func (recorder *Recorder) watchBoundary(point Boundary, now time.Time)       {}
func (recorder *Recorder) watchEvent(event Event)                            {}
func (recorder *Recorder) watchAttempt(point Boundary) (Boundary, bool)      { return point, false }
func (recorder *Recorder) decorateWatchEvent(event *Event)                   {}
func (recorder *Recorder) decorateWatchSnapshot(value *Snapshot)             {}
func cloneWatchDelivery(destination, source *Delivery)                       {}
