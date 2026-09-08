#!/bin/sh
set -eu
umask 077
mkdir -p state
if [ ! -f state/gateway.der ]; then
  openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
    -keyout state/gateway-key.pem -out state/gateway.pem -days 30 \
    -subj /CN=gateway.test -addext subjectAltName=DNS:gateway.test \
    -addext basicConstraints=critical,CA:FALSE
  openssl x509 -in state/gateway.pem -outform DER -out state/gateway.der
  openssl pkcs8 -topk8 -nocrypt -in state/gateway-key.pem -outform DER -out state/gateway-key.der
fi
if [ ! -f state/relay-token ]; then openssl rand -hex 32 > state/relay-token; fi
# Root-owned directory: allow unprivileged core to traverse and read only its lab credentials.
chmod 711 state
chown 65532:65532 state/gateway.der state/gateway-key.der state/relay-token
chmod 400 state/gateway.der state/gateway-key.der state/relay-token
# Other credentials remain root-only; never copy state into Git.
docker run --rm --network none --read-only --cap-drop ALL \
  -v "$PWD/state:/state:rw" family-connect-control:phase0 python scripts/init_state.py
