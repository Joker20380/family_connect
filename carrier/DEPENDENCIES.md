# Linked carrier dependencies — 2026-09-27

Inventory of `go list -deps ./cmd/telemost-binary`, Go 1.27.1, Linux/amd64.
Android/arm64 CGO inventory for5N.2 on27.09 matches the same23 external modules.
The standalone test APK retains these notices plus original NDK/LLVM notices
conservatively (not evidence that every component listed there is linked).
Pinned by go.mod/go.sum; no vendored or modified dependency implementation.
Google UUID is required transitively by Pion, not by our UUID helper.
All module-root LICENSE files and additional LICENSES/ notices are retained
verbatim in [licenses/dependencies.txt](licenses/dependencies.txt), including
Pion BSD-3-Clause/CC0 material. No assumption that every Pion file is MIT.

| Module | Version | Root license | SHA256 of original LICENSE |
| --- | --- | --- | --- |
| `github.com/google/uuid` | `v1.6.0` | BSD-3-Clause | `0a8d61ed3cbfd5312326e8126c31ce9c627a283adc99131b56896d29ada04b2d` |
| `github.com/gorilla/websocket` | `v1.5.3` | BSD-3-Clause | `2be1b548b0387ca8948e1bb9434e709126904d15f622cc2d0d8e7f186e4d122d` |
| `github.com/pion/datachannel` | `v1.6.0` | MIT | `87272dba8c4fcf57101a3195f4f53f7b010b6e153b9b0977bb1a3f91acddf691` |
| `github.com/pion/dtls/v3` | `v3.1.4` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/ice/v4` | `v4.2.7` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/interceptor` | `v0.1.45` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/logging` | `v0.2.4` | MIT | `87272dba8c4fcf57101a3195f4f53f7b010b6e153b9b0977bb1a3f91acddf691` |
| `github.com/pion/mdns/v2` | `v2.1.0` | MIT | `83e4dd21429a91fb7cea67a476032a9641425e5355df2e0f589a738b6ec9fd2c` |
| `github.com/pion/randutil` | `v0.1.0` | MIT | `badaf9bc72e71d5a70e7604c636b5b7adf79b9cafc188688438105d2b1e54722` |
| `github.com/pion/rtcp` | `v1.2.16` | MIT | `87272dba8c4fcf57101a3195f4f53f7b010b6e153b9b0977bb1a3f91acddf691` |
| `github.com/pion/rtp` | `v1.10.2` | MIT | `b85dcd3e453d05982552c52b5fc9e0bdd6d23c6f8e844b984a88af32570b0cc0` |
| `github.com/pion/sctp` | `v1.10.0` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/sdp/v3` | `v3.0.18` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/srtp/v3` | `v3.0.11` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/stun/v3` | `v3.1.5` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/transport/v4` | `v4.0.2` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/turn/v5` | `v5.0.9` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/pion/webrtc/v4` | `v4.2.15` | MIT | `6483daf6c8aa2c8192528e60be098aa82dd18f6d7b96dc8246f4f7c3333fbf3f` |
| `github.com/wlynxg/anet` | `v0.0.5` | BSD-3-Clause | `6b8970dbe36fe214fd02b438c06daee19897708e435d761ecd18adc9ef7e7a05` |
| `golang.org/x/crypto` | `v0.48.0` | BSD-3-Clause | `911f8f5782931320f5b8d1160a76365b83aea6447ee6c04fa6d5591467db9dad` |
| `golang.org/x/net` | `v0.50.0` | BSD-3-Clause | `911f8f5782931320f5b8d1160a76365b83aea6447ee6c04fa6d5591467db9dad` |
| `golang.org/x/sys` | `v0.41.0` | BSD-3-Clause | `911f8f5782931320f5b8d1160a76365b83aea6447ee6c04fa6d5591467db9dad` |
| `golang.org/x/time` | `v0.14.0` | BSD-3-Clause | `911f8f5782931320f5b8d1160a76365b83aea6447ee6c04fa6d5591467db9dad` |

Full module graph also includes upstream tests/tools (Ginkgo/Gomega, testify,
check/yaml, go-spew/go-difflib, agouti, kr/*, x/term/text, transport/v3).
They are not linked into this executable or imported by our tests. Their presence
in `go list -m all` is not binary inclusion; audit separately before adopting them.
This inventory does not clear unrelated historical product distributions.

Reference derivation: pinned olcrtc auth/telemost, engine/goolom signaling/media/
capabilities, transport/vp8channel/wire; pinned whitelist-bypass relay/telemost/api
and relay/tunnel/rtc/vp8tunnel. Original protocol maps and byte constants recovered
from DeepSeek overlap these references; conservatively retain both notices rather
than claim wholly independent origin. No whole reference project, KCP, headless
fork, LiveKit, VPN, TUN or proxy implementation is imported.
