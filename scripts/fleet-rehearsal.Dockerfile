FROM ubuntu@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3
RUN apt-get update -qq && apt-get install -y -qq python3-venv nftables iproute2 systemd zstd openssl openssh-client curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /venv
COPY fleet/requirements.lock /requirements.lock
RUN /venv/bin/pip install --no-cache-dir -r /requirements.lock pytest==9.1.1
ENV PATH=/venv/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
