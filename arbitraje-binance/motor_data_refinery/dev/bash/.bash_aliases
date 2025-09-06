# app/dev/bash/.bash_aliases
# Calidad de vida
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias c='clear'
alias cl='clear'
alias ..='cd ..'
alias ...='cd ../..'
alias rcrc='source /app/dev/bash/.bashrc_custom'
alias h='history'




# 🔊 Cambiar salida de audio rápido
alias auris='pactl set-default-sink alsa_output.pci-0000_00_1b.0.analog-stereo'
alias usb='pactl set-default-sink alsa_output.usb-C-Media_INC._USB_Sound_Device-00.iec958-stereo'

# ▶️ Test rápido de sonido
alias testaudio='paplay /usr/share/sounds/alsa/Front_Center.wav'

# Go
alias gob='go build ./...'
alias gor='go run .'
alias got='go test ./... -count=1 -v'
alias gom='go mod tidy && go mod download'

# Docker
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"'
alias dimg='docker images'
alias drmstopped='docker rm $(docker ps -aq) 2>/dev/null || true'
alias drmiunref='docker image prune -f'

# Git
alias gs='git status -sb'
alias ga='git add -A'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --decorate -20'

# Varios
