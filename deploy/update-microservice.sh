#!/bin/bash
# Atualiza o image-microservice na VPS (git pull + restart do systemd).
# Rodar DIRETO NA VPS, como root: ./update-microservice.sh [dev|prod|both]
#
# Substitui o antigo update-microservice-vps.ps1, que usava pm2 e um caminho
# que não existe mais. Hoje o deploy real é via systemd, com duas instâncias
# separadas:
#   - prod: /root/microservice/image-microservice-prod (porta 5002, service "image-microservice")
#   - dev:  /root/microservice/image-microservice-dev  (porta 5001, service "image-microservice-dev")

set -e

ALVO="${1:-prod}"

atualizar() {
  local pasta="$1"
  local servico="$2"
  local porta="$3"

  echo "=== Atualizando $servico ($pasta) ==="
  cd "$pasta"
  git pull
  systemctl restart "$servico"
  sleep 2
  systemctl status "$servico" --no-pager | head -5
  echo "--- health check (porta $porta) ---"
  curl -s "http://127.0.0.1:$porta/health"
  echo ""
}

case "$ALVO" in
  prod)
    atualizar "/root/microservice/image-microservice-prod" "image-microservice" 5002
    ;;
  dev)
    atualizar "/root/microservice/image-microservice-dev" "image-microservice-dev" 5001
    ;;
  both)
    atualizar "/root/microservice/image-microservice-prod" "image-microservice" 5002
    atualizar "/root/microservice/image-microservice-dev" "image-microservice-dev" 5001
    ;;
  *)
    echo "Uso: ./update-microservice.sh [dev|prod|both]"
    exit 1
    ;;
esac
