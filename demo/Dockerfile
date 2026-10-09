# Runs the CURRENT source of shift-this-version so demo/make_gif.sh can record the real tool.
# Build context must be the repo root (make_gif.sh does this for you).
FROM ghcr.io/charmbracelet/vhs:latest

RUN apt-get update \
 && apt-get install -y --no-install-recommends git python3 python3-pip python3-venv \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE /src/
COPY shift_this_version /src/shift_this_version
RUN python3 -m venv /opt/stv && /opt/stv/bin/pip install --no-cache-dir /src

ENV PATH="/opt/stv/bin:${PATH}"
