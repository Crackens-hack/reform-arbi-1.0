# Makefile para manejar Docker Compose del stack-binance

DOCKER          = docker
DOCKER_COMPOSE  = docker compose

.PHONY: up down build rebuild restart logs sh attach ps psa start stop \
        net net-rm net-ls \
        images rmi-dangling rmi-all rmi-image down-rmi-all rm-orphans \
        vols vols-prune vols-nuke \
        nets nets-prune nets-nuke \
        prune clean nuke

## Construcción y ciclo de vida
build:
	$(DOCKER_COMPOSE) build

# rebuild sin cache
rebuild:
	$(DOCKER_COMPOSE) build --no-cache

run:
	$(DOCKER_COMPOSE) up -d

build-run:
	$(DOCKER_COMPOSE) up -d --build

down:
	$(DOCKER_COMPOSE) down

# baja, elimina imágenes creadas por compose y volúmenes de los servicios
down-rmi-all:
	$(DOCKER_COMPOSE) down --rmi all -v --remove-orphans

restart: down up

ps:
	$(DOCKER_COMPOSE) ps

psa:
	$(DOCKER) ps -a

start:
	$(DOCKER_COMPOSE) start

stop:
	$(DOCKER_COMPOSE) stop

logs:
	$(DOCKER_COMPOSE) logs -f --tail=100

sh:
	$(DOCKER_COMPOSE) exec motor_data_refinery bash

attach:
	$(DOCKER) attach motor_data_refinery

## Redes ---------------------------------------------------------

# crea red externa comms_net si no existe
net:
	@if ! $(DOCKER) network inspect comms_net >/dev/null 2>&1; then \
	  echo "🌐 Creando red externa comms_net..."; \
	  $(DOCKER) network create comms_net; \
	else \
	  echo "✅ La red comms_net ya existe"; \
	fi

# elimina solo la red comms_net si existe
net-rm:
	@if $(DOCKER) network inspect comms_net >/dev/null 2>&1; then \
	  echo "🗑️  Borrando red comms_net..."; \
	  $(DOCKER) network rm comms_net; \
	else \
	  echo "ℹ️  comms_net no existe"; \
	fi

net-ls:
	$(DOCKER) network ls

nets:
	$(DOCKER) network ls

nets-prune:
	$(DOCKER) network prune -f

# borra TODAS las redes user-defined (deja bridge/host/none)
nets-nuke:
	-$(DOCKER) network rm $$($(DOCKER) network ls -q | grep -vE '(^| )bridge$$|(^| )host$$|(^| )none$$') 2>/dev/null || true

## Imágenes ------------------------------------------------------

images:
	$(DOCKER) images

# borra solo dangling
rmi-dangling:
	$(DOCKER) image prune -f

# borra TODAS las imágenes (⚠️ agresivo)
rmi-all:
	-$(DOCKER) rmi -f $$($(DOCKER) images -aq) 2>/dev/null || true

# borra una imagen por nombre/patrón: make rmi-image IMAGE=nombre:o_patron
rmi-image:
	@test -n "$(IMAGE)" || (echo "Usa: make rmi-image IMAGE=repo[:tag]"; exit 1)
	-$(DOCKER) rmi -f $$($(DOCKER) images "$(IMAGE)" -q | sort -u) 2>/dev/null || true

## Volúmenes -----------------------------------------------------

vols:
	$(DOCKER) volume ls

vols-prune:
	$(DOCKER) volume prune -f

# borra TODOS los volúmenes (⚠️ datos se pierden)
vols-nuke:
	-$(DOCKER) volume rm $$($(DOCKER) volume ls -q) 2>/dev/null || true

## Limpieza genérica ---------------------------------------------

# limpia contenedores/imagenes/redes/volúmenes huérfanos
prune:
	$(DOCKER) system prune -af --volumes

# baja stack y hace prune total
clean: down prune

# 🔥 Nuke total: baja, borra imágenes, volúmenes y redes user-defined (incluida comms_net)
nuke:
	-$(DOCKER_COMPOSE) down -v --remove-orphans
	-$(MAKE) rmi-all
	-$(MAKE) vols-nuke
	-$(MAKE) nets-nuke
	-$(MAKE) net-rm
	$(DOCKER) system prune -af --volumes
