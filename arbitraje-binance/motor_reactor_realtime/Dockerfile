FROM golang:1.23
ENV DEBIAN_FRONTEND=noninteractive

# Raíz coherente con Compose
WORKDIR /workspace
RUN mkdir -p /workspace/motor_reactor_realtime

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash bash-completion git openssh-client ca-certificates curl coreutils \
  && rm -rf /var/lib/apt/lists/*

# === Codex CLI (tarball nativo MUSL) ===
ARG CODEX_VERSION
ARG CODEX_CLI_URL
ARG CODEX_SHA256
RUN set -eux; \
    curl -fsSL "${CODEX_CLI_URL}" -o /tmp/codex.tgz; \
    echo "${CODEX_SHA256}  /tmp/codex.tgz" | sha256sum -c -; \
    tar -xzf /tmp/codex.tgz -C /usr/local/bin; \
    if [ ! -f /usr/local/bin/codex ]; then mv /usr/local/bin/codex-* /usr/local/bin/codex; fi; \
    chmod +x /usr/local/bin/codex; \
    rm -f /tmp/codex.tgz; \
    /usr/local/bin/codex --version || true

# Caches de Go (coinciden con los volumes del compose)
ENV GOMODCACHE=/go/pkg/mod
ENV GOCACHE=/root/.cache/go-build

# Scripts de desarrollo del servicio
COPY dev/ /workspace/motor_reactor_realtime/dev/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /workspace/motor_reactor_realtime/dev/bootstrap.sh || true

ENV SHELL=/bin/bash
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash", "-l", "-c", "tail -f /dev/null"]
