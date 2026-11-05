FROM family-connect-renewal-tests:20261030
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client openssh-server \
    && rm -rf /var/lib/apt/lists/*
RUN test -e /usr/bin/python3 || ln -s /usr/local/bin/python3 /usr/bin/python3
