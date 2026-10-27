FROM python:3.13-slim-trixie@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/control_plane
WORKDIR /app
COPY control_plane/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock
COPY control/friends/*.py /app/control/friends/
COPY device_identity/*.py /app/device_identity/
COPY control_plane/manage.py control_plane/pyproject.toml /app/control_plane/
COPY control_plane/fc_control_plane /app/control_plane/fc_control_plane
COPY control_plane/apps /app/control_plane/apps
COPY control_plane/templates /app/control_plane/templates
COPY control_plane/static /app/control_plane/static
COPY control_plane/tests /app/control_plane/tests
RUN useradd --uid 10001 --create-home console && mkdir -p /app/control_plane/.local && chown console:console /app/control_plane/.local
USER console
WORKDIR /app/control_plane
EXPOSE 8000
CMD ["gunicorn", "fc_control_plane.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
