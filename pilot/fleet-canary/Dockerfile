FROM family-connect-amneziawg:3.1-desktop AS awg
FROM family-connect-xray:26.3.27-pilot1 AS tcp
FROM fc-fleet-bootstrap-2-operator:local
USER root
COPY --from=awg /opt/awg31/awg /native/awg
COPY --from=awg /opt/awg31/amneziawg-go /native/amneziawg-go
COPY --from=tcp /usr/local/bin/xray /native/xray
COPY fleet_canary.py /canary.py
RUN python3 -c "import hashlib,sys;sys.path.insert(0,'/');from canary import NATIVE;from pathlib import Path;assert all(hashlib.sha256(Path('/native',name).read_bytes()).hexdigest()==digest for name,digest in NATIVE.items())"
ENTRYPOINT ["sleep", "600"]
