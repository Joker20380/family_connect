FROM ubuntu:24.04 AS system
ENV container=docker
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-venv systemd systemd-sysv systemd-resolved dbus polkitd pkexec iproute2 nftables curl procps ca-certificates && rm -rf /var/lib/apt/lists/*
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]

FROM system AS builder
COPY control/requirements.lock /locks/control.lock
COPY device_identity/requirements.lock /locks/identity.lock
COPY provisioning/requirements.lock /locks/provisioning.lock
COPY messenger/requirements.lock /locks/messenger.lock
RUN python3 -m venv /opt/build-venv && /opt/build-venv/bin/pip install --no-cache-dir -r /locks/control.lock -r /locks/identity.lock -r /locks/provisioning.lock && /opt/build-venv/bin/pip install --no-cache-dir --no-deps --require-hashes -r /locks/messenger.lock
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace
CMD ["/bin/bash"]

FROM builder AS desktop_tests
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-secret-1 xvfb xauth dbus-x11 && rm -rf /var/lib/apt/lists/* && python3 -m venv --system-site-packages /opt/build-venv
