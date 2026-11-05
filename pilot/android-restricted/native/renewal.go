//go:build android

package main

import "C"

import (
	"crypto/sha256"
	"time"

	"github.com/Joker20380/family_connect/carrier/wholedevice"
)

//export fcRestrictedRenew
func fcRestrictedRenew(id int64, response, identity string) int32 {
	ownerMu.Lock()
	if current == nil || current.id != id {
		ownerMu.Unlock()
		return 0
	}
	owned := current
	owned.mu.Lock()
	session := owned.session
	eligible := owned.state == 2 && session != nil && owned.ctx.Err() == nil && len(owned.anchor) == 32
	anchor := append([]byte(nil), owned.anchor...)
	owned.mu.Unlock()
	ownerMu.Unlock()
	if !eligible {
		return 0
	}
	material := []byte(identity)
	defer clear(material)
	profile, _, err := wholedevice.DeliveryMaterial([]byte(response), material, anchor, time.Now())
	if err != nil {
		return 0
	}
	defer clear(profile)
	fingerprint := sha256.Sum256(profile)
	if !session.OfferCredentialsWithCommit(profile, func() {
		owned.mu.Lock()
		defer owned.mu.Unlock()
		if owned.ctx.Err() == nil && owned.session == session && owned.ownership.RefreshProfile(session, fingerprint) {
			owned.profileHash = fingerprint
		}
	}) {
		return 0
	}
	return 1
}
