#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
source_root=$PWD
work="${RUNNER_TEMP:?}/fc-linux-candidate"
mkdir -p "$work/accepted" "$work/normal"
git archive HEAD | tar -xf - -C "$work/accepted"
git init "$work/xray"
git -C "$work/xray" remote add origin https://github.com/XTLS/Xray-core.git
git -C "$work/xray" fetch --depth=1 origin d2758a023cd7f4174a5a5fa4ff66e487d4342ba0
(
  cd "$work/accepted"
  python -m scripts.build_desktop_mesh --go "$(command -v go)" --xray "$work/xray" --out "$work/native" --os linux --test
  tar -c tests/fixtures/linux_system_runtime/Dockerfile control/requirements.lock \
    device_identity/requirements.lock provisioning/requirements.lock messenger/requirements.lock | \
    docker build --target builder -t fc-l032-builder:ci -f tests/fixtures/linux_system_runtime/Dockerfile -
  docker build -f pilot/awg31/Dockerfile -t fc-l032-awg:ci .
  docker build -f pilot/tcp/Dockerfile -t fc-l032-tcp:ci .
)
awg_container=$(docker create fc-l032-awg:ci)
tcp_container=$(docker create fc-l032-tcp:ci)
docker cp "$awg_container:/opt/awg31" "$work/normal/awg"
docker cp "$tcp_container:/usr/local/bin/xray" "$work/normal/xray"
docker rm "$awg_container" "$tcp_container"
docker run --rm --network none --read-only --tmpfs /tmp:exec \
  --mount "type=bind,src=$work/accepted,dst=/workspace,readonly" \
  --mount "type=bind,src=$work,dst=/evidence" fc-l032-builder:ci /bin/bash -c '
    /opt/build-venv/bin/python -m scripts.build_desktop_rns --out /evidence/rns
    /opt/build-venv/bin/python -m scripts.package_mesh_component --native /evidence/native --rns /evidence/rns \
      --awg /evidence/normal/awg --tcp /evidence/normal/xray --out /evidence/system'
docker build -f tests/fixtures/linux_candidate/Dockerfile -t fc-l032-system:ci tests/fixtures/linux_candidate
mkdir -p artifacts/linux-candidate
system_archive="$work/system/FamilyConnect-MESH-system-amd64.tar.gz"
run_container() (
  local name=$1 fixture=$2
  shift 2
  docker run -d --name "$name" --network none --cgroupns private --privileged \
    --tmpfs /run --tmpfs /run/lock --tmpfs /tmp:exec \
    --mount "type=bind,src=$source_root/artifacts/linux-candidate,dst=/artifacts,readonly" \
    --mount "type=bind,src=$system_archive,dst=/evidence/system.tar.gz,readonly" \
    --mount "type=bind,src=$source_root/$fixture,dst=/evidence/smoke.py,readonly" \
    --mount "type=bind,src=$source_root/tests/fixtures/linux_candidate/prestart.py,dst=/fixture/prestart.py,readonly" \
    --mount "type=bind,src=$source_root/tests/fixtures/desktop-friends-catalog-v2.json,dst=/fixture/catalog.json,readonly" \
    fc-l032-system:ci /sbin/init
  trap 'docker stop --timeout 30 "$name"; docker rm "$name"' EXIT
  for attempt in $(seq 1 60); do
    if docker exec "$name" systemctl is-active dbus systemd-resolved >/dev/null 2>&1; then break; fi
    sleep 1
  done
  docker exec -e FC_L031_HOST_NETNS="$(stat -Lc %i /proc/self/ns/net)" \
    -e FC_L032_HOST_NETNS="$(stat -Lc %i /proc/self/ns/net)" "$name" \
    /usr/bin/python3 -I -S /evidence/smoke.py "$@"
)
run_container fc-l032-system-smoke tests/fixtures/linux_system_runtime/smoke.py /evidence/system.tar.gz | tee artifacts/linux-candidate/system-smoke.log
curl -fsSL https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage -o "$work/appimagetool"
chmod 755 "$work/appimagetool"
sha256sum "$work/appimagetool"
APPIMAGE_EXTRACT_AND_RUN=1 python -m scripts.package_linux --system-bundle "$system_archive" \
  --standard-system-rebuild --internal-version '0.2.12~l03.2.5' --output artifacts/linux-candidate --appimagetool "$work/appimagetool"
python -B -m scripts.verify_linux_candidate artifacts/linux-candidate | tee artifacts/linux-candidate/integrity.log
run_container fc-l032-deb tests/fixtures/linux_candidate/smoke.py deb '/artifacts/FamilyConnect_0.2.12~l03.2.5_amd64.deb' | tee artifacts/linux-candidate/deb-smoke.log
run_container fc-l032-appimage tests/fixtures/linux_candidate/smoke.py appimage '/artifacts/FamilyConnect-0.2.12~l03.2.5-x86_64.AppImage' | tee artifacts/linux-candidate/appimage-smoke.log
for transport in awg tcp; do
  run_container "fc-r1-$transport" tests/fixtures/linux_candidate/smoke.py "prestart-$transport" '/artifacts/FamilyConnect_0.2.12~l03.2.5_amd64.deb' | tee "artifacts/linux-candidate/prestart-$transport.log"
done
