# Local acceptance and frozen artifact

Read manifest and verify SHA256SUMS first. The source commit descends directly from
c9d75db6020f9f605e891036cbb9b68cebede708 in an isolated repository. Main dirty checkout
is not build input. Pinned Go1.26.1, local module cache, GOPROXY=off/GOSUMDB=off.

Research build: CGO_ENABLED=0 go build -trimpath -buildvcs=true -tags=seedacceptance
-o <output> ./cmd/bootstrap-broker, working directory source/carrier. Public/default
build omits the tag. No sameroomfixture tag may appear in candidate build inputs.
Build twice from a clean identical commit; compare exact hashes. No push/tag/release.

`validate.py prepare` makes the explicitly NEVER_DEPLOY local-provider overlay from
the previously accepted supervisor fixture. It changes only provider metadata routing,
test transport trust/dial hooks and test SFU instrumentation; production trigger and
supervisor source remain exact. `validate.py batch final` records targeted/race×3 and
three-way full-suite results. Fixture keys are disposable under /tmp and removed after
the run. No production keys or provider credentials are needed. Use a fresh log prefix
for another run; do not overwrite sealed receipts. Local sockets may require sandbox
approval. API regression uses the separate unchanged pinned deployed API reference,
not the obsolete Python checkout within gateway history.

Root acceptance is an explicitly approved local polkit invocation of the compiled
fixture tests TestAcceptanceRootPolicyEntry and TestAcceptanceRealPionContinuity.
It uses /run/fc-seed-acceptance-* temporary root-owned files, real kernel UID0 checks,
local Pion, and removes those files. This is NOT a privileged production operation.
Unprivileged tests verify rejection even when the service UID owns the0600 socket.

One root command is the test fault; the second close in the local fixture comes from
the local provider to exercise a later generation, not a second control consumption.
The permission-failure variant makes receipt storage unwritable, exercises failed
automatic socket unlink, then restores permissions and explicitly removes test state.
It proves protocol recovery/continuity despite missing audit evidence; a future live
run with missing receipts must remain PARTIAL, never repeat the trigger for cosmetics.

Root/normal tests compile test binaries; the frozen production-form executable is
not rebuilt with fixture hooks. Exact frozen-binary real-provider canary remains a
separate operational gate. Its runtime identity must match manifest exactly.
