FROM family-connect-amneziawg:3.1-desktop AS awg
FROM family-connect-xray:26.3.27-pilot1 AS tcp
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 iproute2 && rm -rf /var/lib/apt/lists/*
COPY --from=awg /opt/awg31/awg /native/awg
COPY --from=awg /opt/awg31/amneziawg-go /native/amneziawg-go
COPY --from=tcp /usr/local/bin/xray /native/xray
ENTRYPOINT ["python3", "/source/scripts/check_transport_readback.py"]
