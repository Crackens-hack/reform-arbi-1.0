FROM golang:1.22-bullseye AS build
WORKDIR /src
COPY . .
RUN go build -o /event_hub ./cmd/event_hub

FROM debian:bullseye-slim
RUN apt-get update && apt-get install -y bash curl wget && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /event_hub /usr/local/bin/event_hub
EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=3s --retries=10 CMD curl -fs http://127.0.0.1:8080/healthz || exit 1
ENTRYPOINT ["event_hub"]
