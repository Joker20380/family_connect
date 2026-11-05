//go:build android && !fc_local_core

package main

import "github.com/Joker20380/family_connect/carrier/wholedevice"

var openProvisionedSession = wholedevice.OpenProvisioned
