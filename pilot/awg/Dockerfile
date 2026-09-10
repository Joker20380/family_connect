FROM golang:1.25-bookworm AS build
ARG AWG_GO_REV=1cc94272ca8e9e223a5fe76382f5880f09d3c12d
ARG AWG_TOOLS_REV=61e741780e8465a67a7d7fb6cffe14a8a15d624a
RUN git clone https://github.com/amnezia-vpn/amneziawg-go /go/src/awg && \
    cd /go/src/awg && git checkout "$AWG_GO_REV" && test "$(git rev-parse HEAD)" = "$AWG_GO_REV"
WORKDIR /go/src/awg
# The upstream outline integration test requires an external fixture VPN.
# Exercise the engine and local networking tests here; live pilot acceptance is separate.
RUN go test . ./conn/... ./device/... ./ipc/... ./ratelimiter/... ./replay/... ./rwcancel/... ./tai64n/... ./tun/... && CGO_ENABLED=0 go build -trimpath -o /out/amneziawg-go .
RUN git clone https://github.com/amnezia-vpn/amneziawg-tools /tools && \
    cd /tools && git checkout "$AWG_TOOLS_REV" && test "$(git rev-parse HEAD)" = "$AWG_TOOLS_REV" && \
    make -C src -j2 && cp src/wg /out/awg && cp src/wg-quick/linux.bash /out/awg-quick && \
    cp COPYING /out/LICENSE-tools && cp /go/src/awg/LICENSE /out/LICENSE-go
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends iproute2 nftables curl ca-certificates openresolv python3 procps && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/ /usr/local/bin/
RUN chmod 755 /usr/local/bin/awg-quick
COPY pilot/awg/gateway.sh /usr/local/bin/family-connect-awg
RUN chmod 755 /usr/local/bin/family-connect-awg
ENV WG_QUICK_USERSPACE_IMPLEMENTATION=amneziawg-go WG_SUDO=1
ENTRYPOINT ["/usr/local/bin/family-connect-awg"]
