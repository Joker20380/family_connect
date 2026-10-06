//go:build fc_owner_diagnostic

package sessiontrace

func (point *Boundary) RecordPicture(known bool, picture uint16) {
	point.PictureKnown, point.PictureID = known, picture
}

func (recorder *Recorder) RecordConsumed(sequence, base uint64, mask uint32) {
	recorder.Boundary(Boundary{Direction: "rx", Stage: "reliable_consumed", Result: "ok", DataKnown: true, DataSequence: sequence, ACKBase: base, ACKMask: mask})
}

func (recorder *Recorder) RecordBaseAdvanced(base uint64, mask uint32) {
	recorder.Boundary(Boundary{Direction: "rx", Stage: "base_advanced", Result: "ok", ACKBase: base, ACKMask: mask})
}

func (recorder *Recorder) watchAttempt(point Boundary) (Boundary, bool) {
	if candidate := recorder.watch.identity; candidate.MessageKnown && candidate.Direction == "tx" &&
		candidate.Sender == point.Sender && candidate.Message == point.Message && candidate.AttemptKnown {
		point.DataKnown, point.DataSequence = candidate.DataKnown, candidate.DataSequence
		point.AttemptKnown, point.Attempt = true, candidate.Attempt
		return point, true
	}
	return point, false
}

func (recorder *Recorder) decorateWatchEvent(event *Event) {
	if watch := recorder.watchSnapshot(); watch != nil {
		if event.Delivery == nil {
			event.Delivery = &Delivery{}
		}
		event.Delivery.Watch = watch
	}
}

func (recorder *Recorder) decorateWatchSnapshot(value *Snapshot) {
	value.Watch = recorder.watchSnapshot()
}

func cloneWatchDelivery(destination, source *Delivery) {
	destination.Watch = cloneWatch(source.Watch)
}
