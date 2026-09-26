FROM golang:1.26.1-bookworm AS build
ARG ENGINE_REV=b5928efb6ca19f0153958460c3d141f04abc5c2e
ARG TOOLS_REV=ee0f0a9aa34ff0a0da4b3433b9512781cfe02843
RUN git clone https://github.com/amnezia-vpn/amneziawg-go /engine && cd /engine && git checkout "$ENGINE_REV" && test "$(git rev-parse HEAD)" = "$ENGINE_REV"
WORKDIR /engine
ENV GOTOOLCHAIN=local
COPY pilot/awg31/patches/ /patches/
COPY pilot/awg31/regression_test.go /engine/device/fc_regression_test.go
RUN git apply --check /patches/0001-refresh-s4-after-tun-read.patch && git apply /patches/0001-refresh-s4-after-tun-read.patch
RUN gofmt -w device/fc_regression_test.go
RUN go test -count=3 ./conn/... ./device/... ./ipc/... ./ratelimiter/... ./replay/... ./rwcancel/... ./tai64n/... ./tun/...
RUN CGO_ENABLED=0 go build -trimpath -buildvcs=false -o /out/amneziawg-go .
COPY pilot/awg31/tools_regression.c /tools_regression.c
RUN git clone https://github.com/amnezia-vpn/amneziawg-tools /tools && cd /tools && git checkout "$TOOLS_REV" && test "$(git rev-parse HEAD)" = "$TOOLS_REV" && git apply --check /patches/0002-tools-u16-range.patch && git apply /patches/0002-tools-u16-range.patch && cc -Isrc /tools_regression.c src/type.c -o /tmp/tools-test && /tmp/tools-test && make -C src -j2 && cp src/wg /out/awg && cp src/wg-quick/linux.bash /out/awg-quick && cp COPYING /out/LICENSE-tools && cp /engine/LICENSE /out/LICENSE-go
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 iproute2 nftables curl ca-certificates openresolv procps && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/ /opt/awg31/

COPY pilot/awg31/manifest.py pilot/awg31/pins.json /build/
RUN chmod 755 /opt/awg31/awg-quick && python3 /build/manifest.py /opt/awg31 /build/pins.json
ENV PATH=/opt/awg31:$PATH WG_QUICK_USERSPACE_IMPLEMENTATION=/opt/awg31/amneziawg-go WG_SUDO=1
COPY pilot/awg/gateway.sh /usr/local/bin/family-connect-awg
RUN chmod 755 /usr/local/bin/family-connect-awg
ENTRYPOINT ["/usr/local/bin/family-connect-awg"]
