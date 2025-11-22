#!/usr/bin/env powershell
# Script de Deploy Automático - Hostinger VPS
# Microservice Photo Monitor

Write-Host @"
╔════════════════════════════════════════════════════════════════════════════╗
║                    🚀 DEPLOY HOSTINGER VPS - INÍCIO                       ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 INFORMAÇÕES DO SERVIDOR:
   IP: 212.85.13.64
   DNS: srv819060.hstgr.cloud
   Plano: VPS
   Serviço: Microservice Photo Monitor

"@ -ForegroundColor Cyan

# ============================================================================
# PASSO 1: PREPARAR CÓDIGO LOCALMENTE
# ============================================================================

Write-Host "`n🔧 PASSO 1: Preparando código local..." -ForegroundColor Yellow

$microservicePath = "d:\Repositorio\image-microservice"
Set-Location $microservicePath

# Verificar se git está inicializado
if (!(Test-Path ".git")) {
    Write-Host "  Inicializando Git..." -ForegroundColor Gray
    git init
    git config user.email "deploy@photo-monitor.com"
    git config user.name "Photo Monitor Deploy"
}

# Adicionar todos os arquivos
Write-Host "  Adicionando arquivos..." -ForegroundColor Gray
git add .

# Verificar se há mudanças
$status = git status --porcelain
if ($status) {
    Write-Host "  Commitando mudanças..." -ForegroundColor Gray
    git commit -m "Deploy para VPS Hostinger - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
} else {
    Write-Host "  Nenhuma mudança para commitar" -ForegroundColor Gray
}

# Garantir branch main
if (!(git rev-parse --verify main 2>$null)) {
    Write-Host "  Criando branch main..." -ForegroundColor Gray
    git branch -M main
}

Write-Host "✅ Código local pronto" -ForegroundColor Green

# ============================================================================
# PASSO 2: CRIAR ARQUIVO DE INSTRUÇÕES PARA SSH
# ============================================================================

Write-Host "`n📝 PASSO 2: Criando instruções para deploy via SSH..." -ForegroundColor Yellow

$sshInstructions = @"
# ============================================================================
# INSTRUÇÕES DE DEPLOYMENT - SSH HOSTINGER VPS
# ============================================================================

## INFORMAÇÕES
- IP: 212.85.13.64
- DNS: srv819060.hstgr.cloud
- Usuário: (use seu SSH user da Hostinger)
- Porta SSH: 22 (ou a que foi configurada)

## PASSO 1: Conectar ao VPS via SSH

ssh seu_usuario@212.85.13.64
(ou: ssh seu_usuario@srv819060.hstgr.cloud)

## PASSO 2: Criar diretório do app

mkdir -p /home/seu_usuario/photo-monitor-api
cd /home/seu_usuario/photo-monitor-api

## PASSO 3: Clonar repositório (escolha uma opção)

### OPÇÃO A: GitHub (recomendado)
git clone https://github.com/SEU_USUARIO/image-microservice.git .

### OPÇÃO B: Sem Git (cópia direta)
# Copie os arquivos via SFTP ou tar

## PASSO 4: Instalar Python e dependências

sudo apt update
sudo apt install -y python3 python3-pip python3-venv

## PASSO 5: Criar Virtual Environment

python3 -m venv venv
source venv/bin/activate

## PASSO 6: Instalar dependências Python

pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

## PASSO 7: Testar a aplicação localmente

python run.py

# Deve mostrar: Running on http://127.0.0.1:5001

## PASSO 8: Configurar PM2 para rodar em background

sudo npm install -g pm2
pm2 start "gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app" --name "photo-monitor-api"
pm2 startup
pm2 save

# Verificar status:
pm2 status

## PASSO 9: Configurar Nginx como Reverse Proxy

sudo apt install -y nginx

# Criar arquivo de configuração:
sudo nano /etc/nginx/sites-available/photo-monitor

# Colar conteúdo:
server {
    listen 80;
    server_name 212.85.13.64 srv819060.hstgr.cloud seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Ativar site:
sudo ln -s /etc/nginx/sites-available/photo-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

## PASSO 10: Configurar SSL com Let's Encrypt

sudo apt install -y certbot python3-certbot-nginx

sudo certbot --nginx -d seu-dominio.com

# Renovação automática:
sudo systemctl enable certbot.timer

## PASSO 11: Configurar Variáveis de Ambiente

# Editar arquivo .env
nano .env

# Adicionar:
DEBUG=False
ENVIRONMENT=production
FLASK_PORT=5001
FLASK_HOST=0.0.0.0
ALLOW_CORS=True
CORS_ORIGINS=*

GOOGLE_REFRESH_TOKEN=seu_token_aqui
GOOGLE_CLIENT_ID=seu_client_id_aqui
GOOGLE_CLIENT_SECRET=seu_secret_aqui
TINY_API_TOKEN=seu_token_aqui

SUPABASE_URL=https://qvoctlfnwdesbnjhgiyq.supabase.co
SUPABASE_KEY=seu_service_role_key_aqui

# Salvar: Ctrl+O, Enter, Ctrl+X

## PASSO 12: Reiniciar Aplicação

pm2 restart photo-monitor-api

# Ver logs:
pm2 logs photo-monitor-api

## PRONTO! 🎉

Sua aplicação está rodando em:
- http://212.85.13.64:5001
- http://srv819060.hstgr.cloud:5001
- https://seu-dominio.com (se configurou SSL)

## COMANDOS ÚTEIS

# Ver status
pm2 status

# Logs
pm2 logs photo-monitor-api

# Reiniciar
pm2 restart photo-monitor-api

# Parar
pm2 stop photo-monitor-api

# Deletar
pm2 delete photo-monitor-api

# Monitorar
pm2 monit

"@

$sshInstructions | Out-File -FilePath "deploy-ssh-instructions.txt" -Encoding UTF8
Write-Host "✅ Instruções SSH criadas em: deploy-ssh-instructions.txt" -ForegroundColor Green

# ============================================================================
# PASSO 3: CRIAR ARQUIVO .ENV PARA HOSTINGER
# ============================================================================

Write-Host "`n🔐 PASSO 3: Criando arquivo .env para Hostinger..." -ForegroundColor Yellow

$envFile = @"
# Microservice Configuration - Production (Hostinger VPS)
DEBUG=False
ENVIRONMENT=production
FLASK_PORT=5001
FLASK_HOST=0.0.0.0
ALLOW_CORS=True
CORS_ORIGINS=*

# Google Drive Integration
# PREENCHENDO COM SEUS VALORES:
GOOGLE_REFRESH_TOKEN=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Tiny ERP Integration
# PREENCHENDO COM SEU TOKEN:
TINY_API_TOKEN=

# Supabase Configuration
SUPABASE_URL=https://qvoctlfnwdesbnjhgiyq.supabase.co
SUPABASE_KEY=

# Logging
LOG_LEVEL=INFO

# Image Processing
OUTPUT_IMAGE_QUALITY=90
PADDING_X=30
PADDING_Y=30
LINE_HEIGHT_MULTIPLIER=1.2
PRODUCT_BLOCK_WIDTH_PERCENT=0.45

# Font Sizes
FONT_DESCRIPTION_SIZE=28
FONT_REF_SIZE_PROMO=22
FONT_PRICE_SIZE=30
FONT_ESGOTADO_SIZE=40

# Timeouts
REQUEST_TIMEOUT=30
TASK_TIMEOUT=300
MAX_RETRIES=3
MAX_PRODUCTS_PER_REQUEST=10

# Redis (deixar False para uso básico)
USE_REDIS=False
REDIS_HOST=localhost
REDIS_PORT=6379
"@

$envFile | Out-File -FilePath ".env.production" -Encoding UTF8
Write-Host "✅ Arquivo .env.production criado" -ForegroundColor Green
Write-Host "   ⚠️  IMPORTANTE: Preencha com seus valores antes de fazer upload!" -ForegroundColor Yellow

# ============================================================================
# PASSO 4: CRIAR SCRIPT DE DEPLOYMENT PARA HOSTINGER
# ============================================================================

Write-Host "`n📦 PASSO 4: Preparando script de deployment..." -ForegroundColor Yellow

$deployScript = @"
#!/bin/bash
# Deploy Script para Hostinger VPS

set -e

echo "🚀 Iniciando deploy do Photo Monitor API..."

# Variáveis
APP_DIR="/home/photo-monitor-api"
APP_NAME="photo-monitor-api"
REPO_URL="\$1"

# Criar diretório
mkdir -p \$APP_DIR
cd \$APP_DIR

# Se não existe, clonar repositório
if [ ! -d ".git" ]; then
    echo "📥 Clonando repositório..."
    git clone \$REPO_URL .
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
pm2 delete \$APP_NAME || true
pm2 start "gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app" --name "\$APP_NAME" --env production
pm2 save

echo "✅ Deploy completo!"
echo "🌐 Aplicação rodando em: http://212.85.13.64:5001"
echo "📝 Ver logs: pm2 logs \$APP_NAME"
"@

$deployScript | Out-File -FilePath "deploy.sh" -Encoding UTF8
Write-Host "✅ Script deploy.sh criado" -ForegroundColor Green

# ============================================================================
# PASSO 5: CRIAR RESUMO FINAL
# ============================================================================

Write-Host @"
╔════════════════════════════════════════════════════════════════════════════╗
║                     ✅ ARQUIVOS PRONTOS PARA DEPLOY                       ║
╚════════════════════════════════════════════════════════════════════════════╝

ARQUIVOS CRIADOS:
  ✅ deploy-ssh-instructions.txt - Guia passo a passo SSH
  ✅ deploy.sh - Script automático de deployment
  ✅ .env.production - Template de variáveis de ambiente
  ✅ Procfile - Configuração para Hostinger
  ✅ requirements.txt - Dependências Python

SERVIDOR VPS:
  🖥️  IP: 212.85.13.64
  🌐 DNS: srv819060.hstgr.cloud
  ✅ Plano: VPS (pronto)

PRÓXIMOS PASSOS:

1️⃣  PREENCHA OS DADOS:
    - Abra .env.production
    - Adicione suas credenciais:
      * GOOGLE_REFRESH_TOKEN
      * GOOGLE_CLIENT_ID
      * GOOGLE_CLIENT_SECRET
      * TINY_API_TOKEN
      * SUPABASE_KEY (service role)

2️⃣  FAÇA UPLOAD PARA HOSTINGER:
    Via SFTP (recomendado):
    - Host: 212.85.13.64
    - User: seu_ssh_user
    - Pasta: /home/seu_usuario/photo-monitor-api

3️⃣  CONECTE VIA SSH E EXECUTE:
    ssh seu_usuario@212.85.13.64
    bash deploy.sh "https://seu-repo-github.git"

4️⃣  CONFIGURE NGINX (ver deploy-ssh-instructions.txt)

5️⃣  CONFIGURE EDGE FUNCTION NA SUPABASE:
    supabase secrets set MICROSERVICE_URL=https://212.85.13.64

6️⃣  DEPLOY FRONTEND NO VERCEL (opcional)

DOCUMENTAÇÃO:
  📄 Abra: deploy-ssh-instructions.txt
  📄 Abra: DEPLOY-HOSTINGER-PASSO-A-PASSO.md

"@ -ForegroundColor Green

# ============================================================================
# PASSO 6: GIT PUSH
# ============================================================================

Write-Host "`n⏭️  PASSO 5: Configurando Git para push..." -ForegroundColor Yellow

Write-Host @"

Para fazer push do código, você tem 2 opções:

OPÇÃO A: GitHub (Recomendado)
1. Crie um repositório em https://github.com/new
2. Execute:
   git remote add origin https://github.com/SEU_USUARIO/image-microservice.git
   git push -u origin main

OPÇÃO B: Gitlab / Gitea
1. Configure seu repositório remoto
2. Execute: git push -u origin main

OPÇÃO C: Hostinger Git (se disponível)
1. Hostinger fornecerá um link Git
2. Execute: git remote add hostinger seu_link
3. Execute: git push hostinger main

"@ -ForegroundColor Cyan

Write-Host "`n✨ TUDO PRONTO! 🎉`n" -ForegroundColor Green
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Configure .env.production com suas credenciais" -ForegroundColor Gray
Write-Host "2. Faça git push para seu repositório" -ForegroundColor Gray
Write-Host "3. Upload para Hostinger via SFTP" -ForegroundColor Gray
Write-Host "4. Execute bash deploy.sh via SSH" -ForegroundColor Gray
Write-Host "5. Configure Nginx" -ForegroundColor Gray

Write-Host "`nArquivos criados em: $microservicePath`n" -ForegroundColor Cyan
