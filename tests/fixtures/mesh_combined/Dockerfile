FROM python:3.13-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends iproute2 nftables dbus systemd-resolved procps && rm -rf /var/lib/apt/lists/*
COPY control/requirements.lock /locks/control.lock
COPY device_identity/requirements.lock /locks/identity.lock
COPY provisioning/requirements.lock /locks/provisioning.lock
COPY messenger/requirements.lock /locks/messenger.lock
RUN pip install --no-cache-dir -r /locks/control.lock -r /locks/identity.lock -r /locks/provisioning.lock && pip install --no-cache-dir --no-deps --require-hashes -r /locks/messenger.lock
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace
ENTRYPOINT ["/bin/bash", "/workspace/tests/fixtures/mesh_combined/run.sh"]
