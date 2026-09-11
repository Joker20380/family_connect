FROM golang:1.26.1-bookworm AS build
ARG XRAY_REV=d2758a023cd7f4174a5a5fa4ff66e487d4342ba0
RUN git clone https://github.com/XTLS/Xray-core /src && cd /src && \
    git checkout "$XRAY_REV" && test "$(git rev-parse HEAD)" = "$XRAY_REV"
WORKDIR /src
RUN CGO_ENABLED=0 go build -trimpath -o /out/xray ./main
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates iproute2 curl python3 && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/xray /usr/local/bin/xray
COPY --from=build /src/LICENSE /usr/share/doc/xray/LICENSE
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/xray", "run", "-config", "/keys/server.json"]
