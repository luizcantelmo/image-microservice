#!/bin/bash
# Deploy Script para Hostinger VPS

set -e

echo "🚀 Iniciando deploy do Photo Monitor API..."

# Variáveis
APP_DIR="/home/photo-monitor-api"
APP_NAME="photo-monitor-api"
REPO_URL="\"

# Criar diretório
mkdir -p \
cd \

# Se não existe, clonar repositório
if [ ! -d ".git" ]; then
    echo "📥 Clonando repositório..."
    git clone \ .
else
    echo "📥 Atualizando repositório..."
    git pull origin main
fi

# Python virtual environment
echo "🐍 Instalando dependências Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Copiar .env
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "❗ Crie o arquivo .env com suas credenciais"
    exit 1
fi

# PM2
echo "⚙️  Configurando PM2..."
pm2 delete \ || true
pm2 start "gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app" --name "\" --env production
pm2 save

echo "✅ Deploy completo!"
echo "🌐 Aplicação rodando em: http://212.85.13.64:5001"
echo "📝 Ver logs: pm2 logs \"
