FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive

# Raíz coherente con Compose
WORKDIR /workspace
RUN mkdir -p /workspace/motor_sentinel

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl ca-certificates coreutils git openssh-client \
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

# Zona horaria
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Scripts de desarrollo del servicio
COPY dev/ /workspace/motor_sentinel/dev/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /workspace/motor_sentinel/dev/bootstrap.sh || true

ENV SHELL=/bin/bash
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash", "-l", "-c", "tail -f /dev/null"]
