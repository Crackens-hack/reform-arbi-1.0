¡Listo, Dominus! Acá tenés el **README.md** completo, listo para pegar en tu repo. Cubre **qué hace**, **qué depende del sistema**, **cómo usarlo con Dockerfile/Compose**, estructura, pruebas y troubleshooting.

---

# Bash Portable Dev Env 🐳

Entorno Bash **portable** para contenedores (y hosts) con:

* Prompt 2 líneas con **rama Git en verde** + señales: ✚ (staged), ✱ (unstaged), ✭ (untracked), \$ (stash), ↑/↓/↕ (upstream).
* **Auto-refresh** del prompt en cada `Enter` (sin `rcrc`).
* **bash-completion** para Git, Docker, Compose, Make, Kubectl.
* Config modular y ordenada: `env → aliases → functions → prompt → completions`.

Funciona en Debian/Ubuntu y Alpine (con diferencias de paquetes, ver deps abajo).

---

## 📦 Requisitos (paquetes del sistema)

**Debian/Ubuntu (imagen `golang:1.23` o similar):**

```bash
apt-get update && apt-get install -y \
  bash bash-completion git ca-certificates && \
rm -rf /var/lib/apt/lists/*
```

**Alpine (si alguna vez lo usás):**

```bash
apk add --no-cache bash bash-completion git ca-certificates
# (Alpine NO trae git-prompt.sh; podés seguir con el fallback o bajarlo a mano)
```

> El prompt “pro” usa `git-prompt.sh` si está disponible:
>
> * Debian/Ubuntu: suele estar en `/usr/lib/git-core/git-sh-prompt` o `/usr/share/git/git-prompt.sh`.
> * Si no está, el fallback muestra rama/commit igual (sin símbolos extendidos).

---

## 📂 Estructura

```
app/dev/bash/
├─ .bash_env                   # variables de entorno, history, ls color
├─ .bash_aliases               # alias (docker, git, go, etc.)
├─ .bash_functions             # (opcional) funciones tuyas
├─ .bash_gitprompt             # flags para __git_ps1 (muestra ✚✱✭$↑↓)
├─ .bash_prompt                # prompt 2 líneas + color + fallback
├─ .bash_completion_extras     # carga completados si existen
└─ .bashrc_custom              # orquestador: env→aliases→func→prompt→completion
```

Puentes en root (generados por `entrypoint.sh`):

```
/root/.bash_profile  # SHELL=/bin/bash y source a ~/.bashrc
/root/.bashrc        # source a /app/dev/bash/.bashrc_custom
```

---

## 🐳 Dockerfile (Debian base recomendado)

```dockerfile
FROM golang:1.23

RUN apt-get update && apt-get install -y \
      bash bash-completion git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Baseline por si el volumen no se monta (luego lo sobreescribe tu volumen)
COPY ./app/dev/bash/ /app/dev/bash/

# Entrypoint que crea ~/.bashrc y ~/.bash_profile (puente → tu repo)
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV SHELL=/bin/bash

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash", "-l", "-c", "tail -f /dev/null"]
```

### `entrypoint.sh`

```bash
#!/bin/bash
set -e

cat > /root/.bash_profile <<'EOF'
export SHELL=/bin/bash
[[ -r ~/.bashrc ]] && . ~/.bashrc
EOF

cat > /root/.bashrc <<'EOF'
if [[ -r /app/dev/bash/.bashrc_custom ]]; then
  . /app/dev/bash/.bashrc_custom
else
  echo "[warn] /app/dev/bash/.bashrc_custom no encontrado (¿volumen no montado?)" >&2
fi
EOF

exec "$@"
```

---

## 🧩 docker-compose.yml

```yaml
version: "3.9"

services:
  go-app:
    build:
      context: .
    container_name: go_app
    working_dir: /app
    tty: true
    stdin_open: true
    command: bash -l -c "tail -f /dev/null"
    environment:
      - CONTAINER=true      # activa el bloque 🐳 en el prompt
      - NAME=go_app         # nombre mostrado en el prompt
      - SHELL=/bin/bash
      - GOMODCACHE=/go/pkg/mod
      - GOCACHE=/root/.cache/go-build
    volumes:
      - ./app:/app/
      - go_mod_cache:/go/pkg/mod
      - go_build_cache:/root/.cache/go-build

volumes:
  go_mod_cache:
  go_build_cache:
```

> **Nota**: El volumen `./app:/app` sobreescribe `/app/dev/bash` con tu repo local ⇒ siempre usás tu última config.

---

## ⚙️ Archivos claves (resumen)

### `.bash_env`

* History grande sin duplicados.
* `EDITOR=vim`, `PAGER=less`, `LESS='-R'`.
* `ls` con color (detecta GNU coreutils vs BusyBox).

### `.bash_aliases`

* Aliases de uso diario + Go, Docker, Git.
* `rcrc` recarga tu stack (`.bashrc_custom`).

### `.bash_gitprompt`

Activa señales de `__git_ps1`:

```bash
export GIT_PS1_SHOWDIRTYSTATE=1
export GIT_PS1_SHOWUNTRACKEDFILES=1
export GIT_PS1_SHOWSTASHSTATE=1
export GIT_PS1_SHOWUPSTREAM=auto
export GIT_PS1_DESCRIBE_STYLE=branch
```

### `.bash_prompt`

* Carga `.bash_gitprompt`.
* Busca `git-prompt.sh` en rutas conocidas o usa fallback.
* Prompt 2 líneas:

  ```
  🐳 (go_app) root@HOST:cwd (main ✚✭$)
  $
  ```
* **Auto-refresh** con `PROMPT_COMMAND` (hook puesto en `.bashrc_custom`).

### `.bash_completion_extras`

* Sourcea `bash-completion` del sistema.
* Carga completados de `git`, `docker`, `docker-compose`, `make`, `kubectl` **si existen**.

### `.bashrc_custom`

Orquesta todo en orden y engancha el auto-refresh:

```bash
if type _bash_ps1_refresh >/dev/null 2>&1; then
  PROMPT_COMMAND="_bash_ps1_refresh${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi
```

---

## 🚀 Uso

1. Levantar contenedor:

```bash
docker compose up -d --build
docker exec -it go_app bash -l
```

2. Probar el prompt Git:

```bash
cd /app && mkdir test-repo && cd test-repo
git init
echo "hola" > hola.txt
git add hola.txt              # ✚
echo "cambio" >> hola.txt     # ✱
echo "nuevo" > nuevo.txt      # ✭
git stash -u                  # $
# Enter → prompt se actualiza solo
```

3. Autocompletado:

* `git ch<TAB>` → `checkout`
* `docker exec -it <TAB>` → lista contenedores
* `make <TAB>` → targets

---

## 🧰 Troubleshooting

* **No veo símbolos ✚✱✭\$**
  Verificá que exista `git-prompt.sh` en la imagen (Debian/Ubuntu lo trae). Si no está, el fallback muestra rama/commit (sin señales).
  Confirmá que `.bash_gitprompt` se esté cargando (lo carga `.bash_prompt` al inicio).

* **Colores de `ls` raros en Alpine**
  BusyBox `ls` ya colorea; el bloque en `.bash_env` detecta coreutils vs BusyBox y actúa en consecuencia.

* **El prompt no cambia hasta que aprieto Enter**
  Es normal: el PS1 se “dibuja” al mostrar el prompt. Ya está el `PROMPT_COMMAND` para regenerarlo en cada Enter.

* **VS Code/exec usa sh**
  `entrypoint.sh` crea `~/.bash_profile` con `SHELL=/bin/bash` y puente a `~/.bashrc`. Además, Compose exporta `SHELL=/bin/bash`.

---

## 🧪 Notas útiles

* Ocultar la marca fuera de repos: ya viene configurado (no muestra `(-)`).
* Cambiar color de la rama: edita `BR_COLOR` en `.bash_prompt`.
* Refrescar manual: `rcrc` (igual no hace falta por el auto-refresh).
* Rama inicial `main` por defecto:

  ```bash
  git config --global init.defaultBranch main
  ```

---

Hecho. Tenés un setup **pro**, portable y documentado. Si querés, después sumo un par de funciones útiles en `.bash_functions` (p.ej. `gclean`, `cdf/cdb`, `back`) y un `Makefile` con targets de demo. ¿Le damos? 💪🧠
