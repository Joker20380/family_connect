# Supply the tested control image explicitly; this image contains no private state.
ARG CONTROL_IMAGE=family-connect-source49-tests:latest
FROM ${CONTROL_IMAGE}
COPY messenger/requirements.lock /tmp/messenger-restore.lock
RUN python -m pip install --no-deps --require-hashes -r /tmp/messenger-restore.lock
ENV PYTHONDONTWRITEBYTECODE=1
