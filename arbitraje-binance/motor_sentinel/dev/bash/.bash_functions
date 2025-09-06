# /app/dev/bash/.bash_functions

### 🗂️ Navegación rápida
cdf() { cd "$@" && ls -alF; }   # cd + ls directo
back() { cd -; }                # volver al directorio anterior
mkcd() { mkdir -p "$1" && cd "$1"; }  # crear carpeta y entrar

### 🌱 Git helpers
gclean() {
  # Limpia ramas locales ya mergeadas con main/master
  git fetch -p
  git branch --merged | egrep -v "(^\*|main|master)" | xargs -r git branch -d
}
gundo() {
  # Revierte el último commit pero deja los cambios en staging
  git reset --soft HEAD~1
}
glog() {
  # Log bonito con gráficas
  git log --oneline --graph --decorate -20
}

### ⚙️ Go helpers
gtest() {
  # Corre tests verbosos y guarda log
  go test ./... -count=1 -v | tee /tmp/go_test.log
}
gbench() {
  # Corre benchmarks
  go test -bench=. ./... | tee /tmp/go_bench.log
}
gsize() {
  # Muestra el tamaño del caché de módulos
  du -sh $(go env GOMODCACHE) 2>/dev/null
}

### 🔄 Ecosistema
rcreload() {
  source /app/dev/bash/.bashrc_custom
  echo "🔄 Config recargada!"
}
bashinfo() {
  echo "Shell : $SHELL"
  echo "User  : $(whoami)"
  echo "Host  : $(hostname)"
  echo "CWD   : $(pwd)"
}
