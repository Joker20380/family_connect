FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends wireguard-tools iproute2 nftables curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY pilot/gateway.sh /usr/local/bin/family-connect-wg
ENTRYPOINT ["/usr/local/bin/family-connect-wg"]
