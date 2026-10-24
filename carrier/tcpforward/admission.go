package tcpforward

import (
	"context"
	"time"
)

type admissionWaiter struct{ lease bool }

func leaseRequest(request OpenRequest) bool {
	return canonicalHost(request.Host) == LeaseRenewalHost && request.Port == 1
}

func (mux *Mux) jobSlots(lease bool) chan struct{} {
	if lease {
		return mux.leaseJobs
	}
	return mux.jobs
}

func (mux *Mux) slotAvailableLocked(lease bool) bool {
	count := 0
	for _, stream := range mux.streams {
		if stream.lease == lease {
			count++
		}
	}
	if lease {
		return count < 1
	}
	return count < mux.config.MaxStreams
}

func (mux *Mux) rejectAdmissionLocked(lease bool) {
	if lease {
		mux.stats.LeaseRejected++
	} else {
		mux.stats.AdmissionRejected++
	}
}

func (mux *Mux) admitLocked(ctx context.Context, lease bool, deadline <-chan time.Time) error {
	pending := 0
	for _, waiter := range mux.admission {
		if waiter.lease == lease {
			pending++
		}
	}
	if mux.slotAvailableLocked(lease) && pending == 0 {
		return nil
	}
	closingLease := false
	for _, stream := range mux.streams {
		if stream.lease && stream.terminal != nil {
			closingLease = true
		}
	}
	if lease && (pending != 0 || !closingLease) || !lease && (!mux.config.WaitForSlot || pending >= MuxMaxPendingOpens) {
		mux.rejectAdmissionLocked(lease)
		return ErrStreamLimit
	}
	waiter := &admissionWaiter{lease: lease}
	mux.admission = append(mux.admission, waiter)
	mux.stats.AdmissionWaits++
	defer func() {
		for index, current := range mux.admission {
			if current == waiter {
				copy(mux.admission[index:], mux.admission[index+1:])
				mux.admission[len(mux.admission)-1] = nil
				mux.admission = mux.admission[:len(mux.admission)-1]
				break
			}
		}
		mux.signalLocked()
	}()
	for {
		if ctx.Err() != nil || mux.ctx.Err() != nil {
			mux.stats.AdmissionCancelled++
			return ErrReset
		}
		select {
		case <-deadline:
			mux.stats.AdmissionTimeouts++
			return ErrReset
		default:
		}
		first := false
		for _, current := range mux.admission {
			if current.lease == lease {
				first = current == waiter
				break
			}
		}
		if first && mux.slotAvailableLocked(lease) {
			return nil
		}
		changed := mux.changed
		mux.mu.Unlock()
		select {
		case <-changed:
		case <-ctx.Done():
		case <-mux.ctx.Done():
		case <-deadline:
			mux.mu.Lock()
			mux.stats.AdmissionTimeouts++
			return ErrReset
		}
		mux.mu.Lock()
	}
}
