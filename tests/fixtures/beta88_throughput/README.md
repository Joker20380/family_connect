# Beta88 gateway read-alignment experiment — NOT ACCEPTED FOR DELIVERY

The patch applies to the retained observation-only accepted gateway source,
inventory `bc3721ec8c30c6fb304c478b22398926fe3bfc0c576216c49ed53809d78c3051`,
not to the old repository main. It contains one server target-read alignment
change and its deterministic segmentation regression. No wire/credit/window/RTO
changes. Android beta88 is unchanged.

Physical evidence and decision:
`docs/releases/2026-10-19-beta88-throughput-ipv6-1.md` and adjacent evidence JSON.
The 16,384-byte socket read was split into16,340+44TCP bytes by the existing batch
limit. The fixture reproduces seven44-byte tails in130,720bytes; aligned reads
eliminate them without changing byte content or the nonbatch path.

Run `go test -race -tags=fc_perf_diagnostic ./tcpforward -run TestGatewayReadAlignment`
in the exact patched retained source using recorded Go1.26.1/toolchain settings.
The broader affected dependency race suite passed300test records/11opt-in skips;
the synthetic no-loss throughput result was negative. Physical gain was not
repeatable beyond media-path variability. Production was restored to the original
accepted binary. Do not treat this patch as an approved production optimization.
