ARG BASE=ubuntu:24.04
FROM ${BASE}
ENV container=docker
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 systemd systemd-sysv systemd-resolved dbus dbus-user-session dbus-x11 polkitd pkexec iproute2 nftables curl procps ca-certificates python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-secret-1 gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-pulseaudio libcodec2-1.2 librsvg2-common network-manager libqrencode4 libzbar0 xvfb xauth gnome-keyring desktop-file-utils xdg-utils squashfs-tools git && rm -rf /var/lib/apt/lists/*
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
