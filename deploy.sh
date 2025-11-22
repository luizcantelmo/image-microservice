#!/bin/bash
# Deploy Script - Hostinger VPS
# Photo Monitor Microservice

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🚀 DEPLOY PHOTO MONITOR API - HOSTINGER VPS           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="${1:-}"
APP_DIR="/home/photo-monitor-api"
APP_NAME="photo-monitor-api"
PYTHON_VERSION="python3"

# Check if repo URL is provided
if [ -z "$REPO_URL" ]; then
    echo -e "${YELLOW}❌ Erro: Forneça a URL do repositório!${NC}"
    echo "Uso: bash deploy.sh https://github.com/SEU_USUARIO/image-microservice.git"
    exit 1
fi

echo -e "${BLUE}📋 Configuração:${NC}"
echo "   Diretório: $APP_DIR"
echo "   App Name: $APP_NAME"
echo "   Repositório: $REPO_URL"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
   echo -e "${YELLOW}⚠️  Execute com sudo para instalação completa${NC}"
   echo "   sudo bash deploy.sh $REPO_URL"
fi

# ============================================================================
# PASSO 1: Verificar/Instalar dependências
# ============================================================================

echo -e "${BLUE}🔧 PASSO 1: Verificando dependências...${NC}"

# Update package manager
apt update > /dev/null 2>&1 || true

# Install Python if not present
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo -e "${YELLOW}📥 Instalando Python...${NC}"
    apt install -y python3 python3-pip python3-venv > /dev/null
fi

# Install Git if not present
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}📥 Instalando Git...${NC}"
    apt install -y git > /dev/null
fi

# Install Node.js if not present (para PM2)
if ! command -v npm &> /dev/null; then
    echo -e "${YELLOW}📥 Instalando Node.js...${NC}"
    apt install -y nodejs npm > /dev/null
fi

# Install PM2 if not present
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}📥 Instalando PM2...${NC}"
    npm install -g pm2 > /dev/null
fi

# Install Nginx if not present
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}📥 Instalando Nginx...${NC}"
    apt install -y nginx > /dev/null
fi

echo -e "${GREEN}✅ Dependências OK${NC}"

# ============================================================================
# PASSO 2: Criar/Atualizar código
# ============================================================================

echo -e "${BLUE}📥 PASSO 2: Código do repositório...${NC}"

mkdir -p $APP_DIR
cd $APP_DIR

if [ -d ".git" ]; then
    echo "   Atualizando repositório..."
    git pull origin main
else
    echo "   Clonando repositório..."
    git clone "$REPO_URL" .
fi

echo -e "${GREEN}✅ Código pronto${NC}"

# ============================================================================
# PASSO 3: Configurar Python virtual environment
# ============================================================================

echo -e "${BLUE}🐍 PASSO 3: Configurando Python...${NC}"

if [ ! -d "venv" ]; then
    echo "   Criando virtual environment..."
    $PYTHON_VERSION -m venv venv
fi

source venv/bin/activate

echo "   Instalando dependências Python..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
pip install gunicorn > /dev/null

echo -e "${GREEN}✅ Python OK${NC}"

# ============================================================================
# PASSO 4: Verificar arquivo .env
# ============================================================================

echo -e "${BLUE}🔐 PASSO 4: Verificando .env...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo "   ⚠️  Arquivo .env criado a partir de .env.production"
        echo "   ⚠️  IMPORTANTE: Preencha os valores vazios!"
    else
        echo -e "${RED}❌ Erro: arquivo .env não encontrado!${NC}"
        echo "   Crie o arquivo .env com suas credenciais"
        exit 1
    fi
else
    echo "   Arquivo .env encontrado"
fi

echo -e "${GREEN}✅ .env OK${NC}"

# ============================================================================
# PASSO 5: Configurar PM2
# ============================================================================

echo -e "${BLUE}⚙️  PASSO 5: Configurando PM2...${NC}"

# Stop existing app if running
pm2 delete $APP_NAME 2>/dev/null || true

source venv/bin/activate

echo "   Iniciando aplicação com PM2..."
pm2 start "gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app" \
  --name "$APP_NAME" \
  --cwd "$APP_DIR" \
  --env production

echo "   Salvando configuração PM2..."
pm2 save
pm2 startup | tail -1 | bash

echo -e "${GREEN}✅ PM2 OK${NC}"

# ============================================================================
# PASSO 6: Configurar Nginx
# ============================================================================

echo -e "${BLUE}🌐 PASSO 6: Configurando Nginx...${NC}"

NGINX_CONFIG="/etc/nginx/sites-available/$APP_NAME"

if [ ! -f "$NGINX_CONFIG" ]; then
    echo "   Criando configuração Nginx..."
    
    cat > "$NGINX_CONFIG" << 'NGINX_CONF'
server {
    listen 80;
    server_name 212.85.13.64 srv819060.hstgr.cloud;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Para upload de arquivos grandes
        client_max_body_size 100M;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
NGINX_CONF
    
    # Enable site
    ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/$APP_NAME
    
    # Test config
    nginx -t > /dev/null 2>&1
    
    # Restart Nginx
    systemctl restart nginx
fi

echo -e "${GREEN}✅ Nginx OK${NC}"

# ============================================================================
# PASSO 7: Teste final
# ============================================================================

echo -e "${BLUE}🧪 PASSO 7: Testando aplicação...${NC}"

sleep 2

# Test if app is running
if curl -s http://127.0.0.1:5001/health > /dev/null; then
    echo -e "${GREEN}✅ Aplicação respondendo${NC}"
else
    echo -e "${YELLOW}⚠️  Aplicação pode estar iniciando...${NC}"
fi

# ============================================================================
# RESULTADO FINAL
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DEPLOY COMPLETO! 🎉                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo -e "${GREEN}🌐 URLs de Acesso:${NC}"
echo "   http://212.85.13.64:5001"
echo "   http://srv819060.hstgr.cloud:5001"
echo ""

echo -e "${GREEN}📊 Status:${NC}"
pm2 status

echo ""
echo -e "${BLUE}📝 Comandos Úteis:${NC}"
echo "   Ver logs:      pm2 logs $APP_NAME"
echo "   Reiniciar:     pm2 restart $APP_NAME"
echo "   Parar:         pm2 stop $APP_NAME"
echo "   Monitorar:     pm2 monit"
echo ""

echo -e "${YELLOW}⚠️  Próximos Passos:${NC}"
echo "   1. Configure SSL com Let's Encrypt (opcional)"
echo "   2. Configure domínio no Nginx"
echo "   3. Teste a API: curl http://212.85.13.64:5001/health"
echo "   4. Configure secrets no Supabase"
echo "   5. Deploy Edge Function no Supabase"
echo ""
