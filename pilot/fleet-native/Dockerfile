# Local acceptance image only. Never deploy as a production gateway.
FROM family-connect-amneziawg:3.1-desktop AS awg31
FROM family-connect-amneziawg:2-pilot1 AS awg2
FROM family-connect-source49-tests:latest
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server openssh-client wireguard-tools iproute2 iputils-ping \
    && rm -rf /var/lib/apt/lists/*
COPY --from=awg31 /opt/awg31/awg /opt/awg31/awg
COPY --from=awg31 /opt/awg31/amneziawg-go /opt/awg31/amneziawg-go
COPY --from=awg2 /usr/local/bin/awg /opt/awg2/awg
COPY --from=awg2 /usr/local/bin/amneziawg-go /opt/awg2/amneziawg-go
COPY control /app/control
COPY provisioning /app/provisioning
COPY scripts/fleet_agent.py /app/scripts/fleet_agent.py
COPY pilot/fleet-native/accept.py /app/pilot/fleet-native/accept.py
RUN mkdir -p /run/sshd /etc/family-connect /var/lib/family-connect && \
    chmod 700 /var/lib/family-connect && passwd -d root
ENTRYPOINT ["sleep", "600"]
