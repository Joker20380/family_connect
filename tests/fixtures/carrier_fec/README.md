# Carrier S / SF laboratory only — 2026-10-21

Parent: sealed `p-stack-interaction-20261021` source inventory, binary
`c97d4192f3c54396677da09896cd16784c60445ebd9ada633713787eb595148a`.
Do not substitute the older committed carrier tree. No product source/default,
APK, deployment, identity, routing, public release or Git push is authorized here.

L keeps the 24-byte legacy header and 8192-byte parts. S introduces **incompatible
lab-only FCF2 v1**, a 64-byte header and 1024-byte independently assembled parts.
SF uses the identical S format plus shortened systematic Reed–Solomon groups,
up to 8 source + 2 repair, within one already available carrier message. Messages
of 0..1024 bytes do not generate repair. Each final short source is zero-padded
for coding only; its wire length stays exact, repair is 1024 bytes. Repair is
sent through the same VP8 path, not a new RTP payload type. This is one fixed
profile, not an optimum. No fragment ARQ or retry message-ID reuse.

Header: magic[0:4], version[4], profile[5], direction[6], reserved[7], epoch[8:24],
sender[24:28], message[28:32], original length[32:36], original CRC32[36:40],
group[40:42], symbol index[42], actual source count[43], symbol size[44:46],
wire symbol length[46:48], header+symbol CRC32[48:52], reserved zeros[52:64].
Big-endian integers. The CRC covers bytes[0:48]+[52:end]. Header fields are
validated against locally fixed bounds before allocations/decode. CRC is not
authentication; unchanged Family TLS remains the end-to-end trust boundary.

At most 16 unfinished messages, 80 symbols/message, 1,310,720 retained symbol
bytes, 4096 recent/pending IDs and 10-second lifetime. Receive metadata is bounded
independently of payload; no legacy uint32 bitmap is used for S/SF completion.
An identical duplicate is ignored without destroying a build; conflicting
metadata/content poisons that message. This intentionally differs from legacy
duplicate handling and is tested separately, not represented as size-only wire
compatibility. Missing/invalid symbols are erasures; whole-message CRC gates
delivery after reconstruction. Completed source groups never wait for repair.

All compared main variants: Q0, RS32/32, Mux128, packing OFF, original media A,
phase0, 33ms nominal timestamp increment, original 2ms pause **per frame**.
A common conservative outgoing RTP/RTCP ceiling of 1,048,576 B/s includes repair
and retransmissions; it is not the rejected FIXED4M controller. R0 is the explicit
short original-L bridge without this additional ceiling, not a main competitor.
The inherited 64-byte per-datagram allowance covers IPv6/UDP+16-byte SRTP; SRTCP
can need another 4 bytes, accounted separately in final conservative bounds.

Reproduction requires the pinned parent capsule and Go/module cache:
`lab.py`; pinned `go get github.com/klauspost/reedsolomon@v1.12.4`; `overlay.py`;
`finish_prepare.py`; `operator_finish.py`. `go mod tidy` may need the pinned
test-only Pion transport/v3 dependency. All edits target the ignored new copy.
`finish_prepare.py --build-only` resumes after a recorded dependency-only failure,
not after a source/admission failure. Original failed logs are retained.

`run_series.py smoke|reliable|product` is a finite, explicit plan, not a tuning
loop. It needs external-execution approval. Stop on failure; inspect existing
receipts before any further operation. P uses the inherited 17-body/hash and
both-end stream/ACK/ciphertext barrier; terminal-reset empty depth is never
success. Carrier pending/tail counters are additionally reported. The raw C smoke
may lose messages and is not claimed complete merely because the tool exits zero.

Local tests include actual pinned Pion packetization/RS, bounds, duplicate,
corruption, silence/expiry, cancellation/close/race, and three seeded packet-loss
models. The model is not a reconstruction of SFU loss. Preserve raw loss and
recovery counts separately; an incomplete trace means unknown, not zero loss.
Read `docs/releases/2026-10-20-mesh-capacity.md` for results and limitations.
