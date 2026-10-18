# ADR002 — Provider-independent MESH product name

Date: 2026-10-18. Status: ACCEPTED naming decision; integration PARTIAL.

## Context / Контекст

Telemost in the Android selector conflates Family Connect's transport with its
current media provider. Transport behavior and signed legacy identifiers already
exist, and installs must retain identity, provisioning and preferences. Product
desktop clients currently lack the media-runtime integration.

## Decision / Решение

Use **MESH (Media Encapsulated Secure Hop)**, untranslated in all locales, for
the user-facing secure media transport. VP8/RTP is today's carrier; Telemost is
today's provider. Keep provider names in accurate technical diagnostics and
dependency attribution. No wire/crypto, framing, timer, Auto or gateway change.

Use the compatibility chain `MESH (UI) → telemost (selection) → restricted
(runtime) → telemost-webrtc (signed directory)`. Do not introduce the target ID
`mesh` or a version `mesh/1` without a separate compatibility need and migration.
Optional schema1 diagnostic metadata describes this relationship without
replacing or removing existing fields. No signed structure is modified.

## Consequences / Следствия

The label can survive future carrier/provider changes. It does not claim a
decentralized or multi-hop mesh. Desktop selectors must not advertise a missing
runtime. Separate desktop integration must preserve the existing engines,
identity stores, provisioning and platform permission boundaries and pass native
platform checks before those clients can offer MESH.

MESH 2 is PLANNED provider/route research. MESH 3 is RESEARCH/FUTURE distributed
networking, potentially with Reticulum. Neither is a promise of this release.

Implementation details remain in the [transport contract](../../carrier/README.md#mesh-product-contract)
and [architecture map](../architecture.md#mesh-product-model); operational truth
remains in STATUS and dated reports, not this naming decision.
